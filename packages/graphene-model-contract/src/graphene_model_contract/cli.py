"""Developer/exporter check, separate from the future model-import UI."""

import argparse
import json
from pathlib import Path

from .errors import ContractError
from .package import validate_file


def main():
    parser = argparse.ArgumentParser(
        description="Check a portable graphene model package on CPU."
    )
    parser.add_argument("package", type=Path)
    args = parser.parse_args()
    try:
        result = validate_file(args.package)
    except (ContractError, OSError) as error:
        print(
            json.dumps(
                {
                    "compatible": False,
                    "code": getattr(error, "code", "read_failed"),
                    "message": str(error)
                    if isinstance(error, ContractError)
                    else "Cannot read package.",
                }
            )
        )
        return 1
    print(
        json.dumps(
            {
                "compatible": True,
                "model_id": str(result.manifest.model_id),
                "bundle_sha256": result.bundle_sha256,
                "evaluation": result.evidence_kind,
                "evaluation_verified": False,
                "smoke": result.smoke,
            },
            indent=2,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
