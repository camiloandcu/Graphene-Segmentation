"""Versioned RGB preparation, inverse logits and native tile reconstruction."""

from __future__ import annotations

from dataclasses import dataclass
import math
from typing import Iterator

import numpy as np
from PIL import Image

from .contract import Argmax, Manifest, Preprocessing, Tiles
from .errors import ContractError


@dataclass(frozen=True)
class GeometryLimits:
    max_pixels: int = 16_000_000
    max_tiles: int = 4096

    def __post_init__(self):
        if any(
            type(value) is not int or value <= 0
            for value in (self.max_pixels, self.max_tiles)
        ):
            raise ValueError("Geometry budgets must be positive integers")


@dataclass(frozen=True)
class GeometryRecord:
    mode: str
    original_hw: tuple[int, int]
    resized_hw: tuple[int, int]
    tensor_hw: tuple[int, int]
    top: int
    left: int
    origin_yx: tuple[int, int] = (0, 0)


@dataclass(frozen=True)
class Prepared:
    tensor: np.ndarray
    geometry: GeometryRecord


def check_size(hw: tuple[int, int], limits: GeometryLimits) -> None:
    if len(hw) != 2 or any(type(value) is not int or value <= 0 for value in hw):
        raise ContractError(
            "invalid_pixels", "Image dimensions must be positive integers."
        )
    if hw[0] * hw[1] > limits.max_pixels:
        raise ContractError(
            "image_limit", "Original image exceeds the configured pixel budget."
        )


def check_rgb(rgb: np.ndarray, limits: GeometryLimits) -> None:
    if (
        not isinstance(rgb, np.ndarray)
        or rgb.dtype != np.uint8
        or rgb.ndim != 3
        or rgb.shape[2] != 3
    ):
        raise ContractError("invalid_pixels", "Expected oriented uint8 RGB HWC pixels.")
    check_size(rgb.shape[:2], limits)


def normalize(rgb: np.ndarray, preprocessing: Preprocessing) -> np.ndarray:
    values = rgb.astype(np.float32) * np.float32(preprocessing.scale)
    values -= np.asarray(preprocessing.mean, dtype=np.float32)
    values /= np.asarray(preprocessing.std, dtype=np.float32)
    if not np.isfinite(values).all():
        raise ContractError(
            "invalid_normalization", "Normalization produced non-finite values."
        )
    return np.ascontiguousarray(values.transpose(2, 0, 1)[None])


def prepare_letterbox(
    rgb: np.ndarray, manifest: Manifest, limits: GeometryLimits = GeometryLimits()
) -> Prepared:
    check_rgb(rgb, limits)
    if manifest.geometry.mode != "letterbox":
        raise ContractError(
            "geometry_mismatch", "Package requires native tiles, not letterbox."
        )
    h, w = rgb.shape[:2]
    th, tw = manifest.input.shape[2:]
    scale = min(th / h, tw / w)
    rh = min(th, max(1, math.floor(h * scale + 0.5)))
    rw = min(tw, max(1, math.floor(w * scale + 0.5)))
    top, left = (th - rh) // 2, (tw - rw) // 2
    resized = np.asarray(
        Image.fromarray(rgb).resize((rw, rh), Image.Resampling.BILINEAR)
    )
    padded = np.empty((th, tw, 3), dtype=np.uint8)
    padded[:] = manifest.preprocessing.padding_rgb
    padded[top : top + rh, left : left + rw] = resized
    record = GeometryRecord("letterbox", (h, w), (rh, rw), (th, tw), top, left)
    return Prepared(normalize(padded, manifest.preprocessing), record)


def check_logits(logits: np.ndarray, hw: tuple[int, int]) -> np.ndarray:
    if (
        not isinstance(logits, np.ndarray)
        or logits.dtype != np.float32
        or logits.shape != (1, 3, *hw)
        or not np.isfinite(logits).all()
    ):
        raise ContractError(
            "invalid_logits", "Expected finite float32 [1,3,H,W] logits."
        )
    return logits[0]


def restore_letterbox(
    logits: np.ndarray,
    geometry: GeometryRecord,
    limits: GeometryLimits = GeometryLimits(),
) -> np.ndarray:
    check_size(geometry.original_hw, limits)
    if geometry.mode != "letterbox":
        raise ContractError("geometry_mismatch", "Expected letterbox geometry.")
    planes = check_logits(logits, geometry.tensor_hw)
    rh, rw = geometry.resized_hw
    th, tw = geometry.tensor_hw
    if (
        rh <= 0
        or rw <= 0
        or geometry.top < 0
        or geometry.left < 0
        or geometry.top + rh > th
        or geometry.left + rw > tw
    ):
        raise ContractError(
            "invalid_geometry", "Padding/resize record is outside the input tensor."
        )
    h, w = geometry.original_hw
    restored = np.empty((3, h, w), dtype=np.float32)
    for channel in range(3):
        cropped = planes[
            channel,
            geometry.top : geometry.top + rh,
            geometry.left : geometry.left + rw,
        ]
        restored[channel] = np.asarray(
            Image.fromarray(cropped).resize((w, h), Image.Resampling.BILINEAR)
        )
    return restored


