"""Offline CLI with stable exit statuses and machine-readable results."""
import argparse
import json
import sys
from pathlib import Path

from .artifact import check, prepare
from .common import DatasetError


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    prep = commands.add_parser("prepare", help="Validate a COCO ZIP and prepare a new handoff")
    prep.add_argument("source", type=Path)
    prep.add_argument("--output", type=Path, required=True)
    prep.add_argument("--partial", action="store_true", help="Version 2: unannotated pixels remain unknown")
    prep.add_argument("--review", type=Path)
    prep.add_argument("--groups", type=Path, help="Additional source-bound candidate evidence JSON")
    verify = commands.add_parser("check", help="Validate a ready artifact before consumption")
    verify.add_argument("dataset", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "prepare":
            report = prepare(args.source, args.output, review_path=args.review, groups_path=args.groups, partial=args.partial)
            print(json.dumps(report, indent=2))
            return {"ready": 0, "blocked": 2, "invalid": 3}[report["status"]]
        manifest = check(args.dataset)
        print(json.dumps({"status": "ready", "dataset_fingerprint": manifest.dataset_fingerprint,
                          "split_fingerprint": manifest.split_fingerprint,
                          "evaluation": manifest.review.evaluation.model_dump()}, indent=2))
        return 0
    except DatasetError as exc:
        print(json.dumps({"status": "invalid", "error": str(exc)}), file=sys.stderr)
        return 3
    except OSError as exc:
        print(json.dumps({"status": "io-error", "error": str(exc)}), file=sys.stderr)
        return 4


if __name__ == "__main__":
    raise SystemExit(main())
