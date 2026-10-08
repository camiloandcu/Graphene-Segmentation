"""Read-only, bounded COCO-polygon audit for WI-03; not a production importer."""

import argparse
from collections import Counter
import hashlib
import io
import json
from pathlib import Path, PurePosixPath
import platform
import stat
import zipfile

import numpy as np
from PIL import Image, ImageDraw, __version__ as pillow_version
from pycocotools import mask as coco_mask
from importlib.metadata import version

from wi03_similarity import compare_pairs, descriptors, filename_group

NAME_MAPPING = {"few-layer": 1, "bulk": 2}
COLORS = np.array([[0, 0, 0], [0, 220, 255], [255, 100, 40]], dtype=np.uint8)
MAX_EXPANDED = 100 * 1024 * 1024
MAX_PIXELS = 16_000_000


def digest(data):
    return hashlib.sha256(data).hexdigest()


def write_json(path, data):
    path.write_text(json.dumps(data, indent=2, sort_keys=True, allow_nan=False) + "\n")


def safe_name(name):
    path = PurePosixPath(name)
    if "\\" in name or path.is_absolute() or ".." in path.parts or ":" in name:
        raise ValueError(f"Unsafe archive/file path: {name}")
    return path


def validate_archive(archive):
    members = archive.infolist()
    if len(members) > 2000 or sum(m.file_size for m in members) > MAX_EXPANDED:
        raise ValueError("Export exceeds this audit's member/expanded-byte budget")
    names = [m.filename for m in members]
    if len(names) != len(set(names)):
        raise ValueError("Duplicate ZIP member names")
    for member in members:
        safe_name(member.filename)
        if stat.S_ISLNK(member.external_attr >> 16):
            raise ValueError("Symlink ZIP member")


def polygon_mask(annotation, height, width):
    polygons = annotation.get("segmentation")
    if not isinstance(polygons, list) or not polygons:
        raise ValueError("Missing polygons; RLE and box-only labels are unsupported by this audit")
    for polygon in polygons:
        if not isinstance(polygon, list) or len(polygon) < 6 or len(polygon) % 2:
            raise ValueError("Malformed polygon coordinate list")
        coords = np.asarray(polygon, dtype=np.float64).reshape(-1, 2)
        if not np.isfinite(coords).all():
            raise ValueError("Non-finite polygon coordinates")
        if (coords < 0).any() or (coords[:, 0] > width).any() or (coords[:, 1] > height).any():
            raise ValueError("Polygon coordinates outside image")
        area = abs(np.dot(coords[:, 0], np.roll(coords[:, 1], 1)) - np.dot(coords[:, 1], np.roll(coords[:, 0], 1))) / 2
        if area == 0:
            raise ValueError("Degenerate polygon")
    result = coco_mask.decode(coco_mask.merge(coco_mask.frPyObjects(polygons, height, width))).astype(bool)
    if not result.any():
        raise ValueError("Polygon rasterizes to no pixels")
    return result


def rasterize(annotations, categories, height, width):
    """Union labels by class; conflicting classes remain ignored, never last-wins."""
    planes = np.zeros((2, height, width), dtype=bool)
    issues, counts = [], Counter()
    for annotation in annotations:
        category = categories.get(annotation.get("category_id"))
        canonical = NAME_MAPPING.get(category)
        if canonical is None:
            issues.append({"annotation_id": annotation.get("id"), "reason": "Unresolved source class", "source_category": category})
            continue
        try:
            if annotation.get("iscrowd", 0) != 0:
                raise ValueError("Crowd annotation unsupported")
            plane = polygon_mask(annotation, height, width)
            planes[canonical - 1] |= plane
            counts[category] += 1
        except (ValueError, TypeError, OverflowError) as exc:
            issues.append({"annotation_id": annotation.get("id"), "reason": str(exc)})
    mask = np.zeros((height, width), dtype=np.uint8)
    mask[planes[0]] = 1
    mask[planes[1]] = 2
    conflict = planes[0] & planes[1]
    mask[conflict] = 255
    return mask, int(conflict.sum()), issues, dict(counts)


def save_visual(image, mask, audit_id, output):
    rgb = np.asarray(image)
    palette = COLORS[np.minimum(mask, 2)].copy()
    palette[mask == 255] = [255, 0, 255]
    foreground = mask != 0
    overlay = rgb.copy()
    overlay[foreground] = (0.65 * rgb[foreground] + 0.35 * palette[foreground]).astype(np.uint8)
    Image.fromarray(mask).save(output / "masks" / f"{audit_id}.png")
    Image.fromarray(overlay).save(output / "overlays" / f"{audit_id}.png")
    thumb = Image.fromarray(overlay)
    thumb.thumbnail((384, 288))
    canvas = Image.new("RGB", (384, 312), "white")
    canvas.paste(thumb, (0, 24))
    ImageDraw.Draw(canvas).text((4, 4), audit_id + " cyan=few orange=bulk magenta=conflict", fill="black")
    return canvas


