"""Atomic preparation and strict downstream validation of dataset directories."""
from __future__ import annotations

import ctypes
import os
import platform
import shutil
import tempfile
from importlib.metadata import version
from pathlib import Path

from pydantic import ValidationError

from .common import (DatasetError, MAX_ARTIFACT_BYTES, MAX_BYTES, MAX_MEMBERS,
                     MAX_PIXELS, decode, digest, identity, pixel_counts, read_bytes,
                     read_json, safe_path, write_json)
from .review import group_evidence, split_fingerprint, template, validate_review
from .schema import CLASSES, Groups, Manifest, Report, Review
from .source import scan


def settings():
    return {"max_source_bytes": MAX_BYTES, "max_image_pixels": MAX_PIXELS,
            "max_source_members": MAX_MEMBERS, "rasterization": "pycocotools-union-conflict-ignore",
            "environment": {name: version(name) for name in ("numpy", "Pillow", "pycocotools")}}


def report_for(records, source_sha256, review, blockers):
    decisions = {d.sample_id: d for d in review.samples} if review else {}
    support = {r: {str(i): 0 for i in (0, 1, 2, 255)} for r in ("train", "validation", "test", "excluded", "unassigned")}
    for sample in records:
        decision = decisions.get(sample.sample_id)
        role = decision.role if decision and decision.role else "unassigned"
        for label, count in sample.class_pixels.items():
            support[role][label] += count
    return Report(schema_version=1, status="blocked" if blockers else "ready",
                  source_sha256=source_sha256, blockers=blockers,
                  counts={"images": len(records), "annotations": sum(s.annotation_count for s in records),
                          "conflicting_images": sum(s.class_pixels["255"] > 0 for s in records),
                          "conflict_pixels": sum(s.class_pixels["255"] for s in records)},
                  support=support, evaluation=review.evaluation if review else None,
                  inventory=[s.model_dump(exclude={"role", "image_path", "mask_path", "image_sha256", "mask_sha256"})
                             for s in sorted(records, key=lambda s: s.sample_id)])


def publish(stage: Path, destination: Path):
    """Atomic no-replace rename, including the competing-publisher boundary."""
    if platform.system() == "Linux":
        libc = ctypes.CDLL(None, use_errno=True)
        rename = libc.renameat2
        rename.argtypes = [ctypes.c_int, ctypes.c_char_p, ctypes.c_int, ctypes.c_char_p, ctypes.c_uint]
        rename.restype = ctypes.c_int
        if rename(-100, os.fsencode(stage), -100, os.fsencode(destination), 1) != 0:
            code = ctypes.get_errno()
            raise OSError(code, os.strerror(code), str(destination))
    elif os.name == "nt":
        os.rename(stage, destination)  # Windows refuses an existing destination.
    else:
        raise DatasetError("Atomic no-overwrite publication requires Linux or Windows")


