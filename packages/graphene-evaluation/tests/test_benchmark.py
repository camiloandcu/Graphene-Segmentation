"""Inference timings include file decoding and the bound decision rule."""
import importlib
from itertools import count
from types import SimpleNamespace

import numpy as np
import pytest
import torch
from graphene_dataset_contract import check

bench = importlib.import_module('graphene_evaluation.benchmark')


def configure(monkeypatch, dataset):
    manifest = check(dataset)
    config = SimpleNamespace(seed=42, input_size=64, model_copy=lambda **kwargs: None)
    monkeypatch.setattr(bench, 'checkpoint', lambda *args: (
        torch.nn.Identity(), config, manifest, {'checkpoint_sha256': 'a'*64}))
    monkeypatch.setattr(bench, 'environment', lambda config: {})
    monkeypatch.setattr(bench, 'logits', lambda model, rgb, **kwargs:
                        np.zeros((3, *rgb.shape[:2]), dtype=np.float32))
    return manifest


def test_decode_decision_and_initialization_are_measured(monkeypatch, dataset):
    manifest = configure(monkeypatch, dataset)
    ticks = count()
    monkeypatch.setattr(bench.time, 'perf_counter', lambda: next(ticks))
    decoded, predictions = [], []
    original_decode, original_decision = bench.decode, bench.decision

    def decode(data):
        decoded.append(data)
        return original_decode(data)

    def decide(value, threshold):
        result = original_decision(value, threshold)
        predictions.append(result)
        assert threshold == .2 and np.all(result == 1)
        return result

    monkeypatch.setattr(bench, 'decode', decode)
    monkeypatch.setattr(bench, 'decision', decide)
    result = bench.benchmark(dataset, None, None, warmup=1, repeats=2, threshold=.2)
    assert result['initialization_seconds'] == 1
    assert result['binding']['settings']['threshold'] == .2
    validation = [s for s in manifest.samples if s.role == 'validation']
    assert len(decoded) == len(predictions) == len(validation)*3
    assert {row['sample_id'] for row in result['samples']} == {s.sample_id for s in validation}
    for row in result['samples']:
        assert row['milliseconds'] == [3000, 3000]
        assert row['decode_and_integrity_ms'] == [1000, 1000]
        assert row['inference_and_restoration_ms'] == [1000, 1000]
        assert row['decision_ms'] == [1000, 1000]


def test_repeated_read_rejects_changed_image(monkeypatch, dataset):
    configure(monkeypatch, dataset)
    original = bench.read_bytes
    calls = 0

    def changed(path):
        nonlocal calls
        calls += 1
        data = original(path)
        return data if calls == 1 else data+b'changed'

    monkeypatch.setattr(bench, 'read_bytes', changed)
    with pytest.raises(ValueError, match='Artifact changed after validation'):
        bench.benchmark(dataset, None, None, warmup=1, repeats=2)
