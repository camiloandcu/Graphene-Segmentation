"""Bounded I/O and canonical JSON shared by producer and consumer."""
from __future__ import annotations

import hashlib
import io
import json
import warnings
from pathlib import Path, PurePosixPath

import numpy as np
from PIL import Image

MAX_BYTES = 100 * 1024 * 1024
MAX_PIXELS = 16_000_000
MAX_MEMBERS = 2000
# Converted artifacts can be larger than compressed source files.
MAX_ARTIFACT_BYTES = 512 * 1024 * 1024


class DatasetError(ValueError):
    """Input cannot be safely interpreted as a validated dataset."""


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def canonical(value) -> bytes:
    return json.dumps(value, sort_keys=True, separators=(",", ":"),
                      ensure_ascii=False, allow_nan=False).encode("utf-8")


def identity(value) -> str:
    return digest(canonical(value))


def _pairs(items):
    result = {}
    for key, value in items:
        if key in result:
            raise DatasetError(f"Duplicate JSON key: {key}")
        result[key] = value
    return result


def parse_json(data: bytes):
    try:
        return json.loads(data, object_pairs_hook=_pairs,
                          parse_constant=lambda value: (_ for _ in ()).throw(
                              DatasetError(f"Non-finite JSON value: {value}")))
    except (UnicodeError, json.JSONDecodeError, RecursionError) as exc:
        raise DatasetError(f"Invalid JSON: {exc}") from exc


def read_bytes(path: Path, limit=MAX_BYTES) -> bytes:
    if path.is_symlink() or not path.is_file():
        raise DatasetError(f"Expected regular file: {path}")
    with path.open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise DatasetError(f"File exceeds byte limit: {path}")
    return data


def read_json(path: Path):
    return parse_json(read_bytes(path))


def write_json(path: Path, value):
    path.write_bytes(canonical(value) + b"\n")


def safe_path(name: str) -> str:
    if not isinstance(name, str) or not name or "\\" in name or ":" in name or "\x00" in name:
        raise DatasetError(f"Unsafe path: {name!r}")
    path = PurePosixPath(name)
    if path.is_absolute() or any(p in ("..", ".", "") for p in name.split("/")):
        raise DatasetError(f"Unsafe path: {name!r}")
    return name


def decode(data: bytes, *, mask=False) -> np.ndarray:
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as image:
                if image.width * image.height > MAX_PIXELS:
                    raise DatasetError("Decoded image exceeds pixel limit")
                if getattr(image, "n_frames", 1) != 1 or image.getexif().get(274, 1) != 1:
                    raise DatasetError("Multi-frame/oriented images need reviewed geometry")
                if mask:
                    if image.format != "PNG" or image.mode != "L":
                        raise DatasetError("Mask must be an 8-bit grayscale PNG")
                    array = np.asarray(image).copy()
                    if not np.isin(array, [0, 1, 2, 255]).all():
                        raise DatasetError("Mask contains illegal class values")
                    return array
                return np.asarray(image.convert("RGB")).copy()
    except (OSError, ValueError, Image.DecompressionBombWarning, Image.DecompressionBombError) as exc:
        raise DatasetError(f"Image decode failed: {exc}") from exc


def pixel_counts(mask: np.ndarray) -> dict[str, int]:
    values, counts = np.unique(mask, return_counts=True)
    actual = dict(zip(values.tolist(), counts.tolist()))
    return {str(i): actual.get(i, 0) for i in (0, 1, 2, 255)}