def prepare(source: Path, output: Path, *, review_path: Path | None = None,
            groups_path: Path | None = None) -> dict:
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
        records, provenance = scan(source_bytes, stage)
        groups = group_evidence(source_sha, read_json(groups_path) if groups_path else None)
        review = Review.model_validate(read_json(review_path)) if review_path else template(records, source_sha)
        # Source/evidence is the anchor, not a user-edited review digest.
        blockers = validate_review(review, records, groups)
        report = report_for(records, source_sha, review, blockers)
        if blockers:
            shutil.rmtree(stage / "images")
            shutil.rmtree(stage / "masks")
            write_json(stage / "validation.json", report.model_dump())
            write_json(stage / "review-template.json", template(records, source_sha).model_dump())
            write_json(stage / "group-evidence.json", groups.model_dump())
            write_json(stage / "source.json", provenance.model_dump())
        else:
            decisions = {d.sample_id: d for d in review.samples}
            for sample in records:
                sample.role = decisions[sample.sample_id].role
                if sample.role == "excluded":
                    (stage / sample.image_path).unlink()
                    (stage / sample.mask_path).unlink()
                    sample.image_path = sample.mask_path = None
                    sample.image_sha256 = sample.mask_sha256 = None
            review.samples.sort(key=lambda d: d.sample_id)
            review.dispositions.sort(key=lambda d: (d.left, d.right))
            manifest = Manifest(schema_version=1, converter_version="1.0.0", classes=CLASSES,
                                ignore_value=255, source=provenance, settings=settings(), review=review,
                                group_evidence=groups, samples=sorted(records, key=lambda s: s.sample_id),
                                split_fingerprint=split_fingerprint(records, review), dataset_fingerprint="0" * 64)
            manifest.dataset_fingerprint = identity(manifest.model_dump(exclude={"dataset_fingerprint"}))
            write_json(stage / "manifest.json", manifest.model_dump())
            write_json(stage / "validation.json", report.model_dump())
            check(stage)
        publish(stage, output)
        return report.model_dump()
    except (DatasetError, ValidationError, TypeError, ValueError, OverflowError) as exc:
        # Invalid input gets diagnostics only. I/O errors and interruption propagate
        # after owned staging cleanup; they are not mislabeled as source defects.
        shutil.rmtree(stage)
        stage = Path(tempfile.mkdtemp(prefix=f".{output.name}.staging-", dir=output.parent))
        report = Report(schema_version=1, status="invalid", source_sha256=source_sha,
                        blockers=[str(exc)], counts={}, support={}, evaluation=None, inventory=[])
        write_json(stage / "validation.json", report.model_dump())
        publish(stage, output)
        return report.model_dump()
    finally:
        if stage.exists():
            shutil.rmtree(stage)


def _inventory(directory: Path):
    if directory.is_symlink() or not directory.is_dir():
        raise DatasetError("Dataset must be a regular directory")
    paths, total = {}, 0
    for entry in directory.iterdir():
        if entry.is_symlink():
            raise DatasetError("Symlinks are forbidden in dataset")
        if entry.is_dir():
            if entry.name not in ("images", "masks"):
                raise DatasetError(f"Unexpected artifact directory: {entry.name}")
            children = entry.iterdir()
        else:
            children = [entry]
        for path in children:
            if path.is_symlink() or not path.is_file():
                raise DatasetError("Only regular artifact files are supported")
            relative = path.relative_to(directory).as_posix()
            safe_path(relative)
            total += path.stat().st_size
            paths[relative] = path
            if total > MAX_ARTIFACT_BYTES or len(paths) > MAX_MEMBERS:
                raise DatasetError("Artifact exceeds byte/member budget")
    return paths


