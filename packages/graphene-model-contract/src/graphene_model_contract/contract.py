"""Strict v1 model/evaluation structure, plus cross-document invariants."""

from __future__ import annotations

import json
import math
from typing import Annotated, Literal, Union
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, ValidationError, model_validator

from .errors import ContractError

Name = Annotated[str, Field(min_length=1, max_length=128)]
Text = Annotated[str, Field(min_length=1, max_length=4096)]
Dimension = Annotated[int, Field(ge=32, le=1024, multiple_of=32)]
Channel = Annotated[int, Field(ge=0, le=255)]
Finite = Annotated[float, Field(allow_inf_nan=False)]
Positive = Annotated[float, Field(gt=0, allow_inf_nan=False)]
Digest = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True, strict=True)


class Known(StrictModel):
    status: Literal["known"]
    value: Text


class Unknown(StrictModel):
    status: Literal["unknown"]
    reason: Text


Recorded = Annotated[Union[Known, Unknown], Field(discriminator="status")]


class Source(StrictModel):
    name: Name
    license: Recorded


class Provenance(StrictModel):
    sources: Annotated[tuple[Source, ...], Field(min_length=1, max_length=20)]
    dataset_fingerprint: Recorded
    split_fingerprint: Recorded
    checkpoint: Recorded
    checkpoint_selection: Recorded
    run_config: Recorded
    environment: Recorded
    seed: Recorded


class Background(StrictModel):
    id: Literal[0]
    name: Literal["background"]
    color: tuple[Channel, Channel, Channel]


class FewLayer(StrictModel):
    id: Literal[1]
    name: Literal["few-layer"]
    color: tuple[Channel, Channel, Channel]


class Bulk(StrictModel):
    id: Literal[2]
    name: Literal["bulk"]
    color: tuple[Channel, Channel, Channel]


class ArtifactSpec(StrictModel):
    filename: Literal["model.onnx"]
    sha256: Digest
    size: Annotated[int, Field(gt=0)]
    opset: Literal[17]
    ir_version: Literal[8, 9, 10]


class InputSpec(StrictModel):
    name: Name
    color_space: Literal["RGB"]
    dtype: Literal["float32"]
    layout: Literal["NCHW"]
    shape: tuple[Literal[1], Literal[3], Dimension, Dimension]


class OutputSpec(StrictModel):
    name: Name
    dtype: Literal["float32"]
    layout: Literal["NCHW"]
    semantics: Literal["logits"]
    shape: tuple[Literal[1], Literal[3], Dimension, Dimension]


class Preprocessing(StrictModel):
    version: Literal[1]
    scale: Literal[1 / 255]
    mean: tuple[Finite, Finite, Finite]
    std: tuple[Positive, Positive, Positive]
    padding_rgb: tuple[Channel, Channel, Channel]


class Letterbox(StrictModel):
    mode: Literal["letterbox"]
    version: Literal[1]
    interpolation: Literal["pillow_bilinear"]


class Tiles(StrictModel):
    mode: Literal["tiles"]
    version: Literal[1]
    stride: tuple[Annotated[int, Field(gt=0)], Annotated[int, Field(gt=0)]]
    merge: Literal["mean_logits"]


Geometry = Annotated[Union[Letterbox, Tiles], Field(discriminator="mode")]


class Argmax(StrictModel):
    kind: Literal["argmax"]
    ties: Literal["lower_id"]
    evidence_ref: Literal["evaluation"]


class FewThreshold(StrictModel):
    kind: Literal["few_layer_threshold"]
    threshold: Annotated[float, Field(gt=0, lt=1, allow_inf_nan=False)]
    ties: Literal["lower_id"]
    evidence_ref: Literal["evaluation"]


Decision = Annotated[Union[Argmax, FewThreshold], Field(discriminator="kind")]


class Manifest(StrictModel):
    schema_version: Literal[1]
    model_id: UUID
    name: Name
    model_version: Annotated[str, Field(min_length=1, max_length=64)]
    architecture: Name
    artifact: ArtifactSpec
    classes: tuple[Background, FewLayer, Bulk]
    input: InputSpec
    output: OutputSpec
    preprocessing: Preprocessing
    geometry: Geometry
    decision: Decision
    provenance: Provenance
    metadata: Annotated[dict[Name, Text], Field(max_length=64)]

    @model_validator(mode="after")
    def coherent_shapes(self):
        if self.input.shape != self.output.shape:
            raise ValueError(
                "Output must match the three-channel full input resolution"
            )
        if isinstance(self.geometry, Tiles):
            if any(
                stride > dim
                for stride, dim in zip(self.geometry.stride, self.input.shape[2:])
            ):
                raise ValueError("Tile stride exceeds tile dimensions")
        return self


