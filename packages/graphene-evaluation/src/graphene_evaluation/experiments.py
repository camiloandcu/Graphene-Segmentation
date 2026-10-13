"""Reviewed challenger training with immutable epochs and exact-source recovery."""
import argparse
import hashlib
import json
import sys
from pathlib import Path
from importlib.metadata import version

import torch
from graphene_dataset_contract.common import identity, read_json, write_json
from graphene_training.config import environment as baseline_environment, compatible, PREPROCESSING
from graphene_training.data import preflight
from graphene_training.engine import seed_all, components, restore_rng
from graphene_training.storage import inspect, load_state, lock, run_record, verify_generation, separate_destination
from .config import ExperimentConfig
from .candidates import architecture, pretrained
from .training import train


def environment(config):
    result = baseline_environment(config)
    source = hashlib.sha256()
    for path in sorted(Path(__file__).parent.glob('*.py')):
        source.update(path.name.encode()); source.update(path.read_bytes())
    result['evaluation_source_sha256'] = source.hexdigest()
    result['evaluation_packages'] = {n: version(n) for n in ('graphene-evaluation', 'transformers', 'huggingface-hub', 'scipy')}
    return result


def run(dataset, config, output, *, _fixture_factory=None, _stop_after=None):
    config = ExperimentConfig.model_validate(config) if isinstance(config, dict) else config
    evidence, env = preflight(dataset, config), environment(config)
    output = Path(output)
    if output.exists() or output.is_symlink():
        raise ValueError('Use a new experiment output')
    if config.persistence_directory:
        separate_destination(output, config.persistence_directory)
    seed_all(config.seed)
    if _fixture_factory:
        model, weights = _fixture_factory(), {'initialization': 'synthetic-random-fixture'}
    else:
        model, weights = pretrained(config, output.parent / '.reviewed-weights')
    record = {'schema_version': 1, 'config': config.model_dump(), 'dataset': evidence,
              'environment': env, 'weights': weights, 'preprocessing': PREPROCESSING.model_dump(mode='json'),
              'selection': 'validation foreground macro Dice; earliest exact tie'}
    record['run_fingerprint'] = identity(record)
    output.mkdir(parents=True, exist_ok=False)
    (output / 'epochs').mkdir()
    write_json(output / 'run.json', record)
    with lock(output):
        optimizer, scheduler, scaler, generator = components(model, config)
        return train(dataset, config, output, model, optimizer, scheduler, scaler, generator,
                     start=1, history=[], best_epoch=0, best_score=-1., stop_after=_stop_after)


def resume(dataset, output, generation, *, _fixture_factory=None, _stop_after=None):
    output = Path(output)
    status = inspect(output)
    record = status['run']
    config = ExperimentConfig.model_validate(record['config'])
    if generation != status['last']:
        raise ValueError('Resume only the latest completed generation')
    if preflight(dataset, config) != record['dataset']:
        raise ValueError('Dataset or supervised support changed')
    if not compatible(record['environment'], environment(config)):
        raise ValueError('Training/evaluation source or runtime changed; restore the recorded environment')
    fixture = record['weights']['initialization'] == 'synthetic-random-fixture'
    if fixture != (_fixture_factory is not None):
        raise ValueError('Fixture and pretrained runs cannot be interchanged')
    state = load_state(output, generation)
    meta, history, _ = verify_generation(output, generation)
    seed_all(config.seed)
    model = _fixture_factory() if fixture else architecture(config.architecture)
    optimizer, scheduler, scaler, generator = components(model, config)
    model.load_state_dict(state['model'], strict=True)
    optimizer.load_state_dict(state['optimizer']); scheduler.load_state_dict(state['scheduler'])
    scaler.load_state_dict(state['scaler']); generator.set_state(state['generator'])
    restore_rng(state['rng'])
    with lock(output):
        if inspect(output)['last'] != generation:
            raise ValueError('Run advanced during recovery validation')
        return train(dataset, config, output, model, optimizer, scheduler, scaler, generator,
                     start=meta['next_epoch'], history=history, best_epoch=meta['best_epoch'],
                     best_score=meta['best_score'], stop_after=_stop_after)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for name in ('check', 'run', 'admit'):
        p = commands.add_parser(name); p.add_argument('dataset', type=Path)
        p.add_argument('--config', type=Path, required=True)
        if name in ('run', 'admit'): p.add_argument('--output', type=Path, required=True)
    p = commands.add_parser('resume'); p.add_argument('dataset', type=Path)
    p.add_argument('--run', type=Path, required=True); p.add_argument('--checkpoint', required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == 'resume':
            result = resume(args.dataset, args.run, args.checkpoint)
        else:
            config = ExperimentConfig.model_validate(read_json(args.config))
            if args.command == 'admit':
                from .admission import admit
                preflight(args.dataset, config)
                if args.output.exists(): raise ValueError('Use a new admission output')
                result = admit(config, args.output.parent/'.reviewed-weights')
                write_json(args.output, result)
            else:
                result = {'dataset': preflight(args.dataset, config), 'environment': environment(config)} if args.command == 'check' else run(args.dataset, config, args.output)
        print(json.dumps(result, indent=2, allow_nan=False)); return 0
    except (ValueError, OSError, RuntimeError) as exc:
        print(json.dumps({'status': 'failed', 'error': str(exc)}), file=sys.stderr); return 2


if __name__ == '__main__': raise SystemExit(main())
