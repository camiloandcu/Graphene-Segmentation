"""Public dataset consumer; train/validation only, shared geometry and paired flips."""
from __future__ import annotations
import numpy as np
import torch
from PIL import Image
from graphene_dataset_contract import check, iter_samples
from graphene_model_contract.geometry import prepare_letterbox_rgb
from .config import PREPROCESSING


def transform(rgb, mask, size):
    prepared = prepare_letterbox_rgb(rgb, (size, size), PREPROCESSING)
    g = prepared.geometry
    h, w = g.resized_hw
    resized = np.asarray(Image.fromarray(mask).resize((w, h), Image.Resampling.NEAREST))
    target = np.full((size, size), 255, dtype=np.int64)
    target[g.top:g.top+h, g.left:g.left+w] = resized
    return torch.from_numpy(prepared.tensor[0]), torch.from_numpy(target), g


def preflight(dataset, config):
    manifest = check(dataset)
    output = {"dataset_fingerprint": manifest.dataset_fingerprint,
              "split_fingerprint": manifest.split_fingerprint,
              "supervision_fingerprint": getattr(manifest, 'supervision_fingerprint', manifest.dataset_fingerprint),
              "schema_version": manifest.schema_version,
              "evaluation": manifest.review.evaluation.model_dump(), "roles": {}}
    for role in ('train', 'validation'):
        support = np.zeros(3, dtype=np.int64)
        transformed = np.zeros(3, dtype=np.int64)
        unknown, total, samples, losses = 0, 0, 0, []
        for s, rgb, mask in iter_samples(dataset, role):
            _, target, _ = transform(rgb, mask, config.input_size)
            counts = np.array([(mask == c).sum() for c in range(3)])
            after = np.array([(target.numpy() == c).sum() for c in range(3)])
            if not after.sum():
                raise ValueError(f'{s.sample_id}: resizing erased all supervision; choose a larger input')
            erased = [int(c) for c in range(3) if counts[c] > 0 and after[c] == 0]
            if erased: losses.append({'sample_id': s.sample_id, 'erased_classes': erased})
            support += counts; transformed += after
            unknown += int((mask == 255).sum()); total += mask.size; samples += 1
        if not samples or (support == 0).any():
            missing = [c for c in range(3) if support[c] == 0]
            raise ValueError(f'{role}: reviewed supervised classes missing {missing}; background requires source-bound anchors or verified blank images')
        if (transformed == 0).any():
            raise ValueError(f'{role}: resizing erased aggregate class support')
        output['roles'][role] = {'samples': samples, 'support': support.tolist(),
                                'transformed_support': transformed.tolist(), 'unknown_fraction': unknown / total,
                                'resize_support_losses': losses}
    return output


class RoleDataset(torch.utils.data.Dataset):
    def __init__(self, directory, role, config):
        if role not in ('train', 'validation'):
            raise ValueError('Baseline consumer uses only train and validation')
        self.items = list(iter_samples(directory, role))
        self.role, self.config = role, config

    def __len__(self):
        return len(self.items)

    def __getitem__(self, index):
        _, rgb, mask = self.items[index]
        image, target, _ = transform(rgb, mask, self.config.input_size)
        if self.role == 'train':
            if torch.rand(()).item() < self.config.horizontal_flip:
                image, target = image.flip(-1), target.flip(-1)
            if torch.rand(()).item() < self.config.vertical_flip:
                image, target = image.flip(-2), target.flip(-2)
        return image, target
