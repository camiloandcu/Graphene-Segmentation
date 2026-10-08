"""Bounded read-only adapter for the audited split-directory COCO polygon ZIP."""
from __future__ import annotations

import io
import stat
import zipfile
from pathlib import Path

import numpy as np
from PIL import Image
from pycocotools import mask as coco_mask

from .common import (DatasetError, MAX_ARTIFACT_BYTES, MAX_BYTES, MAX_MEMBERS, MAX_PIXELS, decode,
                     digest, parse_json, pixel_counts, safe_path)
from .schema import MAPPING, Sample, Source

IMAGE_SUFFIXES = {".jpg", ".jpeg", ".png", ".bmp", ".tif", ".tiff", ".webp"}


def integer(value, name, *, positive=False):
    if type(value) is not int or value < int(positive):
        raise DatasetError(f"Invalid {name}: expected {'positive' if positive else 'nonnegative'} integer")
    return value


def indexed(items, label):
    if not isinstance(items, list):
        raise DatasetError(f"{label} must be a list")
    result = {}
    for item in items:
        if not isinstance(item, dict):
            raise DatasetError(f"Invalid {label} record")
        key = integer(item.get("id"), f"{label} ID")
        if key in result:
            raise DatasetError(f"Duplicate {label} ID {key}")
        result[key] = item
    return result


def rasterize(annotations, categories, height, width):
    planes = np.zeros((2, height, width), dtype=bool)
    for ann in annotations:
        label = f"annotation {ann['id']}"
        category = categories.get(integer(ann.get("category_id"), f"{label} category"))
        if category not in MAPPING:
            raise DatasetError(f"{label}: unresolved source class {category!r}")
        if type(ann.get("iscrowd", 0)) is not int or ann.get("iscrowd", 0) != 0:
            raise DatasetError(f"{label}: crowd annotations unsupported")
        polygons = ann.get("segmentation")
        if not isinstance(polygons, list) or not polygons:
            raise DatasetError(f"{label}: polygons required; RLE/box-only unsupported")
        for polygon in polygons:
            if not isinstance(polygon, list) or len(polygon) < 6 or len(polygon) % 2:
                raise DatasetError(f"{label}: malformed polygon")
            if any(type(v) not in (int, float) for v in polygon):
                raise DatasetError(f"{label}: coordinates must be numeric")
            coords = np.asarray(polygon, dtype=np.float64).reshape(-1, 2)
            if not np.isfinite(coords).all():
                raise DatasetError(f"{label}: non-finite coordinates")
            if (coords < 0).any() or (coords[:, 0] > width).any() or (coords[:, 1] > height).any():
                raise DatasetError(f"{label}: coordinates outside image")
            area = abs(np.dot(coords[:, 0], np.roll(coords[:, 1], 1)) -
                       np.dot(coords[:, 1], np.roll(coords[:, 0], 1))) / 2
            if area == 0:
                raise DatasetError(f"{label}: degenerate polygon")
        try:
            plane = coco_mask.decode(coco_mask.merge(
                coco_mask.frPyObjects(polygons, height, width))).astype(bool)
        except (TypeError, ValueError, OverflowError) as exc:
            raise DatasetError(f"{label}: polygon rasterization failed") from exc
        if not plane.any():
            raise DatasetError(f"{label}: polygon rasterizes to no pixels")
        planes[MAPPING[category] - 1] |= plane
    mask = np.zeros((height, width), dtype=np.uint8)
    mask[planes[0]] = 1
    mask[planes[1]] = 2
    mask[planes[0] & planes[1]] = 255
    return mask


