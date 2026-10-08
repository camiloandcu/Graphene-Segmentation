import io
import json
import os
import zipfile
from pathlib import Path

import numpy as np
import pytest
from PIL import Image

from conftest import make_source, reviewed
from graphene_dataset_contract import DatasetError, check, iter_samples, prepare
from graphene_dataset_contract import artifact
from graphene_dataset_contract.cli import main
from graphene_dataset_contract.common import digest, identity, read_json, write_json
from graphene_dataset_contract.schema import Manifest


def seal(output, edit):
    manifest = read_json(output / "manifest.json")
    edit(manifest)
    parsed = Manifest.model_validate(manifest)
    parsed.dataset_fingerprint = identity(parsed.model_dump(exclude={"dataset_fingerprint"}))
    write_json(output / "manifest.json", parsed.model_dump())
    write_json(output / "validation.json", artifact.report_for(
        parsed.samples, parsed.source.sha256, parsed.review, []).model_dump())


def test_ready_reproducible_geometry_and_consumer(source, tmp_path):
    before = source.read_bytes()
    review = reviewed(source, tmp_path)
    a, b = tmp_path / "a", tmp_path / "b"
    for output in (a, b):
        assert prepare(source, output, review_path=review)["status"] == "ready"
    ma, mb = check(a), check(b)
    assert ma.dataset_fingerprint == mb.dataset_fingerprint
    assert ma.split_fingerprint == mb.split_fingerprint
    assert source.read_bytes() == before
    assert ma.source.metadata["train"]["categories"][1]["name"] == "bulk"
    assert ma.source.annotation_files and ma.source.unknowns
    for role in ("train", "validation", "test"):
        [(sample, image, mask)] = list(iter_samples(a, role))
        assert image.shape == (6, 10, 3) and mask.shape == (6, 10)
        assert mask.dtype == np.uint8
        assert mask[1, 1] == 1 and mask[1, 5] == 2 and mask[0, 0] == 0
        assert sample.source_path.endswith("original.png")
    assert [s.original_role for s in ma.samples] == ["test", "train", "valid"]


def test_missing_review_is_blocked_not_ground_truth(source, tmp_path):
    output = tmp_path / "blocked"
    report = prepare(source, output)
    assert report["status"] == "blocked" and report["counts"]["images"] == 3
    assert not (output / "manifest.json").exists()
    template = read_json(output / "review-template.json")
    assert template["reviewer"] is None and template["samples"][0]["origin"] is None
    with pytest.raises(DatasetError, match="No ready manifest"):
        check(output)


@pytest.mark.parametrize("edit,reason", [
    (lambda d: d["train"]["annotations"].append(dict(d["train"]["annotations"][0])), "Duplicate"),
    (lambda d: d["train"]["images"].append(dict(d["train"]["images"][0])), "Duplicate"),
    (lambda d: d["train"]["annotations"][0].update(image_id=99), "Orphan"),
    (lambda d: d["train"]["annotations"][0].update(category_id=0), "unresolved"),
    (lambda d: d["train"]["annotations"][0].update(iscrowd=1), "crowd"),
    (lambda d: d["train"]["annotations"][0].update(segmentation={"counts": "abc"}), "polygons"),
    (lambda d: d["train"]["annotations"][0].update(segmentation=[[1, 2]]), "malformed"),
    (lambda d: d["train"]["annotations"][0].update(segmentation=[[0, 0, 1, 1, 2, 2]]), "degenerate"),
    (lambda d: d["train"]["annotations"][0].update(segmentation=[[-1, 0, 3, 0, 3, 3]]), "outside"),
    (lambda d: d["train"]["annotations"][0].update(segmentation=[[0, 0, float("nan"), 1, 2, 3]]), "Non-finite"),
    (lambda d: d["train"]["images"][0].update(width=11), "geometry"),
    (lambda d: d["train"]["images"][0].update(file_name="missing.png"), "Cannot read"),
    (lambda d: d["train"]["images"][0].update(file_name="../outside.png"), "Unsafe"),
    (lambda d: d["train"]["images"][0].update(width=True), "integer"),
])
def test_malformed_sources_never_publish(tmp_path, edit, reason):
    source = make_source(tmp_path / "bad.zip", edit=edit)
    before = source.read_bytes()
    result = prepare(source, tmp_path / "bad")
    assert result["status"] == "invalid" and reason in result["blockers"][0]
    assert source.read_bytes() == before
    assert not (tmp_path / "bad/manifest.json").exists()


