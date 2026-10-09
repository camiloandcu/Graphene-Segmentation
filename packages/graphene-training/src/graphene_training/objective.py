"""Masked CE + foreground Dice; original-coordinate development metrics."""
import numpy as np
import torch
import torch.nn.functional as F
from graphene_model_contract.geometry import restore_letterbox
from .data import transform


def loss(logits, target):
    valid = target != 255
    if not valid.any():
        raise ValueError('Entire batch is ignored')
    ce = F.cross_entropy(logits.float(), target, ignore_index=255, reduction='sum') / valid.sum()
    probability = logits.float().softmax(1)
    terms = []
    for c in (1, 2):
        truth = (target == c) & valid
        if truth.any():
            prediction = probability[:, c] * valid
            terms.append(1 - (2 * (prediction * truth).sum() + 1e-7) /
                         (prediction.sum() + truth.sum() + 1e-7))
    dice = torch.stack(terms).mean() if terms else logits.sum() * 0
    return ce + dice


def metrics(matrix):
    matrix = np.asarray(matrix, dtype=np.int64)
    values = []
    def ratio(a, b): return float(a / b) if b else None
    for c in range(3):
        tp, target, predicted = int(matrix[c, c]), int(matrix[c].sum()), int(matrix[:, c].sum())
        values.append({'class_id': c, 'support': target, 'predicted_support': predicted,
                       'dice': ratio(2*tp, target+predicted), 'iou': ratio(tp, target+predicted-tp),
                       'precision': ratio(tp, predicted), 'recall': ratio(tp, target)})
    supported = [v['dice'] for v in values[1:] if v['support'] > 0]
    return {'confusion_matrix': matrix.tolist(), 'classes': values,
            'foreground_macro_dice': float(np.mean(supported)) if supported else None,
            'scope': 'original-coordinate supervised pixels only; unknown pixels excluded'}


@torch.no_grad()
def evaluate(model, data, config):
    model.eval()
    matrix = np.zeros((3, 3), dtype=np.int64)
    for _, rgb, mask in data.items:
        image, _, geometry = transform(rgb, mask, config.input_size)
        logits = model(image[None].to(config.device)).float().cpu().numpy()
        restored = restore_letterbox(logits, geometry)
        predicted = restored.argmax(0)  # numpy chooses the lowest class ID on exact ties.
        valid = mask != 255
        matrix += np.bincount(mask[valid].astype(np.int64)*3 + predicted[valid], minlength=9).reshape(3, 3)
    return metrics(matrix)