def audit_image(archive, split, item, annotations, categories, output):
    audit_id = f"{split}-{item['id']:03d}"
    relative = str(PurePosixPath(split) / safe_name(item["file_name"]))
    record = {
        "audit_id": audit_id, "source_image_id": item["id"], "source_path": relative,
        "original_name": item.get("extra", {}).get("name"), "source_split": split,
        "annotation_count": len(annotations), "issues": [],
        "filename_group_candidate": filename_group(item["file_name"]),
        "acquisition_group": None, "annotation_provenance": "lab-human: stakeholder-reported; independently unverified",
        "date_captured_export_field": item.get("date_captured"),
    }
    try:
        data = archive.read(relative)
        with Image.open(io.BytesIO(data)) as source:
            if source.width * source.height > MAX_PIXELS:
                raise ValueError("Image exceeds audit pixel budget")
            image = source.convert("RGB")
        if image.size != (item["width"], item["height"]):
            raise ValueError("Decoded dimensions do not match COCO metadata")
        mask, conflict, issues, counts = rasterize(annotations, categories, image.height, image.width)
    except (KeyError, ValueError, OSError, TypeError) as exc:
        record["issues"].append({"reason": str(exc)})
        record["usable_for_pixel_audit"] = False
        return record, None, None
    record.update({
        "sha256": digest(data), "pixel_sha256": digest(image.tobytes()),
        "mask_sha256": digest(mask.tobytes()), "width": image.width, "height": image.height,
        "class_pixels": {str(label): int((mask == label).sum()) for label in (0, 1, 2, 255)},
        "conflict_pixels": conflict, "valid_annotation_counts": counts,
        "issues": issues, "usable_for_pixel_audit": not issues,
        "background_annotation_completeness": "unknown",
    })
    if not annotations:
        record["issues"].append({"reason": "No annotations; not a verified background image"})
        record["usable_for_pixel_audit"] = False
    return record, descriptors(image), save_visual(image, mask, audit_id, output)


def split_manifest(records, pairs):
    related = set()
    for pair in pairs:
        if pair["cross_split"]:
            related.update((pair["left"], pair["right"]))
    return [{
        "audit_id": record["audit_id"], "original_role": record["source_split"],
        "proposed_role": "unassigned", "group_candidate": record["filename_group_candidate"],
        "cross_split_candidate": record["audit_id"] in related,
        "reason": "Await group/label review; preserve source roles as evidence, no independent test claim",
        "class_pixels": record.get("class_pixels"),
    } for record in records]