@pytest.mark.parametrize("origin", ["prediction", "unknown", None])
def test_origin_never_promoted(source, tmp_path, origin):
    review = reviewed(source, tmp_path, changes=lambda r: r["samples"][0].update(origin=origin))
    report = prepare(source, tmp_path / "blocked", review_path=review)
    assert report["status"] == "blocked" and any("only reviewed human" in b for b in report["blockers"])


@pytest.mark.parametrize("changes,reason", [
    (lambda r: r.update(source_sha256="0" * 64), "digest mismatch"),
    (lambda r: r.update(mapping={"bulk": 1, "few-layer": 2}), "mapping"),
    (lambda r: r.update(class_semantics_approved=False), "semantics"),
    (lambda r: r.update(date="2026-99-99"), "date"),
    (lambda r: r["samples"].pop(), "exactly one"),
    (lambda r: r["samples"].append(r["samples"][0]), "exactly one"),
    (lambda r: r["samples"][0].update(source_path="test/stale.png"), "stale"),
    (lambda r: r["samples"][0].update(completeness="non-exhaustive"), "exhaustive"),
    (lambda r: r["samples"][0].update(role=None), "role"),
    (lambda r: r["samples"][0].update(group="same", group_status="unknown"), "unknown group"),
    (lambda r: r["evaluation"].update(status="independence-reviewed") or r["samples"][0].update(group=None, group_status="unknown"), "affirmative"),
])
def test_review_blocks_unresolved_decisions(source, tmp_path, changes, reason):
    review = reviewed(source, tmp_path, changes=changes)
    report = prepare(source, tmp_path / "blocked", review_path=review)
    assert report["status"] == "blocked"
    assert any(reason in b for b in report["blockers"])


def test_conflict_requires_review_and_is_order_independent(tmp_path):
    def conflict(docs):
        for doc in docs.values():
            doc["annotations"][1]["segmentation"] = doc["annotations"][0]["segmentation"]
    source = make_source(tmp_path / "conflict.zip", edit=conflict)
    review = reviewed(source, tmp_path)
    report = prepare(source, tmp_path / "rejected", review_path=review)
    assert report["counts"]["conflicting_images"] == 3 and report["status"] == "blocked"
    review = reviewed(source, tmp_path, changes=lambda r: [s.update(conflict_policy="ignore", conflict_rationale="fixture conflict") for s in r["samples"]])
    assert prepare(source, tmp_path / "ignored", review_path=review)["status"] == "ready"
    mask = list(iter_samples(tmp_path / "ignored", "train"))[0][2]
    assert mask[1, 1] == 255
    from graphene_dataset_contract.source import rasterize
    anns = [{"id": i, "category_id": i, "segmentation": [[1, 1, 3, 1, 3, 3, 1, 3]]} for i in (1, 2)]
    assert np.array_equal(rasterize(anns, {1: "bulk", 2: "few-layer"}, 6, 10), rasterize(anns[::-1], {1: "bulk", 2: "few-layer"}, 6, 10))


def test_background_requires_explicit_review(tmp_path):
    source = make_source(tmp_path / "background.zip", edit=lambda d: d["test"].update(annotations=[]))
    review = reviewed(source, tmp_path)
    assert prepare(source, tmp_path / "blocked", review_path=review)["status"] == "blocked"
    review = reviewed(source, tmp_path, changes=lambda r: r["samples"][0].update(completeness="verified-background"))
    assert prepare(source, tmp_path / "ready", review_path=review)["status"] == "ready"
    assert not list(iter_samples(tmp_path / "ready", "test"))[0][2].any()


