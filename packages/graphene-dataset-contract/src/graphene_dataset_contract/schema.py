"""Strict, versioned review and artifact structures; unknown facts stay explicit."""
from __future__ import annotations

from typing import Annotated, Literal

from graphene_model_contract.contract import Background, FewLayer, Bulk
from pydantic import BaseModel, ConfigDict, Field, model_validator

Text = Annotated[str, Field(min_length=1, max_length=4096)]
Hash = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
Count = Annotated[int, Field(ge=0)]
SampleID = Annotated[str, Field(pattern=r"^(train|valid|test)-[0-9]{3,}$")]
Role = Literal["train", "validation", "test", "excluded"]

# Resolve definitions from the authoritative portable model contract.
CLASSES = [item.model_dump(exclude={"color"}) for item in (
    Background(id=0, name="background", color=(0, 0, 0)),
    FewLayer(id=1, name="few-layer", color=(0, 220, 255)),
    Bulk(id=2, name="bulk", color=(255, 100, 40)),
)]
MAPPING = {"few-layer": 1, "bulk": 2}


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)

    @model_validator(mode="before")
    @classmethod
    def integer_constants(cls, value):
        # Python equality makes True/1.0 match Literal[1]; JSON versions must be integers.
        if isinstance(value, dict):
            for key in ("schema_version", "ignore_value", "class_id", "category_id"):
                if key in value and type(value[key]) is not int:
                    raise ValueError(f"{key} must be a JSON integer")
        return value


class Pair(Strict):
    left: SampleID
    right: SampleID
    evidence: Text


class Groups(Strict):
    schema_version: Literal[1]
    source_sha256: Hash
    pairs: list[Pair]


class Disposition(Strict):
    left: SampleID
    right: SampleID
    decision: Literal["co-group", "excluded", "unrelated", "uncertain"]
    rationale: Text


class Decision(Strict):
    sample_id: SampleID
    source_path: Text
    role: Role | None = None
    exclusion_reason: Text | None = None
    origin: Literal["human", "prediction", "unknown"] | None = None
    origin_evidence: Text | None = None
    eligibility_approved: bool | None = None
    completeness: Literal["exhaustive", "verified-background", "non-exhaustive"] | None = None
    conflict_policy: Literal["reject", "ignore"] = "reject"
    conflict_rationale: Text | None = None
    group: Text | None = None
    group_status: Literal["known", "unknown"] | None = None
    group_evidence: Text | None = None


class Evaluation(Strict):
    status: Literal["exploratory", "independence-reviewed"]
    evidence: Text
    limitations: list[Text]


class Review(Strict):
    schema_version: Literal[1]
    source_sha256: Hash
    reference: Text | None = None
    reviewer: Text | None = None
    date: Annotated[str, Field(pattern=r"^\d{4}-\d{2}-\d{2}$")] | None = None
    mapping: dict[str, int] | None = None
    class_semantics_approved: bool | None = None
    evaluation: Evaluation | None = None
    samples: list[Decision]
    dispositions: list[Disposition] = []


class Sample(Strict):
    sample_id: SampleID
    source_image_id: Count
    source_path: Text
    original_role: Literal["train", "valid", "test"]
    role: Role
    annotation_count: Count
    width: Annotated[int, Field(gt=0)]
    height: Annotated[int, Field(gt=0)]
    source_sha256: Hash
    rgb_sha256: Hash
    class_pixels: dict[str, Count]
    mask_pixels_sha256: Hash
    image_path: Text | None = None
    mask_path: Text | None = None
    image_sha256: Hash | None = None
    mask_sha256: Hash | None = None


class Source(Strict):
    sha256: Hash
    metadata: dict
    unknowns: list[Text]
    annotation_files: dict[str, Hash]


class PixelClass(Strict):
    id: Annotated[int, Field(ge=0, le=2)]
    name: Literal["background", "few-layer", "bulk"]


class Manifest(Strict):
    schema_version: Literal[1]
    converter_version: Literal["1.0.0"]
    classes: list[PixelClass]
    ignore_value: Literal[255]
    source: Source
    settings: dict
    review: Review
    group_evidence: Groups
    samples: list[Sample]
    split_fingerprint: Hash
    dataset_fingerprint: Hash


class Report(Strict):
    schema_version: Literal[1]
    status: Literal["ready", "blocked", "invalid"]
    source_sha256: Hash
    blockers: list[Text]
    counts: dict[str, Count]
    support: dict[str, dict[str, Count]]
    evaluation: Evaluation | None
    inventory: list[dict]