class Metric(StrictModel):
    name: Name
    value: Annotated[float, Field(ge=0, allow_inf_nan=False)] | None
    unit: Literal["fraction", "count", "milliseconds"]
    support: Annotated[int, Field(ge=0)] | None
    definition: Text
    unavailable_reason: Text | None
    support_unknown_reason: Text | None

    @model_validator(mode="after")
    def explicit_support(self):
        if self.value is None and self.unavailable_reason is None:
            raise ValueError("Unavailable metric requires a reason")
        if self.support is None and self.support_unknown_reason is None:
            raise ValueError("Unknown support requires a reason")
        if self.unit == "fraction" and self.value is not None:
            if self.value > 1 or self.support == 0:
                raise ValueError(
                    "Fraction must be in [0,1] and cannot score zero support"
                )
        return self


class Unmeasured(StrictModel):
    kind: Literal["unmeasured"]
    reason: Text


class Reported(StrictModel):
    kind: Literal["reported"]
    source: Text
    dataset_fingerprint: Text
    split_fingerprint: Text
    metrics: Annotated[tuple[Metric, ...], Field(min_length=1, max_length=100)]


Evidence = Annotated[Union[Unmeasured, Reported], Field(discriminator="kind")]


class Evaluation(StrictModel):
    schema_version: Literal[1]
    model_id: UUID
    model_sha256: Digest
    checkpoint: Recorded
    preprocessing: Preprocessing
    geometry: Geometry
    decision: Decision
    evidence: Evidence


def strict_json(data: bytes) -> dict:
    def pairs(items):
        result = {}
        for key, value in items:
            if key in result:
                raise ValueError("Duplicate JSON key")
            result[key] = value
        return result

    try:
        result = json.loads(
            data,
            object_pairs_hook=pairs,
            parse_constant=lambda _: (_ for _ in ()).throw(
                ValueError("Non-finite JSON")
            ),
        )
        if not isinstance(result, dict):
            raise ValueError("Expected a JSON object")
        pending = [result]
        while pending:
            value = pending.pop()
            if isinstance(value, dict):
                pending.extend(value.values())
            elif isinstance(value, list):
                pending.extend(value)
            elif isinstance(value, float) and not math.isfinite(value):
                raise ValueError("Non-finite JSON number")
        return result
    except (ValueError, UnicodeDecodeError, RecursionError):
        raise ContractError(
            "invalid_json", "JSON must be a finite object without duplicate keys."
        ) from None


def parse_document(data: bytes, model: type[StrictModel]):
    decoded = strict_json(data)
    pending = [decoded]
    while pending:
        value = pending.pop()
        if isinstance(value, dict):
            pending.extend(value.values())
        elif isinstance(value, list):
            pending.extend(value)
        elif isinstance(value, bool):
            # No v1 field is boolean; Literal[1] must not accept True == 1.
            raise ContractError(
                "invalid_schema",
                "Boolean values cannot substitute v1 numeric/string fields.",
            )
    try:
        # JSON mode deliberately supports UUID/tuple representations, without scalar coercion.
        return model.model_validate_json(data)
    except (ValidationError, ValueError):
        raise ContractError(
            "invalid_schema",
            f"{model.__name__} does not match the supported v1 contract.",
        ) from None


def parse_contract(
    manifest_bytes: bytes, evaluation_bytes: bytes
) -> tuple[Manifest, Evaluation]:
    manifest = parse_document(manifest_bytes, Manifest)
    evaluation = parse_document(evaluation_bytes, Evaluation)
    if (
        evaluation.model_id != manifest.model_id
        or evaluation.model_sha256 != manifest.artifact.sha256
        or evaluation.checkpoint != manifest.provenance.checkpoint
        or evaluation.preprocessing != manifest.preprocessing
        or evaluation.geometry != manifest.geometry
        or evaluation.decision != manifest.decision
    ):
        raise ContractError(
            "evaluation_mismatch",
            "Evaluation identity, checkpoint or settings disagree with the manifest.",
        )
    if isinstance(evaluation.evidence, Reported):
        for field in ("dataset_fingerprint", "split_fingerprint"):
            recorded = getattr(manifest.provenance, field)
            if not isinstance(recorded, Known) or recorded.value != getattr(
                evaluation.evidence, field
            ):
                raise ContractError(
                    "evaluation_mismatch",
                    "Reported dataset/split evidence must match known provenance.",
                )
    return manifest, evaluation