def test_all_ignore_rejected(tmp_path):
    def edit(docs):
        for doc in docs.values():
            for ann in doc["annotations"]:
                ann["segmentation"] = [[0, 0, 10, 0, 10, 6, 0, 6]]
    source = make_source(tmp_path / "all-ignore.zip", edit=edit)
    review = reviewed(source, tmp_path, changes=lambda r: [s.update(conflict_policy="ignore", conflict_rationale="fixture") for s in r["samples"]])
    result = prepare(source, tmp_path / "bad", review_path=review)
    assert any("all-ignore" in b for b in result["blockers"])


def test_duplicates_and_groups_cannot_cross_roles(tmp_path):
    source = make_source(tmp_path / "duplicates.zip", duplicate=True)
    review = reviewed(source, tmp_path)
    result = prepare(source, tmp_path / "bad", review_path=review)
    assert any("rgb_sha256 spans" in b for b in result["blockers"])
    source = make_source(tmp_path / "groups.zip")
    review = reviewed(source, tmp_path, changes=lambda r: [s.update(group="shared") for s in r["samples"]])
    assert any("group spans" in b for b in prepare(source, tmp_path / "bad-group", review_path=review)["blockers"])


def test_candidate_disposition_and_explicit_exclusion(source, tmp_path):
    groups = tmp_path / "groups.json"
    groups.write_text(json.dumps({"schema_version": 1, "source_sha256": digest(source.read_bytes()), "pairs": [{"left": "test-000", "right": "train-000", "evidence": "fixture cue"}]}))
    review = reviewed(source, tmp_path)
    result = prepare(source, tmp_path / "undecided", review_path=review, groups_path=groups)
    assert any("disposition" in b for b in result["blockers"])
    def changes(r):
        r["samples"][0].update(role="excluded", exclusion_reason="candidate uncertainty")
        r["dispositions"] = [{"left": "test-000", "right": "train-000", "decision": "excluded", "rationale": "exclude cue"}]
    review = reviewed(source, tmp_path, changes=changes)
    assert prepare(source, tmp_path / "excluded", review_path=review, groups_path=groups)["status"] == "ready"
    assert list(iter_samples(tmp_path / "excluded", "test")) == []
    assert not (tmp_path / "excluded/images/test-000.png").exists()


def test_assignment_changes_fingerprints(source, tmp_path):
    a, b = tmp_path / "a", tmp_path / "b"
    assert prepare(source, a, review_path=reviewed(source, tmp_path))["status"] == "ready"
    def changes(r):
        for s in r["samples"]:
            if s["role"] == "train": s["role"] = "validation"
            elif s["role"] == "validation": s["role"] = "train"
    assert prepare(source, b, review_path=reviewed(source, tmp_path, changes=changes))["status"] == "ready"
    assert check(a).split_fingerprint != check(b).split_fingerprint
    assert check(a).dataset_fingerprint != check(b).dataset_fingerprint
    assert [s.original_role for s in check(a).samples] == [s.original_role for s in check(b).samples]


@pytest.mark.parametrize("mutation", ["bytes", "missing", "extra", "symlink", "report", "role", "provenance", "illegal-mask"])
def test_consumer_rejects_tampering_even_with_recomputed_identity(ready, mutation):
    if mutation == "bytes": (ready / "images/train-000.png").write_bytes(b"bad")
    elif mutation == "missing": (ready / "masks/train-000.png").unlink()
    elif mutation == "extra": (ready / "masks/prediction.png").write_bytes(b"bad")
    elif mutation == "symlink": (ready / "extra").symlink_to("images", target_is_directory=True)
    elif mutation == "report": (ready / "validation.json").write_text('{}')
    elif mutation == "role": seal(ready, lambda m: m["samples"][1].update(role="test"))
    elif mutation == "provenance": seal(ready, lambda m: m["review"]["samples"][1].update(origin="prediction"))
    elif mutation == "illegal-mask":
        path = ready / "masks/train-000.png"
        Image.fromarray(np.full((6, 10), 7, dtype=np.uint8)).save(path)
        seal(ready, lambda m: m["samples"][1].update(mask_sha256=digest(path.read_bytes())))
    with pytest.raises(DatasetError):
        list(iter_samples(ready, "train"))


