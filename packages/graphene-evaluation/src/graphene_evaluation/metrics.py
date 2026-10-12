"""Supervised pixel counts and censored connected-component detection proxies."""
from __future__ import annotations

import numpy as np
from scipy.ndimage import label
from scipy.optimize import linear_sum_assignment
from graphene_training.objective import metrics as pixel_metrics


def confusion(target, prediction):
    target, prediction = np.asarray(target), np.asarray(prediction)
    if target.shape != prediction.shape or target.ndim != 2:
        raise ValueError('Target and prediction must have equal original H,W')
    if not np.isin(target, [0, 1, 2, 255]).all() or not np.isin(prediction, [0, 1, 2]).all():
        raise ValueError('Invalid canonical class IDs')
    known = target != 255
    return np.bincount(target[known].astype(np.int64)*3 + prediction[known], minlength=9).reshape(3, 3)


def pixels(matrix):
    result = pixel_metrics(matrix)
    supported = [v['iou'] for v in result['classes'][1:] if v['support'] > 0]
    result['foreground_macro_iou'] = float(np.mean(supported)) if supported else None
    for value in result['classes']:
        value['unavailable_reasons'] = {
            name: 'Zero denominator on supervised reference/prediction support'
            for name in ('precision', 'recall', 'dice', 'iou') if value[name] is None
        }
    return result


def components(target, prediction, *, threshold=.5):
    """Full-image prediction components; IoU on fixed known support only.

    Connected eligible overlap graphs are solved independently, avoiding a dense
    all-object matrix. Canonical row-major component IDs fix assignment tie order.
    """
    confusion(target, prediction)  # Validate shapes and values even on empty support.
    if threshold != .5:
        raise ValueError('The reviewed matching proxy uses IoU >= 0.5')
    known = target != 255
    ref, nr = label(target == 1, structure=np.ones((3, 3)))
    pred, npred = label(prediction == 1, structure=np.ones((3, 3)))
    ref_size = np.bincount(ref.ravel(), minlength=nr+1)
    pred_known = np.bincount(pred[known], minlength=npred+1)
    pred_unknown = np.bincount(pred[~known], minlength=npred+1)
    pred_size = np.bincount(pred.ravel(), minlength=npred+1)
    both = (ref > 0) & (pred > 0)
    # Only sparse observed intersections are materialized.
    keys, counts = np.unique(ref[both].astype(np.int64)*(npred+1)+pred[both], return_counts=True)
    edges, overlap, coverage = {}, set(), np.zeros(nr+1, dtype=np.int64)
    for key, count in zip(keys, counts):
        r, p = divmod(int(key), npred+1)
        coverage[r] += int(count)
        overlap.add(p)
        iou = int(count) / (int(ref_size[r])+int(pred_known[p])-int(count))
        if iou >= threshold:
            edges[r, p] = iou
    adjacency = {}
    for r, p in sorted(edges):
        adjacency.setdefault(('r', r), set()).add(('p', p))
        adjacency.setdefault(('p', p), set()).add(('r', r))
    matched = []
    remaining = set(adjacency)
    while remaining:
        pending, vertices = [min(remaining)], set()
        while pending:
            node = pending.pop()
            if node in vertices:
                continue
            vertices.add(node)
            pending.extend(sorted(adjacency[node]-vertices))
        remaining -= vertices
        rs = sorted(i for t, i in vertices if t == 'r')
        ps = sorted(i for t, i in vertices if t == 'p')
        if len(rs)*len(ps) > 1_000_000:
            raise ValueError('Matching overlap graph exceeds bounded assignment memory')
        # Any extra eligible match dominates all possible IoU improvements.
        priority = min(len(rs), len(ps))+1
        costs = np.zeros((len(rs), len(ps)+len(rs)), dtype=np.float64)
        for i, r in enumerate(rs):
            for j, p in enumerate(ps):
                if (r, p) in edges:
                    costs[i, j] = -priority-edges[r, p]
        rows, cols = linear_sum_assignment(costs)
        for i, j in zip(rows, cols):
            if j < len(ps) and (rs[i], ps[j]) in edges:
                matched.append({'reference_id': rs[i], 'prediction_id': ps[j], 'supervised_iou': edges[rs[i], ps[j]]})
    matched.sort(key=lambda v: (v['reference_id'], v['prediction_id']))
    mr = {v['reference_id'] for v in matched}
    mp = {v['prediction_id'] for v in matched}
    unmatched = set(range(1, npred+1))-mp
    known_unmatched = sorted(p for p in unmatched if pred_unknown[p] == 0)
    indeterminate = sorted(p for p in unmatched if pred_unknown[p] > 0)
    reference = [{'id': r, 'area': int(ref_size[r]), 'covered_fraction': float(coverage[r]/ref_size[r]),
                  'matched': r in mr} for r in range(1, nr+1)]
    predictions = [{'id': p, 'area': int(pred_size[p]), 'unknown_pixels': int(pred_unknown[p]),
                    'unknown_fraction': float(pred_unknown[p]/pred_size[p]), 'matched': p in mp,
                    'status': 'matched' if p in mp else ('indeterminate' if p in indeterminate else 'known-support-unmatched')}
                   for p in range(1, npred+1)]
    return {'reference_components': nr, 'prediction_components': npred, 'matches': matched,
            'missed_reference_ids': sorted(set(range(1, nr+1))-mr),
            'annotated_component_recall_proxy': len(mr)/nr if nr else None,
            'recall_unavailable_reason': None if nr else 'No annotated few-layer component',
            'known_support_unmatched_ids': known_unmatched,
            'known_support_no_overlap_ids': [p for p in known_unmatched if p not in overlap],
            'known_support_localization_or_fragment_ids': [p for p in known_unmatched if p in overlap],
            'indeterminate_unmatched_ids': indeterminate,
            'unknown_intersecting_ids': [p for p in range(1, npred+1) if pred_unknown[p] > 0],
            'references': reference, 'predictions': predictions,
            'definition': '8-connected original-coordinate components; maximum-cardinality then maximum-supervised-IoU one-to-one matching at IoU>=0.5; canonical row-major IDs for assignment ties',
            'limitations': ['Semantic components are not physical flake instances',
                           'Unknown bridges, touching labels and conflict ignores can alter components',
                           'Unknown coverage cannot establish exhaustive recall or full false burden']}


def unavailable():
    return {name: {'value': None, 'unavailable_reason': reason} for name, reason in {
        'complete_flake_recall': 'Non-exhaustive annotations and unverified physical instance identities',
        'full_false_detections_per_image': 'Predictions in unknown coverage cannot be classified as false',
        'coverage_ranking_agreement': 'No independent exhaustive whole-image coverage reference',
    }.items()}
