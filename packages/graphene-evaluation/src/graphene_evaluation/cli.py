"""Evaluate immutable checkpoints; test access requires an explicit reviewed freeze."""
import argparse
import json
import sys
from pathlib import Path
from graphene_dataset_contract.common import read_json, write_json
from .report import evaluate, freeze_report
from .benchmark import benchmark
from .compare import compare


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest='command', required=True)
    p = commands.add_parser('score')
    p.add_argument('dataset', type=Path); p.add_argument('--run', type=Path, required=True)
    p.add_argument('--checkpoint', required=True); p.add_argument('--output', type=Path, required=True)
    p.add_argument('--role', choices=['validation', 'test'], default='validation')
    p.add_argument('--device', choices=['cpu', 'cuda'], default='cpu')
    p.add_argument('--size', type=int); p.add_argument('--geometry', choices=['letterbox', 'tiles'], default='letterbox')
    p.add_argument('--stride', type=int, default=384); p.add_argument('--threshold', type=float)
    p.add_argument('--no-sweep', action='store_true'); p.add_argument('--freeze', type=Path)
    p.add_argument('--no-panels', action='store_true'); p.add_argument('--cache-logits', action='store_true')
    p = commands.add_parser('freeze')
    p.add_argument('report', type=Path); p.add_argument('--output', type=Path, required=True)
    p.add_argument('--reviewer', required=True); p.add_argument('--date', required=True)
    p.add_argument('--evidence', required=True); p.add_argument('--setting', default='argmax')
    p = commands.add_parser('benchmark')
    p.add_argument('dataset', type=Path); p.add_argument('--run', type=Path, required=True)
    p.add_argument('--checkpoint', required=True); p.add_argument('--output', type=Path, required=True)
    p.add_argument('--size', type=int); p.add_argument('--geometry', choices=['letterbox','tiles'], default='letterbox')
    p.add_argument('--stride', type=int, default=384); p.add_argument('--device', choices=['cpu','cuda'], default='cpu')
    p.add_argument('--threshold', type=float)
    p = commands.add_parser('compare'); p.add_argument('reports', type=Path, nargs='+')
    p.add_argument('--output', type=Path, required=True); p.add_argument('--setting', default='argmax')
    args = parser.parse_args(argv)
    try:
        if args.command in ('benchmark', 'compare'):
            if args.output.exists(): raise ValueError('Use a new immutable output')
            result = compare(args.reports, setting=args.setting) if args.command == 'compare' else benchmark(
                args.dataset, args.run, args.checkpoint, size=args.size, geometry=args.geometry,
                stride=args.stride, device=args.device, threshold=args.threshold)
            write_json(args.output, result)
        elif args.command == 'freeze':
            result = freeze_report(args.report, args.output, reviewer=args.reviewer, date=args.date, evidence=args.evidence, setting=args.setting)
        else:
            result = evaluate(args.dataset, args.run, args.checkpoint, args.output, role=args.role,
                              device=args.device, size=args.size, geometry=args.geometry, stride=args.stride,
                              threshold=args.threshold, sweep=not args.no_sweep,
                              freeze=read_json(args.freeze) if args.freeze else None,
                              panels=not args.no_panels, cache=args.cache_logits)
        print(json.dumps(result, indent=2, allow_nan=False)); return 0
    except (ValueError, OSError, RuntimeError) as exc:
        print(json.dumps({'status': 'failed', 'error': str(exc)}), file=sys.stderr); return 2


if __name__ == '__main__': raise SystemExit(main())
