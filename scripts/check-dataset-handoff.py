"""Reproduce WI-05 real blocked and synthetic ready evidence in a NEW directory."""
import argparse
import json
import sys
from importlib.metadata import version
from pathlib import Path

from graphene_dataset_contract import DatasetError, check, iter_samples, prepare
from graphene_dataset_contract.common import decode, digest, identity, read_bytes, read_json, write_json

# Reuse synthetic fixture construction; this verification command needs pytest.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "packages/graphene-dataset-contract/tests"))
from conftest import make_source, reviewed


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--audit", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        parser.error("Use a new evidence directory")
    args.output.mkdir(parents=True)
    before = digest(read_bytes(args.source))
    reports = [prepare(args.source, args.output / f"real-{i}") for i in (1, 2)]
    assert reports[0] == reports[1] and reports[0]["status"] == "blocked"
    assert reports[0]["counts"] == {"images": 40, "annotations": 759, "conflicting_images": 10, "conflict_pixels": 10578}
    audit = {s["audit_id"]: s for s in read_json(args.audit / "inventory.json")}
    for sample in reports[0]["inventory"]:
        original = audit[sample["sample_id"]]
        assert sample["source_sha256"] == original["sha256"]
        assert sample["rgb_sha256"] == original["pixel_sha256"]
        assert sample["class_pixels"] == original["class_pixels"]
        mask = decode(read_bytes(args.audit / "masks" / f"{sample['sample_id']}.png"), mask=True)
        assert sample["mask_pixels_sha256"] == digest(mask.tobytes())
    groups = read_json(args.output / "real-1/group-evidence.json")
    assert len(groups["pairs"]) == 15
    for directory in (args.output / "real-1", args.output / "real-2"):
        try:
            check(directory)
        except DatasetError:
            pass
        else:
            raise AssertionError("Blocked lab evidence accepted as a dataset")
    assert digest(read_bytes(args.source)) == before
    source = make_source(args.output / "synthetic.zip")
    review = reviewed(source, args.output)
    for i in (1, 2):
        assert prepare(source, args.output / f"synthetic-{i}", review_path=review)["status"] == "ready"
    a, b = check(args.output / "synthetic-1"), check(args.output / "synthetic-2")
    assert a.dataset_fingerprint == b.dataset_fingerprint
    assert a.split_fingerprint == b.split_fingerprint
    consumed = {role: len(list(iter_samples(args.output / "synthetic-1", role))) for role in ("train", "validation", "test")}
    summary = {"real_status": "blocked", "real_counts": reports[0]["counts"],
               "real_report_fingerprint": identity(reports[0]), "all_40_masks_match_wi03": True,
               "source_unchanged": True, "candidate_pairs": 15, "real_ready_handoff": "pending genuine lab review",
               "synthetic_status": "ready", "synthetic_dataset_fingerprint": a.dataset_fingerprint,
               "synthetic_split_fingerprint": a.split_fingerprint, "consumed_synthetic_roles": consumed,
               "environment": {name: version(name) for name in ("numpy", "Pillow", "pycocotools", "pydantic")}}
    write_json(args.output / "summary.json", summary)
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