def test_publication_failures_preserve_prior_and_clean_staging(source, ready, tmp_path, monkeypatch):
    before = source.read_bytes()
    review = reviewed(source, tmp_path)
    existing = (ready / "manifest.json").read_bytes()
    with pytest.raises(DatasetError, match="new output"):
        prepare(source, ready, review_path=review)
    def fail(*args):
        raise OSError("injected publication failure")
    monkeypatch.setattr(artifact, "publish", fail)
    with pytest.raises(OSError):
        prepare(source, tmp_path / "failed", review_path=review)
    assert not (tmp_path / "failed").exists()
    assert not list(tmp_path.glob(".failed.staging-*"))
    assert (ready / "manifest.json").read_bytes() == existing and source.read_bytes() == before


def test_competing_publication_cannot_replace_existing_directory(tmp_path):
    stage, dest = tmp_path / "stage", tmp_path / "dest"
    stage.mkdir(); dest.mkdir()
    with pytest.raises(OSError): artifact.publish(stage, dest)
    assert stage.exists() and dest.exists()


def test_cli_exit_statuses(source, ready, tmp_path, capsys):
    assert main(["check", str(ready)]) == 0
    assert main(["prepare", str(source), "--output", str(tmp_path / "blocked")]) == 2
    assert main(["check", str(tmp_path / "blocked")]) == 3
    assert '"status": "blocked"' in capsys.readouterr().out


def test_archive_boundaries(source, tmp_path, monkeypatch):
    import graphene_dataset_contract.source as adapter
    monkeypatch.setattr(adapter, "MAX_MEMBERS", 1)
    assert prepare(source, tmp_path / "limit")["status"] == "invalid"
    monkeypatch.setattr(adapter, "MAX_MEMBERS", 2000)
    with zipfile.ZipFile(source, "a") as archive:
        archive.writestr("unaccounted.png", b"png")
    assert "Unaccounted" in prepare(source, tmp_path / "extra")["blockers"][0]


@pytest.mark.parametrize("unsupported", [99, True, 1.0])
def test_unknown_schema_and_duplicate_json_rejected(source, tmp_path, ready, unsupported):
    review = reviewed(source, tmp_path)
    review.write_text('{"schema_version":1,"schema_version":1}')
    assert prepare(source, tmp_path / "duplicate-json", review_path=review)["status"] == "invalid"
    doc = read_json(ready / "manifest.json"); doc["schema_version"] = unsupported
    write_json(ready / "manifest.json", doc)
    with pytest.raises(DatasetError): check(ready)


def test_decoded_duplicates_different_png_bytes_still_block(tmp_path):
    from PIL.PngImagePlugin import PngInfo
    source = make_source(tmp_path / "dupes.zip", duplicate=True)
    with zipfile.ZipFile(source) as z:
        members = {n: z.read(n) for n in z.namelist()}
    buf = io.BytesIO(); metadata = PngInfo(); metadata.add_text("note", "different encoding")
    with Image.open(io.BytesIO(members["test/original.png"])) as image:
        image.save(buf, format="PNG", pnginfo=metadata)
    members["test/original.png"] = buf.getvalue()
    with zipfile.ZipFile(source, "w") as z:
        for name, data in members.items(): z.writestr(name, data)
    review = reviewed(source, tmp_path)
    assert any("rgb_sha256 spans" in b for b in prepare(source, tmp_path / "blocked", review_path=review)["blockers"])


def test_same_role_duplicate_different_labels_block(tmp_path):
    source = make_source(tmp_path / "dupes.zip", duplicate=True,
                         edit=lambda d: d["test"]["annotations"][0].update(segmentation=[[1, 1, 4, 1, 4, 3, 1, 3]]))
    def changes(r):
        r["samples"][0].update(role="train")
    review = reviewed(source, tmp_path, changes=changes)
    assert any("conflicting annotations" in b for b in prepare(source, tmp_path / "blocked", review_path=review)["blockers"])


@pytest.mark.parametrize("mode", ["write", "interrupt"])
def test_owned_staging_cleanup_at_write_and_interrupt(source, tmp_path, monkeypatch, mode):
    review = reviewed(source, tmp_path)
    original = Image.Image.save
    def failure(*args, **kwargs):
        if mode == "interrupt": raise KeyboardInterrupt()
        raise OSError("injected write failure")
    monkeypatch.setattr(Image.Image, "save", failure)
    with pytest.raises(KeyboardInterrupt if mode == "interrupt" else OSError):
        prepare(source, tmp_path / "failed", review_path=review)
    assert not (tmp_path / "failed").exists() and not list(tmp_path.glob(".failed.staging-*"))
    monkeypatch.setattr(Image.Image, "save", original)


