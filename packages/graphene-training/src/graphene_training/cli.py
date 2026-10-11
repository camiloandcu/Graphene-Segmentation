"""Thin CLI; failures leave previous completed epoch generations intact."""
import argparse
import json
import sys
from pathlib import Path
from graphene_dataset_contract.common import read_json
from .config import TrainingConfig, environment
from .data import preflight
from .engine import run, resume
from .storage import inspect, persist


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    for action in ('check', 'run'):
        p = commands.add_parser(action)
        p.add_argument('dataset', type=Path)
        p.add_argument('--config', type=Path, required=True)
        if action == 'run': p.add_argument('--output', type=Path, required=True)
    p = commands.add_parser('resume')
    p.add_argument('dataset', type=Path); p.add_argument('--run', type=Path, required=True)
    p.add_argument('--checkpoint', required=True, help='epoch-NNNNNN')
    p = commands.add_parser('inspect'); p.add_argument('run', type=Path)
    p = commands.add_parser('persist'); p.add_argument('run', type=Path); p.add_argument('destination', type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command in ('check', 'run'):
            config = TrainingConfig.model_validate(read_json(args.config))
            result = ({'dataset': preflight(args.dataset, config), 'environment': environment(config)}
                      if args.command == 'check' else run(args.dataset, config, args.output))
        elif args.command == 'resume': result = resume(args.dataset, args.run, args.checkpoint)
        elif args.command == 'persist': result = persist(args.run, args.destination)
        else: result = inspect(args.run)
        print(json.dumps(result, indent=2, allow_nan=False)); return 0
    except (ValueError, OSError, RuntimeError) as exc:
        print(json.dumps({'status': 'failed', 'error': str(exc)}), file=sys.stderr); return 2


if __name__ == '__main__': raise SystemExit(main())