def _positions(size: int, tile: int, stride: int) -> tuple[int, ...]:
    end = max(0, size - tile)
    positions = tuple(range(0, end + 1, stride))
    return positions if positions[-1] == end else (*positions, end)


def tile_records(
    hw: tuple[int, int], manifest: Manifest, limits: GeometryLimits = GeometryLimits()
) -> tuple[GeometryRecord, ...]:
    check_size(hw, limits)
    if not isinstance(manifest.geometry, Tiles):
        raise ContractError(
            "geometry_mismatch", "Package does not declare native tiles."
        )
    th, tw = manifest.input.shape[2:]
    sy, sx = manifest.geometry.stride
    h, w = hw
    counts = [
        (max(0, size - tile) // stride + 1 + (max(0, size - tile) % stride != 0))
        for size, tile, stride in ((h, th, sy), (w, tw, sx))
    ]
    if counts[0] * counts[1] > limits.max_tiles:
        raise ContractError(
            "tile_limit", "Tile plan exceeds the configured work budget."
        )
    return tuple(
        GeometryRecord(
            "tiles", hw, (min(th, h - y), min(tw, w - x)), (th, tw), 0, 0, (y, x)
        )
        for y in _positions(h, th, sy)
        for x in _positions(w, tw, sx)
    )


def prepare_tiles(
    rgb: np.ndarray, manifest: Manifest, limits: GeometryLimits = GeometryLimits()
) -> Iterator[Prepared]:
    check_rgb(rgb, limits)
    for record in tile_records(rgb.shape[:2], manifest, limits):
        th, tw = record.tensor_hw
        rh, rw = record.resized_hw
        y, x = record.origin_yx
        padded = np.empty((th, tw, 3), dtype=np.uint8)
        padded[:] = manifest.preprocessing.padding_rgb
        padded[:rh, :rw] = rgb[y : y + rh, x : x + rw]
        yield Prepared(normalize(padded, manifest.preprocessing), record)


class TileAccumulator:
    def __init__(
        self,
        original_hw: tuple[int, int],
        manifest: Manifest,
        limits: GeometryLimits = GeometryLimits(),
    ):
        self.records = frozenset(tile_records(original_hw, manifest, limits))
        self.seen: set[GeometryRecord] = set()
        self.sums = np.zeros((3, *original_hw), dtype=np.float32)
        self.counts = np.zeros(original_hw, dtype=np.uint32)

    def add(self, logits: np.ndarray, geometry: GeometryRecord) -> None:
        if geometry not in self.records or geometry in self.seen:
            raise ContractError(
                "invalid_tile", "Tile is duplicate or outside the declared plan."
            )
        planes = check_logits(logits, geometry.tensor_hw)
        h, w = geometry.resized_hw
        y, x = geometry.origin_yx
        region = self.sums[:, y : y + h, x : x + w]
        with np.errstate(over="ignore"):
            merged = region + planes[:, :h, :w]
        if not np.isfinite(merged).all():
            raise ContractError(
                "invalid_logits", "Overlap logits exceeded finite accumulation range."
            )
        region[:] = merged
        self.counts[y : y + h, x : x + w] += 1
        self.seen.add(geometry)

    def finish(self) -> np.ndarray:
        if self.seen != self.records or (self.counts == 0).any():
            raise ContractError(
                "missing_tile",
                "All original pixels require their declared tile contributions.",
            )
        return self.sums / self.counts.astype(np.float32)[None]


def decide(
    logits: np.ndarray, manifest: Manifest, limits: GeometryLimits = GeometryLimits()
) -> np.ndarray:
    if (
        not isinstance(logits, np.ndarray)
        or logits.dtype != np.float32
        or logits.ndim != 3
        or logits.shape[0] != 3
    ):
        raise ContractError(
            "invalid_logits", "Decision requires float32 [3,H,W] logits."
        )
    check_size(logits.shape[1:], limits)
    if not np.isfinite(logits).all():
        raise ContractError("invalid_logits", "Decision logits must be finite.")
    if isinstance(manifest.decision, Argmax):
        return logits.argmax(axis=0).astype(np.uint8)
    stable = logits.astype(np.float64)
    stable -= stable.max(axis=0)
    probabilities = np.exp(stable)
    probabilities /= probabilities.sum(axis=0)
    mask = np.where(probabilities[0] >= probabilities[2], 0, 2).astype(np.uint8)
    mask[probabilities[1] >= manifest.decision.threshold] = 1
    return mask


def smoke_rgb(hw: tuple[int, int]) -> np.ndarray:
    y, x = np.indices(hw)
    return np.stack((x % 256, y % 256, (x + y) % 256), axis=-1).astype(np.uint8)
