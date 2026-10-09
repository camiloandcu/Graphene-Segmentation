"""Source-reconstructable partial supervision with reviewed background anchors."""
from __future__ import annotations

import io
import shutil
import tempfile
import zipfile
from datetime import date
from pathlib import Path

import numpy as np
from PIL import Image
from pydantic import ValidationError

from .artifact import _inventory, publish, settings
from .common import (DatasetError, MAX_PIXELS, decode, digest, identity, parse_json,
                     pixel_counts, read_bytes, read_json, safe_path, write_json)
from .partial_schema import (PartialDecision, PartialManifest, PartialReport,
                             PartialReview, PartialSample)
from .review import group_evidence, split_fingerprint, validate_review
from .schema import CLASSES, MAPPING, Sample
from .source import rasterize, scan


CATEGORIES = {1: "few-layer", 2: "bulk"}


def template(records, source_sha):
    return PartialReview(schema_version=2, source_sha256=source_sha,
                         samples=[PartialDecision(sample_id=s.sample_id, source_path=s.source_path)
                                  for s in records])


def raw(sample):
    return rasterize([p.model_dump() for p in sample.source_polygons], CATEGORIES,
                     sample.height, sample.width)


def supervised(sample, decision):
    source = raw(sample)
    mask = source.copy()
    mask[source == 0] = 255
    # Only an affirmative review of a genuinely blank image permits whole-image negatives.
    if decision.completeness == "verified-background":
        if sample.annotation_count:
            raise DatasetError(f"{sample.sample_id}: foreground contradicts blank-image review")
        mask[:] = 0
    ids = set()
    for anchor in decision.background_anchors:
        if anchor.id in ids or type(anchor.class_id) is not int:
            raise DatasetError("Duplicate anchor identity or noninteger background class")
        ids.add(anchor.id)
        date.fromisoformat(anchor.date)
        if anchor.image_sha256 != sample.source_sha256:
            raise DatasetError(f"{sample.sample_id}: stale background anchor image digest")
        plane = rasterize([{"id": 0, "category_id": 1, "segmentation": anchor.polygons}],
                          CATEGORIES, sample.height, sample.width) == 1
        if np.any(plane & (source != 0)):
            raise DatasetError(f"{sample.sample_id}: background anchor intersects source foreground/conflict")
        mask[plane] = 0
    return mask


def source_view(records):
    return [Sample.model_validate({**s.model_dump(exclude={"source_class_pixels", "source_mask_pixels_sha256", "source_polygons"}),
                                   "class_pixels": s.source_class_pixels,
                                   "mask_pixels_sha256": s.source_mask_pixels_sha256}) for s in records]


def supervision_fingerprint(records, review):
    return identity({"mode": "partial", "review": review.model_dump(),
                     "samples": [{"id": s.sample_id, "source_polygons": [p.model_dump() for p in s.source_polygons],
                                  "mask": s.mask_pixels_sha256} for s in sorted(records, key=lambda s: s.sample_id)]})


def report_for(records, source_sha, review, blockers):
    support = {r: {str(i): 0 for i in (0, 1, 2, 255)}
               for r in ("train", "validation", "test", "excluded", "unassigned")}
    decisions = {d.sample_id: d for d in review.samples}
    for sample in records:
        d = decisions.get(sample.sample_id)
        for label, count in sample.class_pixels.items():
            support[d.role if d and d.role else "unassigned"][label] += count
    return PartialReport(schema_version=2, status="blocked" if blockers else "ready",
                         source_sha256=source_sha, blockers=blockers, support=support,
                         evaluation=review.evaluation,
                         counts={"images": len(records), "annotations": sum(s.annotation_count for s in records),
                                 "source_conflict_pixels": sum(s.source_class_pixels["255"] for s in records),
                                 "unknown_pixels": sum(s.class_pixels["255"] for s in records)},
                         inventory=[s.model_dump(exclude={"role", "image_path", "mask_path", "image_sha256", "mask_sha256"})
                                    for s in sorted(records, key=lambda s: s.sample_id)])