@pytest.mark.parametrize("name,special", [("../outside.txt", False), ("link", True), ("train/original.png", False)])
def test_unsafe_special_duplicate_archive_members(source, tmp_path, name, special):
    with zipfile.ZipFile(source, "a") as z:
        info = zipfile.ZipInfo(name)
        if special: info.external_attr = 0o120777 << 16
        z.writestr(info, "outside")
    assert prepare(source, tmp_path / "bad")["status"] == "invalid"


def test_rotated_metadata_requires_geometry_review(tmp_path):
    exif = Image.Exif(); exif[274] = 6
    source = make_source(tmp_path / "rotated.zip", image_options={"exif": exif})
    assert "geometry" in prepare(source, tmp_path / "bad")["blockers"][0]


def test_known_audit_evidence_cannot_be_omitted():
    from graphene_dataset_contract.review import KNOWN_SOURCE, group_evidence
    groups = group_evidence(KNOWN_SOURCE, {"schema_version": 1, "source_sha256": KNOWN_SOURCE, "pairs": []})
    assert len(groups.pairs) == 15
    assert ("test-000", "train-007") in {(p.left, p.right) for p in groups.pairs}
    assert ("test-001", "valid-002") in {(p.left, p.right) for p in groups.pairs}


def test_schemas_match_runtime_definitions():
    from importlib.resources import files
    from graphene_dataset_contract.schema import Groups, Review
    for name, cls in (("manifest-v1", Manifest), ("review-v1", Review), ("groups-v1", Groups)):
        assert json.loads(files("graphene_dataset_contract").joinpath(f"schemas/{name}.schema.json").read_text()) == cls.model_json_schema()


def test_mask_dimensions_and_palette_rejected(ready):
    path = ready / "masks/train-000.png"
    Image.fromarray(np.zeros((10, 6), dtype=np.uint8)).save(path)
    seal(ready, lambda m: m["samples"][1].update(mask_sha256=digest(path.read_bytes())))
    with pytest.raises(DatasetError, match="geometry"): check(ready)
    Image.fromarray(np.zeros((6, 10), dtype=np.uint8)).convert("P").save(path)
    seal(ready, lambda m: m["samples"][1].update(mask_sha256=digest(path.read_bytes())))
    with pytest.raises(DatasetError, match="grayscale"): check(ready)


def test_label_and_review_changes_alter_dataset_identity(source, tmp_path):
    review = reviewed(source, tmp_path)
    assert prepare(source, tmp_path / "a", review_path=review)["status"] == "ready"
    document = read_json(review); document["reference"] = "second synthetic review"
    write_json(review, document)
    assert prepare(source, tmp_path / "b", review_path=review)["status"] == "ready"
    assert check(tmp_path / "a").dataset_fingerprint != check(tmp_path / "b").dataset_fingerprint
    assert check(tmp_path / "a").split_fingerprint == check(tmp_path / "b").split_fingerprint
    changed = make_source(tmp_path / "changed.zip", edit=lambda d: d["train"]["annotations"][0].update(segmentation=[[1, 1, 4, 1, 4, 3, 1, 3]]))
    assert prepare(changed, tmp_path / "c", review_path=reviewed(changed, tmp_path))["status"] == "ready"
    assert check(tmp_path / "a").dataset_fingerprint != check(tmp_path / "c").dataset_fingerprint


def test_artifact_and_conversion_resource_limits(source, ready, tmp_path, monkeypatch):
    import graphene_dataset_contract.source as adapter
    monkeypatch.setattr(adapter, "MAX_ARTIFACT_BYTES", 1)
    assert prepare(source, tmp_path / "conversion-limit")["status"] == "invalid"
    monkeypatch.setattr(artifact, "MAX_ARTIFACT_BYTES", 1)
    with pytest.raises(DatasetError, match="budget"): check(ready)
