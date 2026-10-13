"""Immutable role-scoped reports, model binding and explicit test-freeze gate."""
from __future__ import annotations
import hashlib
import platform
import resource
import time
from importlib.metadata import version
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageDraw
from graphene_dataset_contract import check, iter_samples
from graphene_dataset_contract.common import identity, read_json, write_json
from graphene_dataset_contract.artifact import publish
from graphene_training.config import TrainingConfig, PREPROCESSING
from graphene_training.storage import load_state, run_record, verify_generation, file_hash
from .config import ExperimentConfig
from .candidates import architecture
from .metrics import confusion, pixels, components, unavailable
from graphene_training.engine import seed_all
from .experiments import environment
from .predict import logits, decision

THRESHOLDS = (None, .2, .3, .4, .5, .6, .7, .8)


def configuration(record):
    return (TrainingConfig if record['config']['schema_version'] == 1 else ExperimentConfig).model_validate(record['config'])


def checkpoint(run, generation, dataset):
    record = run_record(run)
    meta, _, path = verify_generation(run, generation)
    manifest = check(dataset)
    support = getattr(manifest, 'supervision_fingerprint', manifest.dataset_fingerprint)
    actual = {'dataset_fingerprint': manifest.dataset_fingerprint, 'split_fingerprint': manifest.split_fingerprint,
              'supervision_fingerprint': support}
    if any(record['dataset'].get(k) != v for k, v in actual.items()):
        raise ValueError('Run/data split or supervision identity mismatch')
    config = configuration(record)
    model = architecture(config.architecture)
    state = load_state(run, generation)
    model.load_state_dict(state['model'], strict=True)
    binding = {**actual, 'run_fingerprint': record['run_fingerprint'],
               'checkpoint_sha256': file_hash(path/'checkpoint.pt'), 'generation': generation,
               'architecture': config.architecture, 'seed': config.seed, 'config': record['config'],
               'preprocessing': PREPROCESSING.model_dump(mode='json'), 'weights': record['weights'],
               'training_environment': record['environment'], 'recorded_best_epoch': meta['best_epoch']}
    return model, config, manifest, binding


def scope(binding, *, size, geometry, stride, threshold):
    return {**binding, 'settings': {'input_size': size, 'geometry': geometry,
            'stride': stride if geometry == 'tiles' else None,
            'decision': 'argmax' if threshold is None else 'few_layer_threshold', 'threshold': threshold,
            'ties': 'lower_id'}}


def validate_freeze(freeze, selected):
    if not isinstance(freeze, dict) or set(freeze) != {'schema_version', 'selection', 'development_report_sha256',
                                                    'reviewer', 'date', 'evidence', 'freeze_fingerprint'}:
        raise ValueError('A complete stakeholder freeze record is required before test predictions')
    if freeze['schema_version'] != 1 or freeze['selection'] != selected:
        raise ValueError('Frozen checkpoint/settings do not match requested test evaluation')
    if freeze['freeze_fingerprint'] != identity({k:v for k,v in freeze.items() if k != 'freeze_fingerprint'}):
        raise ValueError('Freeze record integrity mismatch')
    if not all(isinstance(freeze[k], str) and freeze[k].strip() for k in ('reviewer', 'date', 'evidence')):
        raise ValueError('Freeze needs genuine stakeholder review evidence')
    if len(freeze['development_report_sha256']) != 64:
        raise ValueError('Freeze needs the reviewed development-report SHA-256')


def freeze_report(report_path, output, *, reviewer, date, evidence, setting='argmax'):
    report = read_json(report_path)
    if report.get('role') != 'validation' or report.get('schema_version') != 1:
        raise ValueError('Freeze only a completed development report')
    if setting not in report['settings']:
        raise ValueError('Freeze only a setting actually evaluated on development')
    if report.get('report_fingerprint') != identity({k:v for k,v in report.items() if k != 'report_fingerprint'}):
        raise ValueError('Development report integrity mismatch')
    selected = {**report['binding'], 'settings': report['settings'][setting]['selection_settings']}
    result = {'schema_version': 1, 'selection': selected, 'development_report_sha256': file_hash(Path(report_path)),
              'reviewer': reviewer, 'date': date, 'evidence': evidence}
    result['freeze_fingerprint'] = identity(result)
    validate_freeze(result, selected)
    output = Path(output)
    if output.exists():
        raise ValueError('Freeze output must be new and immutable')
    write_json(output, result)
    return result


def panel(rgb, target, prediction, path):
    # Scientific evidence figure, preserving original RGB in the first panel.
    colors = np.array([[75, 95, 115], [46, 190, 112], [203, 95, 65]], dtype=np.uint8)
    supervision = np.full_like(rgb, 150)
    known = target != 255
    supervision[known] = colors[target[known]]
    overlay = (.6*rgb+.4*colors[prediction]).astype(np.uint8)
    errors = rgb.copy()
    errors[known & (target != prediction)] = (255, 0, 90)
    h, w = rgb.shape[:2]
    sheet = Image.new('RGB', (4*w, h+40), 'white')
    draw = ImageDraw.Draw(sheet)
    for i, (name, array) in enumerate(zip(('Original RGB', 'Reviewed labels / gray unknown', 'Prediction overlay', 'Supervised errors'),
                                         (rgb, supervision, overlay, errors))):
        sheet.paste(Image.fromarray(array), (i*w, 40)); draw.text((i*w+5, 12), name, fill='black')
    sheet.save(path)


