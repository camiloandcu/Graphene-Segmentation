"""Common original-coordinate semantic prediction and decision contracts."""
from types import SimpleNamespace
import numpy as np
import torch
import torch.nn.functional as F
from graphene_training.config import PREPROCESSING
from graphene_model_contract.contract import Tiles
from graphene_model_contract.geometry import prepare_letterbox_rgb, restore_letterbox, prepare_tiles, TileAccumulator


@torch.no_grad()
def logits(model, rgb, *, device='cpu', size=512, geometry='letterbox', stride=384):
    model.eval()
    def forward(tensor):
        result = model(torch.from_numpy(tensor).to(device))
        if result.shape[-2:] != (size, size):
            result = F.interpolate(result.float(), (size, size), mode='bilinear', align_corners=False)
        value = result.float().cpu().numpy()
        if value.shape != (1, 3, size, size) or not np.isfinite(value).all():
            raise ValueError('Candidate did not return finite three-channel logits')
        return value
    if geometry == 'letterbox':
        prepared = prepare_letterbox_rgb(rgb, (size, size), PREPROCESSING)
        return restore_letterbox(forward(prepared.tensor), prepared.geometry)
    if geometry != 'tiles' or not 0 < stride <= size:
        raise ValueError('Unsupported geometry or tile stride')
    policy = SimpleNamespace(geometry=Tiles(mode='tiles', version=1, stride=(stride, stride), merge='mean_logits'),
                             input=SimpleNamespace(shape=(1, 3, size, size)), preprocessing=PREPROCESSING)
    accumulator = TileAccumulator(rgb.shape[:2], policy)
    for prepared in prepare_tiles(rgb, policy):
        accumulator.add(forward(prepared.tensor), prepared.geometry)
    return accumulator.finish()


def decision(value, threshold=None):
    if value.ndim != 3 or value.shape[0] != 3 or not np.isfinite(value).all():
        raise ValueError('Expected finite original-coordinate [3,H,W] logits')
    if threshold is None:
        return value.argmax(0).astype(np.uint8)
    if not 0 < threshold < 1:
        raise ValueError('Few-layer threshold must be strictly between zero and one')
    stable = value.astype(np.float64)-value.max(0)
    probability = np.exp(stable)
    probability /= probability.sum(0)
    result = np.where(probability[0] >= probability[2], 0, 2).astype(np.uint8)
    result[probability[1] >= threshold] = 1
    return result