def scan(source_bytes: bytes, stage: Path):
    records, annotation_files, metadata = [], {}, {}
    consumed, total, written = set(), 0, 0
    try:
        archive = zipfile.ZipFile(io.BytesIO(source_bytes))
    except zipfile.BadZipFile as exc:
        raise DatasetError("Invalid source ZIP") from exc
    with archive:
        members = archive.infolist()
        names = [m.filename for m in members]
        if len(members) > MAX_MEMBERS or sum(m.file_size for m in members) > MAX_BYTES:
            raise DatasetError("Source ZIP exceeds member/expanded-byte limit")
        if len(set(names)) != len(names):
            raise DatasetError("Duplicate ZIP member names")
        for m in members:
            safe_path(m.filename.rstrip("/") if m.is_dir() else m.filename)
            mode = stat.S_IFMT(m.external_attr >> 16)
            if mode not in (0, stat.S_IFREG, stat.S_IFDIR) or (mode == stat.S_IFDIR and not m.is_dir()):
                raise DatasetError(f"Unsupported special ZIP member: {m.filename}")
            if m.flag_bits & 1:
                raise DatasetError("Encrypted ZIP members unsupported")

        def read(name):
            nonlocal total
            if name in consumed:
                raise DatasetError(f"Repeated source reference: {name}")
            try:
                with archive.open(name) as stream:
                    data = stream.read(MAX_BYTES - total + 1)
            except (KeyError, OSError, RuntimeError, zipfile.BadZipFile) as exc:
                raise DatasetError(f"Cannot read source member: {name}") from exc
            total += len(data)
            if total > MAX_BYTES:
                raise DatasetError("Source ZIP exceeds actual read budget")
            consumed.add(name)
            return data

        json_names = sorted(n for n in names if n.endswith("/_annotations.coco.json"))
        if not json_names:
            raise DatasetError("No supported split annotation files")
        for name in json_names:
            split = name.split("/")[0]
            if name != f"{split}/_annotations.coco.json" or split not in ("train", "valid", "test"):
                raise DatasetError(f"Unsupported split layout: {name}")
            raw = read(name)
            doc = parse_json(raw)
            if not isinstance(doc, dict):
                raise DatasetError(f"Invalid COCO document: {name}")
            images = indexed(doc.get("images"), f"{split} image")
            annotations = indexed(doc.get("annotations"), f"{split} annotation")
            cats = indexed(doc.get("categories"), f"{split} category")
            categories = {i: c.get("name") for i, c in cats.items()}
            if any(not isinstance(v, str) or not v for v in categories.values()):
                raise DatasetError(f"Invalid category names: {name}")
            if len(set(categories.values())) != len(categories):
                raise DatasetError(f"Duplicate category names: {name}")
            annotation_files[name] = digest(raw)
            metadata[split] = {k: doc.get(k) for k in ("info", "licenses", "categories")}
            by_image = {i: [] for i in images}
            for ann in annotations.values():
                image_id = integer(ann.get("image_id"), "annotation image ID")
                if image_id not in images:
                    raise DatasetError(f"Orphan annotation {ann['id']} in {split}")
                by_image[image_id].append(ann)
            for image_id, item in sorted(images.items()):
                sid = f"{split}-{image_id:03d}"
                path = f"{split}/{safe_path(item.get('file_name'))}"
                suffix = Path(path).suffix.lower()
                if suffix not in IMAGE_SUFFIXES:
                    raise DatasetError(f"Unsupported image extension: {path}")
                width = integer(item.get("width"), f"{sid} width", positive=True)
                height = integer(item.get("height"), f"{sid} height", positive=True)
                if width * height > MAX_PIXELS:
                    raise DatasetError(f"{sid}: image exceeds pixel limit")
                data = read(path)
                rgb = decode(data)
                if rgb.shape[:2] != (height, width):
                    raise DatasetError(f"{sid}: source/image geometry mismatch")
                mask = rasterize(by_image[image_id], categories, height, width)
                image_path, mask_path = f"images/{sid}{suffix}", f"masks/{sid}.png"
                (stage / image_path).write_bytes(data)
                Image.fromarray(mask).save(stage / mask_path)
                mask_bytes = (stage / mask_path).read_bytes()
                written += len(data) + len(mask_bytes)
                if written > MAX_ARTIFACT_BYTES or len(records) * 2 + 4 > MAX_MEMBERS:
                    raise DatasetError("Converted artifacts exceed byte/member budget")
                records.append(Sample(
                    sample_id=sid, source_image_id=image_id, source_path=path,
                    original_role=split, role="excluded", annotation_count=len(by_image[image_id]),
                    width=width, height=height, source_sha256=digest(data),
                    rgb_sha256=digest(rgb.tobytes()), class_pixels=pixel_counts(mask),
                    mask_pixels_sha256=digest(mask.tobytes()), image_path=image_path,
                    mask_path=mask_path, image_sha256=digest(data), mask_sha256=digest(mask_bytes)))
        for name in names:
            if name in consumed or name.endswith("/"):
                continue
            if Path(name).suffix.lower() in IMAGE_SUFFIXES or Path(name).suffix.lower() not in (".txt", ".md"):
                raise DatasetError(f"Unaccounted source file: {name}")
            # README/license text is retained verbatim, not promoted to acquisition truth.
            metadata[name] = read(name).decode("utf-8", errors="replace")
    if not records:
        raise DatasetError("No source images")
    return records, Source(sha256=digest(source_bytes), metadata=metadata,
                          annotation_files=annotation_files,
                          unknowns=["Physical label correctness is not software-verified",
                                    "Acquisition identity is unknown unless documented in review",
                                    "Individual annotation history is unknown unless documented in review"])
