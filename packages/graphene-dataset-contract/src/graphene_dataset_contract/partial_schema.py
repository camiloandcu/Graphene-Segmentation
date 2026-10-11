"""Version 2 represents partial supervision without redefining dense version 1."""
from typing import Annotated, Literal
from pydantic import Field
from .schema import Count, Decision, Hash, Manifest, Report, Review, Sample, Strict, Text


class BackgroundAnchor(Strict):
    id: Text
    image_sha256: Hash
    class_id: Literal[0]
    polygons: list[list[float | int]]
    evidence: Text
    reviewer: Text
    date: Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}$")]


class PartialDecision(Decision):
    background_anchors: list[BackgroundAnchor] = []


class PartialReview(Review):
    schema_version: Literal[2]
    supervision_mode: Literal["partial"] = "partial"
    samples: list[PartialDecision]


class SourcePolygon(Strict):
    id: Count
    category_id: Literal[1, 2]
    segmentation: list[list[float | int]]


class PartialSample(Sample):
    source_class_pixels: dict[str, Count]
    source_mask_pixels_sha256: Hash
    source_polygons: list[SourcePolygon]


class PartialManifest(Manifest):
    schema_version: Literal[2]
    converter_version: Literal["2.0.0"]
    supervision_mode: Literal["partial"] = "partial"
    review: PartialReview
    samples: list[PartialSample]
    supervision_fingerprint: Hash


class PartialReport(Report):
    schema_version: Literal[2]
    supervision_mode: Literal["partial"] = "partial"