def run(archive_path, output):
    if output.exists():
        raise ValueError("Use a new output directory to preserve previous evidence")
    with zipfile.ZipFile(archive_path) as archive:
        validate_archive(archive)
        # Finish input validation before creating any evidence directory.
        json_names = sorted(n for n in archive.namelist() if n.endswith("/_annotations.coco.json"))
        if not json_names:
            raise ValueError("No supported COCO split annotation files")
        output.mkdir(parents=True)
        for directory in ("masks", "overlays", "contact_sheets", "pair_sheets"):
            (output / directory).mkdir()
        records, features, thumbs, metadata = [], {}, {}, {}
        source_annotation_count = 0
        metadata_issues = []
        referenced_images = set()
        for name in json_names:
            split = str(PurePosixPath(name).parent)
            doc = json.loads(archive.read(name))
            source_annotation_count += len(doc["annotations"])
            categories = {category["id"]: category["name"] for category in doc["categories"]}
            metadata[split] = {"info": doc.get("info"), "licenses": doc.get("licenses"), "categories": doc["categories"], "annotation_file_sha256": digest(archive.read(name))}
            image_ids = [item["id"] for item in doc["images"]]
            if len(image_ids) != len(set(image_ids)):
                raise ValueError("Duplicate image IDs within split")
            annotation_ids = [a["id"] for a in doc["annotations"]]
            if len(annotation_ids) != len(set(annotation_ids)):
                raise ValueError("Duplicate annotation IDs within split")
            if len(categories) != len(doc["categories"]):
                raise ValueError("Duplicate source category IDs")
            for annotation in doc["annotations"]:
                if annotation.get("image_id") not in image_ids:
                    metadata_issues.append({"split": split, "annotation_id": annotation["id"], "reason": "Orphan annotation"})
            for item in sorted(doc["images"], key=lambda item: item["id"]):
                selected = [a for a in doc["annotations"] if a.get("image_id") == item["id"]]
                record, feature, thumb = audit_image(archive, split, item, selected, categories, output)
                records.append(record)
                referenced_images.add(record["source_path"])
                if feature is not None:
                    features[record["audit_id"]], thumbs[record["audit_id"]] = feature, thumb
        valid = [r for r in records if r["audit_id"] in features]
        pairs = compare_pairs(valid, features)
        for offset in range(0, len(valid), 12):
            page = Image.new("RGB", (4 * 384, 3 * 312), "white")
            for index, record in enumerate(valid[offset:offset + 12]):
                page.paste(thumbs[record["audit_id"]], ((index % 4) * 384, (index // 4) * 312))
            page.save(output / "contact_sheets" / f"page-{offset // 12 + 1:02d}.jpg")
        for index, pair in enumerate(pairs):
            page = Image.new("RGB", (768, 336), "white")
            draw = ImageDraw.Draw(page)
            draw.text((4, 4), f"pair {index:03d}: dHash={pair['dhash_distance']} cross_split={pair['cross_split']} name_group={pair['same_filename_group_candidate']}", fill="black")
            page.paste(thumbs[pair["left"]], (0, 24))
            page.paste(thumbs[pair["right"]], (384, 24))
            page.save(output / "pair_sheets" / f"pair-{index:03d}.jpg")
        actual = {n for n in archive.namelist() if n.lower().endswith((".jpg", ".jpeg", ".png"))}
        summary = {
            "archive_sha256": digest(archive_path.read_bytes()),
            "environment": {"python": platform.python_version(), "numpy": np.__version__, "pillow": pillow_version, "pycocotools": version("pycocotools")},
            "mapping_by_name": NAME_MAPPING, "rasterizer": "pycocotools polygon union; incompatible overlaps=255",
            "actual_image_files": len(actual), "referenced_images": len(records),
            "unreferenced_image_files": sorted(actual - referenced_images),
            "split_counts": dict(Counter(r["source_split"] for r in records)),
            "annotation_count": sum(r["annotation_count"] for r in records),
            "source_annotation_count": source_annotation_count,
            "dimensions": {f"{w}x{h}": count for (w, h), count in Counter((r["width"], r["height"]) for r in valid).items()},
            "split_class_pixels": {split: {str(label): sum(r.get("class_pixels", {}).get(str(label), 0) for r in records if r["source_split"] == split) for label in (0, 1, 2, 255)} for split in sorted(metadata)},
            "source_annotation_class_counts": dict(sum((Counter(r.get("valid_annotation_counts", {})) for r in records), Counter())),
            "class_pixels": {str(label): sum(r.get("class_pixels", {}).get(str(label), 0) for r in records) for label in (0, 1, 2, 255)},
            "class_image_support": {str(label): sum(r.get("class_pixels", {}).get(str(label), 0) > 0 for r in records) for label in (0, 1, 2, 255)},
            "issue_count": sum(len(r["issues"]) for r in records) + len(metadata_issues),
            "metadata_issues": metadata_issues, "decoded_images": len(valid),
            "conflict_images": sum(r.get("conflict_pixels", 0) > 0 for r in records),
            "conflict_pixels": sum(r.get("conflict_pixels", 0) for r in records),
            "exact_duplicate_pairs": sum(p["pixel_identical"] or p["byte_identical"] for p in pairs),
            "candidate_pair_count": len(pairs), "cross_split_candidate_count": sum(p["cross_split"] for p in pairs),
            "filename_group_candidates": len({r["filename_group_candidate"] for r in records if r["filename_group_candidate"]}),
            "similarity_settings": {"dhash_bits": 64, "dhash_max_distance": 12, "gray_thumbnail_shape": [48, 64], "correlation_minimum": 0.90, "filename_groups": "unconfirmed date/sample tokens; no acquisition identity asserted"},
            "visual_review_status": "pending; sheets generated for all decoded images and candidate pairs",
            "independent_evaluation": "unverified; proposed roles unassigned pending group/label review",
        }
        write_json(output / "inventory.json", records)
        write_json(output / "metadata.json", metadata)
        write_json(output / "summary.json", summary)
        write_json(output / "duplicate_candidates.json", pairs)
        write_json(output / "proposed_split.json", split_manifest(records, pairs))
        print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("archive", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    run(args.archive, args.output)
