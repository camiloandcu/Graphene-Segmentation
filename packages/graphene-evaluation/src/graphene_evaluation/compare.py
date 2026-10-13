"""Common-support development comparisons; no scalar winner or test ranking."""
from pathlib import Path
import numpy as np
from graphene_dataset_contract.common import identity, read_json
from .metrics import pixels


def compare(paths, *, setting='argmax', bootstrap_repeats=1000, bootstrap_seed=20261011):
    reports = [read_json(Path(path)) for path in paths]
    if len(reports) < 2:
        raise ValueError('Compare at least two actual development reports')
    first = reports[0]
    keys = ('dataset_fingerprint', 'split_fingerprint', 'supervision_fingerprint')
    samples = first['settings'][setting]['samples']
    support = [(s['sample_id'], s['image_sha256'], s['mask_sha256'], s['supervised_pixels']) for s in samples]
    for report in reports:
        if report.get('role') != 'validation':
            raise ValueError('Model comparison uses validation only; no test ranking')
        if report.get('report_fingerprint') != identity({k:v for k,v in report.items() if k != 'report_fingerprint'}):
            raise ValueError('Report fingerprint mismatch')
        if any(report['binding'][k] != first['binding'][k] for k in keys):
            raise ValueError('Comparison dataset/split/supervision mismatch')
        actual = [(s['sample_id'], s['image_sha256'], s['mask_sha256'], s['supervised_pixels']) for s in report['settings'][setting]['samples']]
        if actual != support or report['groups'] != first['groups']:
            raise ValueError('Comparison image support/group identities differ')
    group_names = sorted({v['group'] for v in first['groups'].values() if v['status'] == 'known'})
    known_groups = all(v['status'] == 'known' for v in first['groups'].values())
    # Group resamples shared by every model: paired uncertainty, not independent intervals.
    rng = np.random.default_rng(bootstrap_seed)
    draws = rng.integers(0, len(group_names), (bootstrap_repeats, len(group_names))) if known_groups and len(group_names) > 1 else None
    candidates = []
    for report in reports:
        measured = report['settings'][setting]
        item = {'binding': report['binding'], 'settings': measured['selection_settings'],
                'pixels': measured['pixels'], 'components': measured['component_totals'],
                'resources': report['resources'], 'per_image': [
                    {'sample_id': s['sample_id'], 'foreground_macro_dice': s['pixels']['foreground_macro_dice'],
                     'component_recall': s['components']['annotated_component_recall_proxy']}
                    for s in measured['samples']]}
        matrices = {}
        for group in group_names:
            records = [s for s in measured['samples'] if report['groups'][s['sample_id']]['group'] == group]
            matrices[group] = np.sum([s['pixels']['confusion_matrix'] for s in records], axis=0)
        item['per_group'] = {g: pixels(m) for g, m in matrices.items()}
        if draws is not None:
            values = [pixels(np.sum([matrices[group_names[i]] for i in draw], axis=0))['foreground_macro_dice'] for draw in draws]
            item['group_bootstrap_foreground_dice_95_percentile_interval'] = np.percentile(values, [2.5, 97.5]).tolist()
            item['paired_bootstrap_draw_scores'] = values
        else:
            item['group_bootstrap_foreground_dice_95_percentile_interval'] = None
        candidates.append(item)
    seed_summaries = {}
    for name in sorted({c['binding']['architecture'] for c in candidates}):
        subset = [c for c in candidates if c['binding']['architecture'] == name]
        # Only identical configurations other than seed/persistence are a seed series.
        configs = [{k:v for k,v in c['binding']['config'].items() if k not in ('seed', 'persistence_directory')} for c in subset]
        if all(c == configs[0] for c in configs) and len({c['binding']['seed'] for c in subset}) == len(subset):
            values = [c['pixels']['foreground_macro_dice'] for c in subset]
            seed_summaries[name] = {'seeds': [c['binding']['seed'] for c in subset],
                                    'foreground_dice_mean': float(np.mean(values)),
                                    'foreground_dice_range': [min(values), max(values)],
                                    'sample_std': float(np.std(values, ddof=1)) if len(values)>1 else None}
    return {'schema_version': 1, 'role': 'validation', 'candidates': candidates, 'seed_summaries': seed_summaries,
            'bootstrap': {'seed': bootstrap_seed, 'repeats': bootstrap_repeats,
                'unit': 'reviewed group', 'available': draws is not None,
                'limitation': 'Few reviewed groups; exploratory sensitivity, not a generalization guarantee'},
            'decision': 'Stakeholder reviews few-layer/component recall, known-support errors and resources; no automatic scalar winner'}