def prepare_partial(source, output, *, review_path=None, groups_path=None):
    source, output = Path(source), Path(output)
    if output.exists() or output.is_symlink():
        raise DatasetError("Use a new output destination; existing outputs are never overwritten")
    source_bytes = read_bytes(source)
    source_sha = digest(source_bytes)
    output.parent.mkdir(parents=True, exist_ok=True)
    stage = Path(tempfile.mkdtemp(prefix=f".{output.name}.staging-", dir=output.parent))
    try:
        (stage / "images").mkdir()
        (stage / "masks").mkdir()
        scanned, provenance = scan(source_bytes, stage)
        records = []
        # scan already checked the complete bounded ZIP before retaining the source polygons.
        with zipfile.ZipFile(io.BytesIO(source_bytes)) as archive:
            docs = {r: parse_json(archive.read(f"{r}/_annotations.coco.json")) for r in ("train", "valid", "test")}
        for s in scanned:
            doc = docs[s.original_role]
            categories = {c["id"]: c["name"] for c in doc["categories"]}
            polygons = [{"id": a["id"], "category_id": MAPPING[categories[a["category_id"]]],
                         "segmentation": a["segmentation"]}
                        for a in doc["annotations"] if a["image_id"] == s.source_image_id]
            records.append(PartialSample(**s.model_dump(), source_class_pixels=s.class_pixels,
                                         source_mask_pixels_sha256=s.mask_pixels_sha256, source_polygons=polygons))
        review = PartialReview.model_validate(read_json(review_path)) if review_path else template(records, source_sha)
        groups = group_evidence(source_sha, read_json(groups_path) if groups_path else None)
        blockers = validate_review(review, source_view(records), groups, partial=True)
        decisions = {d.sample_id: d for d in review.samples}
        for sample in records:
            d = decisions.get(sample.sample_id)
            mask = supervised(sample, d or PartialDecision(sample_id=sample.sample_id, source_path=sample.source_path))
            sample.class_pixels, sample.mask_pixels_sha256 = pixel_counts(mask), digest(mask.tobytes())
            if d and d.role not in (None, "excluded") and not (mask != 255).any():
                blockers.append(f"{sample.sample_id}: all-unknown supervision is ineligible")
            Image.fromarray(mask).save(stage / sample.mask_path)
            sample.mask_sha256 = digest(read_bytes(stage / sample.mask_path))
        report = report_for(records, source_sha, review, sorted(set(blockers)))
        if blockers:
            shutil.rmtree(stage / "images")
            shutil.rmtree(stage / "masks")
            write_json(stage / "review-template.json", template(records, source_sha).model_dump())
            write_json(stage / "source.json", provenance.model_dump())
            write_json(stage / "group-evidence.json", groups.model_dump())
        else:
            review.samples.sort(key=lambda d: d.sample_id)
            review.dispositions.sort(key=lambda d: (d.left, d.right))
            for sample in records:
                sample.role = decisions[sample.sample_id].role
                if sample.role == "excluded":
                    (stage / sample.image_path).unlink()
                    (stage / sample.mask_path).unlink()
                    sample.image_path = sample.mask_path = sample.image_sha256 = sample.mask_sha256 = None
            manifest = PartialManifest(schema_version=2, converter_version="2.0.0", classes=CLASSES,
                                       ignore_value=255, source=provenance, settings=settings(), review=review,
                                       samples=sorted(records, key=lambda s: s.sample_id), group_evidence=groups,
                                       split_fingerprint=split_fingerprint(records, review),
                                       supervision_fingerprint=supervision_fingerprint(records, review),
                                       dataset_fingerprint="0" * 64)
            manifest.dataset_fingerprint = identity(manifest.model_dump(exclude={"dataset_fingerprint"}))
            write_json(stage / "manifest.json", manifest.model_dump())
        write_json(stage / "validation.json", report.model_dump())
        if not blockers:
            check_partial(stage)
        publish(stage, output)
        return report.model_dump()
    except (DatasetError, ValidationError, TypeError, ValueError, OverflowError) as exc:
        shutil.rmtree(stage)
        stage = Path(tempfile.mkdtemp(prefix=f".{output.name}.staging-", dir=output.parent))
        report = PartialReport(schema_version=2, status="invalid", source_sha256=source_sha,
                               blockers=[str(exc)], counts={}, support={}, evaluation=None, inventory=[])
        write_json(stage / "validation.json", report.model_dump())
        publish(stage, output)
        return report.model_dump()
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def check_partial(directory):
    directory = Path(directory)
    paths = _inventory(directory)
    try:
        m = PartialManifest.model_validate(read_json(paths["manifest.json"]))
        report = PartialReport.model_validate(read_json(paths["validation.json"]))
        if [c.model_dump() for c in m.classes] != CLASSES or m.settings.get("max_image_pixels") != MAX_PIXELS:
            raise DatasetError("Unsupported classes/resource settings")
        if m.source.sha256 != m.review.source_sha256 or m.group_evidence.source_sha256 != m.source.sha256:
            raise DatasetError("Source/review/group digest mismatch")
        known = group_evidence(m.source.sha256)
        actual_pairs = {tuple(sorted((p.left, p.right))) for p in m.group_evidence.pairs}
        if any(tuple(sorted((p.left, p.right))) not in actual_pairs for p in known.pairs):
            raise DatasetError("Known grouping evidence missing")
        if not m.samples or len({s.sample_id for s in m.samples}) != len(m.samples):
            raise DatasetError("Missing/duplicate sample identities")
        blockers = validate_review(m.review, source_view(m.samples), m.group_evidence, partial=True)
        if blockers:
            raise DatasetError("Review not ready: " + "; ".join(blockers))
        if m.split_fingerprint != split_fingerprint(m.samples, m.review):
            raise DatasetError("Split fingerprint mismatch")
        if m.supervision_fingerprint != supervision_fingerprint(m.samples, m.review):
            raise DatasetError("Supervision fingerprint mismatch")
        if m.dataset_fingerprint != identity(m.model_dump(exclude={"dataset_fingerprint"})):
            raise DatasetError("Dataset fingerprint mismatch")
        if report.model_dump() != report_for(m.samples, m.source.sha256, m.review, []).model_dump():
            raise DatasetError("Validation report differs from manifest")
        decisions = {d.sample_id: d for d in m.review.samples}
        expected = {"manifest.json", "validation.json"}
        for s in m.samples:
            safe_path(s.source_path)
            if s.sample_id != f"{s.original_role}-{s.source_image_id:03d}" or not s.source_path.startswith(s.original_role + "/"):
                raise DatasetError("Sample identity/source path mismatch")
            if s.width * s.height > MAX_PIXELS or s.role != decisions[s.sample_id].role:
                raise DatasetError("Geometry/role mismatch")
            if len(s.source_polygons) != s.annotation_count or len({p.id for p in s.source_polygons}) != s.annotation_count:
                raise DatasetError("Source annotation identity/count mismatch")
            original = raw(s)
            if pixel_counts(original) != s.source_class_pixels or digest(original.tobytes()) != s.source_mask_pixels_sha256:
                raise DatasetError("Source polygon/support mismatch")
            target = supervised(s, decisions[s.sample_id])
            if pixel_counts(target) != s.class_pixels or digest(target.tobytes()) != s.mask_pixels_sha256:
                raise DatasetError("Supervision differs from reviewed source polygons/anchors")
            if s.role == "excluded":
                if any((s.image_path, s.mask_path, s.image_sha256, s.mask_sha256)):
                    raise DatasetError("Excluded sample retains artifacts")
                continue
            if not (target != 255).any():
                raise DatasetError("Active sample has no supervised pixels")
            if s.image_path != f"images/{s.sample_id}{Path(s.source_path).suffix.lower()}" or s.mask_path != f"masks/{s.sample_id}.png":
                raise DatasetError("Noncanonical artifact paths")
            for name in (s.image_path, s.mask_path):
                safe_path(name)
                if name not in paths or name in expected:
                    raise DatasetError("Missing/multiply referenced artifact")
                expected.add(name)
            image_bytes, mask_bytes = read_bytes(paths[s.image_path]), read_bytes(paths[s.mask_path])
            rgb, mask = decode(image_bytes), decode(mask_bytes, mask=True)
            if digest(image_bytes) != s.image_sha256 or s.image_sha256 != s.source_sha256 or digest(mask_bytes) != s.mask_sha256:
                raise DatasetError("Artifact digest mismatch")
            if rgb.shape[:2] != (s.height, s.width) or mask.shape != target.shape:
                raise DatasetError("Artifact geometry mismatch")
            if digest(rgb.tobytes()) != s.rgb_sha256 or not np.array_equal(mask, target):
                raise DatasetError("Artifact pixels differ from source/review supervision")
        if set(paths) != expected:
            raise DatasetError("Unreferenced files in partial dataset")
        return m
    except (ValidationError, KeyError, TypeError, ValueError) as exc:
        raise DatasetError(f"Invalid partial artifact: {exc}") from exc