def check(directory: Path) -> Manifest:
    directory = Path(directory)
    try:
        paths = _inventory(directory)
        if "manifest.json" not in paths:
            raise DatasetError("No ready manifest; diagnostic/staging directories are not datasets")
        manifest = Manifest.model_validate(read_json(paths["manifest.json"]))
        report = Report.model_validate(read_json(paths["validation.json"]))
        records, review, groups = manifest.samples, manifest.review, manifest.group_evidence
        if [c.model_dump() for c in manifest.classes] != CLASSES:
            raise DatasetError("Canonical classes differ from the model contract")
        if manifest.settings.get("max_image_pixels") != MAX_PIXELS or manifest.settings.get("max_source_bytes") != MAX_BYTES:
            raise DatasetError("Unsupported preparation resource settings")
        if manifest.source.sha256 != review.source_sha256 or groups.source_sha256 != review.source_sha256:
            raise DatasetError("Review/source/group digest mismatch")
        known = group_evidence(manifest.source.sha256)
        actual_pairs = {tuple(sorted((p.left, p.right))) for p in groups.pairs}
        if any(tuple(sorted((p.left, p.right))) not in actual_pairs for p in known.pairs):
            raise DatasetError("Known source grouping evidence is missing")
        if not records or len({s.sample_id for s in records}) != len(records):
            raise DatasetError("Missing/duplicate manifest sample identities")
        blockers = validate_review(review, records, groups)
        if blockers:
            raise DatasetError("Review not ready: " + "; ".join(blockers))
        if manifest.split_fingerprint != split_fingerprint(records, review):
            raise DatasetError("Split fingerprint mismatch")
        if manifest.dataset_fingerprint != identity(manifest.model_dump(exclude={"dataset_fingerprint"})):
            raise DatasetError("Dataset fingerprint mismatch")
        if report.model_dump() != report_for(records, manifest.source.sha256, review, []).model_dump():
            raise DatasetError("Validation report differs from manifest")
        decisions = {d.sample_id: d for d in review.samples}
        expected = {"manifest.json", "validation.json"}
        actual_total = 0
        for sample in records:
            if sample.sample_id != f"{sample.original_role}-{sample.source_image_id:03d}":
                raise DatasetError("Sample identity differs from source identity")
            safe_path(sample.source_path)
            if not sample.source_path.startswith(sample.original_role + "/"):
                raise DatasetError("Source path/role mismatch")
            if sample.role != decisions[sample.sample_id].role:
                raise DatasetError("Effective role differs from review")
            if sample.width * sample.height > MAX_PIXELS:
                raise DatasetError("Manifest sample exceeds pixel limit")
            if set(sample.class_pixels) != {"0", "1", "2", "255"} or sum(sample.class_pixels.values()) != sample.width * sample.height:
                raise DatasetError("Invalid class support/geometry")
            if sample.role == "excluded":
                if any((sample.image_path, sample.mask_path, sample.image_sha256, sample.mask_sha256)):
                    raise DatasetError("Excluded sample retains active artifacts")
                continue
            for name in (sample.image_path, sample.mask_path):
                safe_path(name)
                if name in expected or name not in paths:
                    raise DatasetError("Missing or multiply referenced artifact")
                expected.add(name)
            if sample.image_path != f"images/{sample.sample_id}{Path(sample.source_path).suffix.lower()}" or sample.mask_path != f"masks/{sample.sample_id}.png":
                raise DatasetError("Noncanonical artifact path")
            image_bytes, mask_bytes = read_bytes(paths[sample.image_path]), read_bytes(paths[sample.mask_path])
            actual_total += len(image_bytes) + len(mask_bytes)
            if actual_total > MAX_ARTIFACT_BYTES:
                raise DatasetError("Artifact exceeds actual byte budget")
            if digest(image_bytes) != sample.image_sha256 or sample.image_sha256 != sample.source_sha256 or digest(mask_bytes) != sample.mask_sha256:
                raise DatasetError(f"{sample.sample_id}: artifact digest mismatch")
            rgb, mask = decode(image_bytes), decode(mask_bytes, mask=True)
            if rgb.shape[:2] != (sample.height, sample.width) or mask.shape != rgb.shape[:2]:
                raise DatasetError(f"{sample.sample_id}: mask/image geometry mismatch")
            if digest(rgb.tobytes()) != sample.rgb_sha256 or digest(mask.tobytes()) != sample.mask_pixels_sha256:
                raise DatasetError(f"{sample.sample_id}: decoded pixel digest mismatch")
            if pixel_counts(mask) != sample.class_pixels:
                raise DatasetError(f"{sample.sample_id}: mask class support mismatch")
        if set(paths) != expected:
            raise DatasetError("Unreferenced files in dataset; predictions cannot be included by directory copying")
        return manifest
    except (ValidationError, KeyError, TypeError) as exc:
        raise DatasetError(f"Invalid artifact schema/inventory: {exc}") from exc


def iter_samples(directory: Path, role: str):
    """Validate the entire artifact before returning any requested-role samples."""
    if role not in ("train", "validation", "test"):
        raise DatasetError("Consumer role must be train, validation or test")
    directory = Path(directory)
    manifest = check(directory)
    for sample in manifest.samples:
        if sample.role == role:
            # Recheck bytes at use time to catch mutation after initial validation.
            image_bytes, mask_bytes = read_bytes(directory / sample.image_path), read_bytes(directory / sample.mask_path)
            if digest(image_bytes) != sample.image_sha256 or digest(mask_bytes) != sample.mask_sha256:
                raise DatasetError("Artifact changed after validation")
            yield sample, decode(image_bytes), decode(mask_bytes, mask=True)
