"""Baseline-equivalence and initialization identity for the WI-07 U-Net runner."""
import json
import pytest
import torch
from graphene_training.config import TrainingConfig
from graphene_training.engine import run as baseline_run, seed_all
from graphene_training.storage import load_state, inspect
from graphene_evaluation.config import ExperimentConfig
from graphene_evaluation.experiments import run, resume
from graphene_evaluation import candidates


def tiny():
    # Dropout makes an extra RNG draw or incorrect replay observable.
    return torch.nn.Sequential(torch.nn.Conv2d(3, 4, 1), torch.nn.Dropout2d(.2), torch.nn.Conv2d(4, 3, 1))


def equal_state(a, b):
    if isinstance(a, torch.Tensor):
        assert torch.equal(a, b)
    elif isinstance(a, dict):
        assert a.keys() == b.keys()
        for key in a: equal_state(a[key], b[key])
    elif isinstance(a, (list, tuple)):
        assert len(a) == len(b)
        for x, y in zip(a, b): equal_state(x, y)
    else:
        assert a == b


def test_unet_finalist_matches_baseline_and_retained_resume(dataset, tmp_path):
    full, trial, retained = (tmp_path/name for name in ('baseline', 'trial', 'retained'))
    settings = dict(input_size=64, epochs=2, horizontal_flip=.5, vertical_flip=.5)
    baseline_run(dataset, TrainingConfig(**settings), full, _fixture_factory=tiny)
    config = ExperimentConfig(architecture='unet-resnet18', weights='imagenet-resnet18-v1',
                              **settings, persistence_directory=str(retained))
    run(dataset, config, trial, _fixture_factory=tiny, _stop_after=1)
    resume(dataset, trial, 'epoch-000001', _fixture_factory=tiny)
    assert inspect(retained)['completed_epochs'] == 2
    equal_state(load_state(full, 'epoch-000002'), load_state(retained, 'epoch-000002'))
    old = json.loads((full/'epochs/epoch-000002/history.json').read_text())
    new = json.loads((retained/'epochs/epoch-000002/history.json').read_text())
    for a, b in zip(old, new):
        for key in ('epoch', 'loss', 'validation', 'learning_rate'): assert a[key] == b[key]


def test_unet_initializes_once_and_checks_reviewed_weight_digest(tmp_path, monkeypatch):
    calls = []
    def initialize(cache):
        calls.append(cache)
        return tiny(), {'sha256': 'a'*64, 'initialization': 'synthetic-test-only'}
    monkeypatch.setattr(candidates, 'initialize_resnet', initialize)
    config = ExperimentConfig(architecture='unet-resnet18', weights='imagenet-resnet18-v1',
                              license_approved=True, weights_sha256='a'*64)
    seed_all(42); expected, _ = initialize(tmp_path); expected_rng = torch.get_rng_state()
    calls.clear(); seed_all(42); actual, _ = candidates.pretrained(config, tmp_path)
    assert len(calls) == 1
    equal_state(expected.state_dict(), actual.state_dict())
    assert torch.equal(expected_rng, torch.get_rng_state())
    with pytest.raises(ValueError, match='weight identity mismatch'):
        candidates.pretrained(config.model_copy(update={'weights_sha256':'b'*64}), tmp_path)
