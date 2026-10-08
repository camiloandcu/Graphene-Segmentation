"""Independent small-image checks for the data-audit failure boundaries."""

import hashlib
import io
import json
from pathlib import Path
import sys
import zipfile

import numpy as np
from PIL import Image
import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from audit_lab_dataset import polygon_mask, rasterize, run, validate_archive
from wi03_similarity import compare_pairs, descriptors, filename_group


def annotation(category=1, polygon=None):
    return {"id": 0, "category_id": category, "image_id": 0,
            "segmentation": [polygon or [1, 1, 5, 1, 5, 5, 1, 5]], "iscrowd": 0}


def test_source_ids_are_mapped_by_name_not_number():
    mask, conflict, issues, counts = rasterize([annotation(1)], {1: "bulk", 2: "few-layer"}, 8, 8)
    expected = np.zeros((8, 8), dtype=np.uint8)
    expected[1:5, 1:5] = 2
    np.testing.assert_array_equal(mask, expected)
    assert conflict == 0 and issues == [] and counts == {"bulk": 1}


def test_incompatible_overlap_is_ignored_and_order_independent():
    labels = [annotation(1), annotation(2)]
    left = rasterize(labels, {1: "bulk", 2: "few-layer"}, 8, 8)
    right = rasterize(labels[::-1], {1: "bulk", 2: "few-layer"}, 8, 8)
    expected = np.zeros((8, 8), dtype=np.uint8)
    expected[1:5, 1:5] = 255
    np.testing.assert_array_equal(left[0], expected)
    np.testing.assert_array_equal(right[0], expected)
    assert left[1] == 16


def test_unknown_source_category_is_not_background_evidence():
    _, _, issues, counts = rasterize([annotation(99)], {99: "unreviewed"}, 8, 8)
    assert issues[0]["reason"] == "Unresolved source class"
    assert counts == {}


@pytest.mark.parametrize("polygon", [
    [1, 1, 2, 2], [1, 1, 2, 2, 3, 3, 4],
    [-1, 1, 5, 1, 5, 5], [1, 1, 9, 1, 5, 5],
    [1, 1, float("nan"), 1, 5, 5], [1, 1, 2, 2, 3, 3],
])
def test_invalid_polygons_have_specific_failure(polygon):
    with pytest.raises(ValueError):
        polygon_mask(annotation(polygon=polygon), 8, 8)


def test_box_only_annotation_is_not_segmentation():
    with pytest.raises(ValueError, match="Missing polygons"):
        polygon_mask({"bbox": [1, 1, 4, 4]}, 8, 8)


@pytest.mark.parametrize("name", ["../escape.jpg", "/absolute.jpg", "train\\escape.jpg"])
def test_unsafe_archive_members_are_rejected(tmp_path, name):
    path = tmp_path / "bad.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr(name, b"x")
    with zipfile.ZipFile(path) as archive, pytest.raises(ValueError, match="Unsafe"):
        validate_archive(archive)


def make_export(path, *, image_exists=True, width=8, labels=True, orphan=False):
    image = Image.new("RGB", (8, 8), (50, 70, 90))
    buffer = io.BytesIO()
    image.save(buffer, format="PNG")
    label = annotation()
    if orphan:
        label["image_id"] = 9
    doc = {"categories": [{"id": 1, "name": "bulk"}],
           "images": [{"id": 0, "file_name": "source.png", "width": width, "height": 8}],
           "annotations": [label] if labels else []}
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("train/_annotations.coco.json", json.dumps(doc))
        if image_exists:
            archive.writestr("train/source.png", buffer.getvalue())


@pytest.mark.parametrize("options,reason", [
    ({"image_exists": False}, "no item"),
    ({"width": 9}, "Decoded dimensions"),
    ({"labels": False}, "No annotations"),
])
def test_real_manifest_records_missing_invalid_or_unlabeled_entries(tmp_path, options, reason):
    path, output = tmp_path / "source.zip", tmp_path / "evidence"
    make_export(path, **options)
    before = hashlib.sha256(path.read_bytes()).hexdigest()
    run(path, output)
    record = json.loads((output / "inventory.json").read_text())[0]
    assert not record["usable_for_pixel_audit"]
    assert reason.lower() in record["issues"][0]["reason"].lower()
    assert hashlib.sha256(path.read_bytes()).hexdigest() == before
    assert json.loads((output / "proposed_split.json").read_text())[0]["proposed_role"] == "unassigned"
    with pytest.raises(ValueError, match="new output directory"):
        run(path, output)


def test_orphan_annotation_is_not_lost_from_report(tmp_path):
    path, output = tmp_path / "source.zip", tmp_path / "evidence"
    make_export(path, orphan=True)
    run(path, output)
    summary = json.loads((output / "summary.json").read_text())
    assert summary["metadata_issues"][0]["reason"] == "Orphan annotation"
    assert summary["source_annotation_count"] == 1
    assert summary["annotation_count"] == 0


def test_pixel_duplicate_with_different_bytes_and_labels_is_flagged():
    records = [
        {"audit_id": "a", "source_split": "train", "pixel_sha256": "same",
         "sha256": "different-1", "mask_sha256": "label-1", "filename_group_candidate": None},
        {"audit_id": "b", "source_split": "test", "pixel_sha256": "same",
         "sha256": "different-2", "mask_sha256": "label-2", "filename_group_candidate": None},
    ]
    feature = descriptors(Image.new("RGB", (8, 8), "white"))
    pair = compare_pairs(records, {"a": feature, "b": feature})[0]
    assert pair["pixel_identical"] and not pair["byte_identical"]
    assert pair["cross_split"] and not pair["mask_identical"]


def test_expanded_byte_budget_is_checked_before_reading(tmp_path, monkeypatch):
    import audit_lab_dataset
    monkeypatch.setattr(audit_lab_dataset, "MAX_EXPANDED", 2)
    path = tmp_path / "large.zip"
    with zipfile.ZipFile(path, "w") as archive:
        archive.writestr("entry.txt", "four")
    with zipfile.ZipFile(path) as archive, pytest.raises(ValueError, match="expanded-byte budget"):
        validate_archive(archive)


def test_filename_group_is_only_a_candidate_and_preserves_sample_token():
    one = filename_group("8_Grafeno_Maio_070524_Amostra-1_Floco-1_20X.jpg")
    two = filename_group("9_Grafeno_Maio_070524_Amostra-1_Floco-2_20X.jpg")
    other = filename_group("13_Grafeno_Maio_070524_Amostra-4_20X.jpg")
    assert one == two and one != other
    assert filename_group("unknown.jpg") is None