def evaluate(dataset, run, generation, output, *, role='validation', device='cpu', size=None,
             geometry='letterbox', stride=384, threshold=None, sweep=True, freeze=None, panels=True,
             cache=False, _fixture_model=None):
    if role not in ('validation', 'test'):
        raise ValueError('Evaluation only uses declared validation or frozen test roles')
    if role == 'test' and (freeze is None or sweep):
        raise ValueError('Test requires a stakeholder freeze and a single fixed setting; no test sweep')
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise ValueError('Reports are immutable; use a new output directory')
    model, config, manifest, binding = checkpoint(run, generation, dataset)
    size = size or config.input_size
    if type(size) is not int or not 64 <= size <= 1024 or size % 32:
        raise ValueError('Evaluation input size must be divisible by 32 within 64..1024')
    if geometry not in ('letterbox','tiles') or (geometry == 'tiles' and not 0 < stride <= size):
        raise ValueError('Unsupported geometry or stride')
    selected = scope(binding, size=size, geometry=geometry, stride=stride, threshold=threshold)
    if role == 'test':
        validate_freeze(freeze if isinstance(freeze, dict) else read_json(freeze), selected)
    if device not in ('cpu', 'cuda') or (device == 'cuda' and not torch.cuda.is_available()):
        raise ValueError('Requested evaluation device is unavailable')
    seed_all(config.seed)
    evaluation_environment = environment(config.model_copy(update={'device':device,'precision':'float32'}))
    model = (_fixture_model or model).to(device).eval()
    choices = THRESHOLDS if sweep else (threshold,)
    settings = {('argmax' if t is None else f'threshold-{t:g}'): {'selection_settings': scope(
        {}, size=size, geometry=geometry, stride=stride, threshold=t)['settings'],
        'matrix': np.zeros((3, 3), dtype=np.int64), 'samples': []} for t in choices}
    import tempfile, shutil
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix='.evaluation-', dir=output.parent))
    elapsed, unknown, total = [], 0, 0
    try:
        begin = time.monotonic()
        for sample, rgb, target in iter_samples(dataset, role):
            start = time.monotonic()
            value = logits(model, rgb, device=device, size=size, geometry=geometry, stride=stride)
            elapsed.append((time.monotonic()-start)*1000)
            unknown += int((target == 255).sum()); total += target.size
            if cache:
                np.save(stage/f'{sample.sample_id}-logits.npy', value, allow_pickle=False)
            for t in choices:
                key = 'argmax' if t is None else f'threshold-{t:g}'
                predicted = decision(value, t)
                matrix = confusion(target, predicted)
                settings[key]['matrix'] += matrix
                settings[key]['samples'].append({'sample_id': sample.sample_id,
                    'image_sha256': sample.image_sha256, 'mask_sha256': sample.mask_sha256,
                    'supervised_pixels': int((target != 255).sum()), 'unknown_pixels': int((target == 255).sum()),
                    'pixels': pixels(matrix), 'components': components(target, predicted)})
                if panels:
                    panel(rgb, target, predicted, stage/f'{sample.sample_id}-{key}.png')
        if not elapsed:
            raise ValueError('Requested role has no images')
        for result in settings.values():
            result['pixels'] = pixels(result.pop('matrix'))
            records = [r['components'] for r in result['samples']]
            refs = sum(r['reference_components'] for r in records)
            matches = sum(len(r['matches']) for r in records)
            result['component_totals'] = {'reference_components': refs, 'matched_components': matches,
                'annotated_component_recall_proxy': matches/refs if refs else None,
                'known_support_unmatched': sum(len(r['known_support_unmatched_ids']) for r in records),
                'indeterminate_unmatched': sum(len(r['indeterminate_unmatched_ids']) for r in records)}
        groups = {s.sample_id: {'group': s.group, 'status': s.group_status} for s in manifest.review.samples}
        result = {'schema_version': 1, 'role': role, 'binding': binding, 'settings': settings,
                  'evaluation_environment': evaluation_environment,
                  'support': {'images': len(elapsed), 'total_pixels': total, 'unknown_pixels': unknown,
                              'unknown_fraction': unknown/total}, 'unsupported': unavailable(),
                  'groups': {r['sample_id']: groups[r['sample_id']] for r in next(iter(settings.values()))['samples']},
                  'resources': {'device': device, 'cpu': platform.processor() or platform.machine(),
                    'threads': torch.get_num_threads(), 'torch': version('torch'), 'numpy': version('numpy'),
                    'inference_ms': elapsed, 'median_ms': float(np.median(elapsed)),
                    'p95_ms': float(np.percentile(elapsed, 95)), 'warmup': 0, 'repeat_count': 1,
                    'definition': 'Single pass per role image; normalization, model, restoration included; not warmed benchmark',
                    'process_peak_rss_bytes': resource.getrusage(resource.RUSAGE_SELF).ru_maxrss*1024,
                    'elapsed_seconds': time.monotonic()-begin,
                    'cpu_feasibility': 'Hardware-specific pilot only; stakeholder lab latency/RAM acceptance pending'},
                  'freeze': (freeze if isinstance(freeze, dict) else read_json(freeze)) if role == 'test' else None,
                  'limitations': manifest.review.evaluation.model_dump()}
        result['report_fingerprint'] = identity(result)
        write_json(stage/'report.json', result)
        publish(stage, output)
        return result
    finally:
        if stage.exists():
            shutil.rmtree(stage)
