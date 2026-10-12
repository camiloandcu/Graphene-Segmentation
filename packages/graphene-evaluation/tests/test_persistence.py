"""Persistence failures and replacement-session verification, using fixtures."""
import pytest
import torch

from graphene_evaluation.config import ExperimentConfig
from graphene_evaluation.experiments import run, resume
from graphene_evaluation import persistence
from graphene_training.storage import inspect, load_state


def tiny():
    return torch.nn.Conv2d(3, 3, 1)


def test_persisted_resume_matches_uninterrupted(dataset, tmp_path):
    full, partial, retained = (tmp_path/n for n in ('full', 'partial', 'retained'))
    common = dict(architecture='deeplabv3plus-resnet18', weights='imagenet-resnet18-v1', input_size=64, epochs=2)
    run(dataset, ExperimentConfig(**common), full, _fixture_factory=tiny)
    run(dataset, ExperimentConfig(**common, persistence_directory=str(retained)), partial,
        _fixture_factory=tiny, _stop_after=1)
    assert inspect(retained)['last'] == 'epoch-000001'
    resume(dataset, partial, 'epoch-000001', _fixture_factory=tiny)
    assert inspect(retained)['last'] == 'epoch-000002'
    a, b = load_state(full, 'epoch-000002'), load_state(retained, 'epoch-000002')
    assert all(torch.equal(a['model'][key], b['model'][key]) for key in a['model'])
    assert torch.equal(a['rng']['torch'], b['rng']['torch'])
    assert torch.equal(a['generator'], b['generator'])


def test_interrupted_copy_has_no_completion_authority(dataset, tmp_path, monkeypatch):
    source, target = tmp_path/'source', tmp_path/'target'
    cfg = ExperimentConfig(architecture='deeplabv3plus-resnet18', weights='imagenet-resnet18-v1', input_size=64, epochs=1)
    run(dataset, cfg, source, _fixture_factory=tiny)
    original = persistence.copy_checked

    def interrupt(src, dst, expected):
        if dst.name == 'metadata.json':
            raise OSError('Synthetic copy interruption')
        original(src, dst, expected)

    monkeypatch.setattr(persistence, 'copy_checked', interrupt)
    with pytest.raises(OSError, match='Synthetic copy interruption'):
        persistence.IncrementalPersistence(source, target)
    assert not (target/'epochs/epoch-000001/complete.json').exists()
    assert inspect(target)['last'] is None
    monkeypatch.setattr(persistence, 'copy_checked', original)
    persistence.IncrementalPersistence(source, target)
    assert inspect(target)['last'] == 'epoch-000001'


def test_new_session_rejects_corrupt_old_acknowledgement(dataset, tmp_path):
    source, target = tmp_path/'source', tmp_path/'target'
    cfg = ExperimentConfig(architecture='deeplabv3plus-resnet18', weights='imagenet-resnet18-v1', input_size=64, epochs=2)
    run(dataset, cfg, source, _fixture_factory=tiny)
    persistence.IncrementalPersistence(source, target)
    (target/'epochs/epoch-000001/checkpoint.pt').write_bytes(b'corrupt retained bytes')
    with pytest.raises(ValueError, match='checksum mismatch'):
        persistence.IncrementalPersistence(source, target)
