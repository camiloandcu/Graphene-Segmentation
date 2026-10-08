"""Candidate retrieval only: visual similarity does not prove acquisition identity."""

import hashlib
import itertools
import re

import numpy as np
from PIL import Image


def descriptors(image):
    gray = image.convert("L")
    small = np.asarray(gray.resize((9, 8), Image.Resampling.LANCZOS))
    return {
        "dhash": (small[:, 1:] > small[:, :-1]).flatten(),
        "thumbnail": np.asarray(gray.resize((64, 48), Image.Resampling.BILINEAR), dtype=np.float32),
    }


def filename_group(filename):
    """Unconfirmed sample/date cue, not authoritative acquisition metadata."""
    match = re.search(r"_(\d{6})_Amostra-([A-Za-z0-9]+)_", filename)
    if match is None:
        return None
    return hashlib.sha256("/".join(match.groups()).encode()).hexdigest()[:16]


def compare_pairs(records, features):
    pairs = []
    for left, right in itertools.combinations(records, 2):
        a, b = features[left["audit_id"]], features[right["audit_id"]]
        distance = int(np.count_nonzero(a["dhash"] != b["dhash"]))
        x, y = a["thumbnail"].flatten(), b["thumbnail"].flatten()
        x, y = x - x.mean(), y - y.mean()
        norm = float(np.linalg.norm(x) * np.linalg.norm(y))
        correlation = float(np.dot(x, y) / norm) if norm else None
        identical = left["pixel_sha256"] == right["pixel_sha256"]
        byte_identical = left["sha256"] == right["sha256"]
        group = left["filename_group_candidate"]
        same_group = group is not None and group == right["filename_group_candidate"]
        if identical or byte_identical or distance <= 12 or (correlation is not None and correlation >= 0.90) or same_group:
            pairs.append({
                "left": left["audit_id"], "right": right["audit_id"],
                "cross_split": left["source_split"] != right["source_split"],
                "byte_identical": byte_identical, "pixel_identical": identical,
                "mask_identical": left["mask_sha256"] == right["mask_sha256"],
                "dhash_distance": distance, "thumbnail_correlation": correlation,
                "same_filename_group_candidate": same_group,
                "review_status": "pending", "review_note": None,
            })
    return sorted(pairs, key=lambda p: (not p["pixel_identical"], p["dhash_distance"], p["left"], p["right"]))
