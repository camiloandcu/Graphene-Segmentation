import io
import json
import zipfile
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from graphene_dataset_contract import prepare
from graphene_dataset_contract.common import digest


def make_source(path: Path, *, edit=None, duplicate=False, image_options=None):
    docs = {}
    for split in ("train", "valid", "test"):
        docs[split] = {
            "images": [{"id": 0, "file_name": "original.png", "width": 10, "height": 6}],
            "categories": [{"id": 0, "name": "unused-parent"}, {"id": 1, "name": "bulk"}, {"id": 2, "name": "few-layer"}],
            "annotations": [
                {"id": 1, "image_id": 0, "category_id": 2, "segmentation": [[1, 1, 3, 1, 3, 3, 1, 3]]},
                {"id": 2, "image_id": 0, "category_id": 1, "segmentation": [[5, 1, 8, 1, 8, 4, 5, 4]]},
            ],
            "info": {"version": "synthetic-fixture"}, "licenses": [{"name": "synthetic test only"}],
        }
    if edit:
        edit(docs)
    with zipfile.ZipFile(path, "w") as archive:
        for index, (split, doc) in enumerate(docs.items()):
            archive.writestr(f"{split}/_annotations.coco.json", json.dumps(doc))
            rgb = np.arange(180, dtype=np.uint8).reshape(6, 10, 3)
            rgb = rgb + (0 if duplicate else index * 20)
            image = Image.fromarray(rgb)
            buf = io.BytesIO()
            image.save(buf, format="PNG", **(image_options or {}))
            archive.writestr(f"{split}/original.png", buf.getvalue())
        archive.writestr("README.txt", "Synthetic fixtures, not lab annotations.")
    return path


def reviewed(source: Path, tmp_path: Path, *, changes=None):
    blocked = tmp_path / f"template-{len(list(tmp_path.iterdir()))}"
    assert prepare(source, blocked)["status"] == "blocked"
    review = json.loads((blocked / "review-template.json").read_text())
    review.update(reference="synthetic-fixture-review", reviewer="pytest fixture author", date="2026-10-08",
                  mapping={"few-layer": 1, "bulk": 2}, class_semantics_approved=True,
                  evaluation={"status": "exploratory", "evidence": "fixture construction",
                              "limitations": ["Synthetic examples cannot establish lab independence"]})
    for sample in review["samples"]:
        sample.update(role={"train": "train", "valid": "validation", "test": "test"}[sample["sample_id"].split("-")[0]],
                      origin="human", origin_evidence="fixture authored polygons", eligibility_approved=True,
                      completeness="exhaustive", group_status="known", group=sample["sample_id"],
                      group_evidence="separately generated synthetic pixels")
    if changes:
        changes(review)
    dest = tmp_path / f"review-{len(list(tmp_path.iterdir()))}.json"
    dest.write_text(json.dumps(review))
    return dest


@pytest.fixture
def source(tmp_path):
    return make_source(tmp_path / "source.zip")


@pytest.fixture
def ready(source, tmp_path):
    output = tmp_path / "ready"
    assert prepare(source, output, review_path=reviewed(source, tmp_path))["status"] == "ready"
    return output
