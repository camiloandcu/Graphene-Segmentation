"""Synthetic contract evidence; these cases are not laboratory model results."""
import json
import numpy as np
import pytest
import torch
from graphene_training.storage import load_state
from graphene_evaluation.metrics import confusion, pixels, components
from graphene_evaluation.predict import decision, logits
from graphene_evaluation.config import ExperimentConfig
from graphene_evaluation.experiments import run, resume
from graphene_evaluation import report


def tiny():
    return torch.nn.Sequential(torch.nn.Conv2d(3, 4, 1), torch.nn.Dropout2d(.2), torch.nn.Conv2d(4, 3, 1))


def test_pixels_ignore_unknown_and_report_absent_support():
    target = np.array([[0, 1, 255], [1, 2, 255]], dtype=np.uint8)
    predicted = np.array([[0, 1, 1], [2, 2, 0]], dtype=np.uint8)
    matrix = confusion(target, predicted)
    assert matrix.tolist() == [[1, 0, 0], [0, 1, 1], [0, 0, 1]]
    assert pixels(matrix)['classes'][1]['recall'] == .5
    assert pixels(np.zeros((3, 3), dtype=int))['foreground_macro_iou'] is None


def test_unknown_bridge_remains_one_component_and_censored():
    target = np.array([[1, 255, 1]], dtype=np.uint8)
    predicted = np.ones((1, 3), dtype=np.uint8)
    result = components(target, predicted)
    assert result['reference_components'] == 2
    assert result['prediction_components'] == 1
    assert len(result['matches']) == 1
    assert result['matches'][0]['reference_id'] == 1
    assert result['annotated_component_recall_proxy'] == .5
    assert result['unknown_intersecting_ids'] == [1]
    assert result['known_support_unmatched_ids'] == []
    assert result['predictions'][0]['unknown_fraction'] == pytest.approx(1/3)


def test_false_known_vs_indeterminate_and_fragment():
    target = np.array([[0, 0, 0, 255, 255], [0, 0, 0, 255, 255]], dtype=np.uint8)
    predicted = np.array([[1, 0, 0, 0, 1], [0, 0, 0, 0, 1]], dtype=np.uint8)
    result = components(target, predicted)
    assert result['known_support_no_overlap_ids'] == [1]
    assert result['indeterminate_unmatched_ids'] == [2]
    assert result['annotated_component_recall_proxy'] is None
    target = np.ones((1, 5), dtype=np.uint8)
    result = components(target, np.array([[1, 0, 0, 0, 1]], dtype=np.uint8))
    assert result['known_support_localization_or_fragment_ids'] == [1, 2]
    assert result['missed_reference_ids'] == [1]


def test_decision_and_original_coordinate_geometries():
    class Constant(torch.nn.Module):
        def forward(self, x):
            return torch.ones((len(x), 3, *x.shape[-2:]))
    image = np.zeros((83, 117, 3), dtype=np.uint8)
    for geometry in ('letterbox', 'tiles'):
        value = logits(Constant(), image, size=64, geometry=geometry, stride=48)
        assert value.shape == (3, 83, 117)
        assert np.all(decision(value) == 0)
        assert np.all(decision(value, .3) == 1)
        assert np.all(decision(value, .5) == 0)


def test_exact_experiment_resume(dataset, tmp_path):
    cfg = ExperimentConfig(architecture='deeplabv3plus-resnet18', weights='imagenet-resnet18-v1', input_size=64, epochs=2)
    full, partial = tmp_path/'full', tmp_path/'partial'
    run(dataset, cfg, full, _fixture_factory=tiny)
    run(dataset, cfg, partial, _fixture_factory=tiny, _stop_after=1)
    resume(dataset, partial, 'epoch-000001', _fixture_factory=tiny)
    a, b = load_state(full, 'epoch-000002'), load_state(partial, 'epoch-000002')
    for key in a['model']:
        assert torch.equal(a['model'][key], b['model'][key])
    assert torch.equal(a['rng']['torch'], b['rng']['torch'])


def test_freeze_prevents_test_prediction_and_binds_setting(dataset, tmp_path, monkeypatch):
    monkeypatch.setattr(report, 'architecture', lambda name: tiny())
    cfg = ExperimentConfig(architecture='deeplabv3plus-resnet18', weights='imagenet-resnet18-v1', input_size=64, epochs=1)
    directory = tmp_path/'run'
    run(dataset, cfg, directory, _fixture_factory=tiny)
    with pytest.raises(ValueError, match='Test requires'):
        report.evaluate('does-not-exist', directory, 'epoch-000001', tmp_path/'forbidden', role='test')
    development = tmp_path/'development'
    result = report.evaluate(dataset, directory, 'epoch-000001', development, panels=False)
    assert result['support']['images'] == 2
    frozen = report.freeze_report(development/'report.json', tmp_path/'freeze.json', reviewer='synthetic fixture', date='2026-10-11', evidence='Synthetic test only')
    with pytest.raises(ValueError, match='do not match'):
        report.evaluate(dataset, directory, 'epoch-000001', tmp_path/'wrong', role='test', sweep=False, freeze=frozen, threshold=.5)
    result = report.evaluate(dataset, directory, 'epoch-000001', tmp_path/'fixed', role='test', sweep=False, freeze=frozen, panels=False)
    assert result['support']['images'] == 1
    assert list(result['settings']) == ['argmax']


def test_semantic_adapters_and_frozen_probe_gradients():
    from graphene_evaluation.candidates import architecture
    from graphene_training.objective import loss
    torch.set_num_threads(1)
    rgb = torch.randn(1,3,64,64)
    target = torch.randint(0,3,(1,64,64)); target[:,::2,::3] = 255
    for name in ('segformer-b0', 'dinov3-vits16-linear', 'deeplabv3plus-resnet18'):
        model = architecture(name).train()
        value = model(rgb)
        assert value.shape == (1,3,64,64)
        loss(value,target).backward()
        if name == 'dinov3-vits16-linear':
            assert not model.encoder.training
            assert all(p.grad is None for p in model.encoder.parameters())
            assert torch.isfinite(model.head.weight.grad).all()
        else:
            assert any(p.grad is not None for p in model.parameters())


def test_comparison_rejects_test_and_changed_support(dataset, tmp_path, monkeypatch):
    from graphene_evaluation.compare import compare
    from graphene_dataset_contract.common import identity
    monkeypatch.setattr(report, 'architecture', lambda name: tiny())
    cfg=ExperimentConfig(architecture='deeplabv3plus-resnet18',weights='imagenet-resnet18-v1',input_size=64,epochs=1)
    directory=tmp_path/'run'; run(dataset,cfg,directory,_fixture_factory=tiny)
    first=tmp_path/'first'; second=tmp_path/'second'
    report.evaluate(dataset,directory,'epoch-000001',first,panels=False,sweep=False)
    result=report.evaluate(dataset,directory,'epoch-000001',second,panels=False,sweep=False)
    comparison=compare([first/'report.json',second/'report.json'])
    assert comparison['bootstrap']['available']
    result['role']='test'; result['report_fingerprint']=identity({k:v for k,v in result.items() if k!='report_fingerprint'})
    (second/'report.json').write_text(json.dumps(result))
    with pytest.raises(ValueError,match='validation only'):
        compare([first/'report.json',second/'report.json'])
