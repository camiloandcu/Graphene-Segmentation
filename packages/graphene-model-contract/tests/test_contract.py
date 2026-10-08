import copy
from importlib.resources import files
import json

import jsonschema
import pytest

from graphene_model_contract import ContractError, parse_contract
from graphene_model_contract.contract import Evaluation, Manifest


def parse(manifest, evaluation):
    return parse_contract(
        json.dumps(manifest).encode(), json.dumps(evaluation).encode()
    )


def test_schema_and_parser_agree_and_published_schema_is_current(documents):
    _, raw, report = documents
    manifest, evaluation = parse(raw, report)
    for model, name, data in (
        (Manifest, "manifest", raw),
        (Evaluation, "evaluation", report),
    ):
        schema = json.loads(
            files("graphene_model_contract")
            .joinpath("schemas", name + "-v1.schema.json")
            .read_text()
        )
        jsonschema.Draft202012Validator(
            schema, format_checker=jsonschema.FormatChecker()
        ).validate(data)
        assert {
            k: v for k, v in schema.items() if k not in ("$id", "$schema")
        } == model.model_json_schema()
    assert manifest.input.shape == (1, 3, 32, 32)
    assert tuple(cls.name for cls in manifest.classes) == (
        "background",
        "few-layer",
        "bulk",
    )
    assert evaluation.evidence.kind == "unmeasured"


@pytest.mark.parametrize(
    "damage",
    ["version", "unknown", "binary", "classes", "normalization", "shape", "stride"],
)
def test_incompatible_schema_is_rejected(documents, damage):
    _, raw, report = documents
    if damage == "version":
        raw["schema_version"] = 2
    elif damage == "unknown":
        raw["guessed_framework"] = "pytorch"
    elif damage == "binary":
        raw["output"]["shape"][1] = 1
    elif damage == "classes":
        raw["classes"][1]["name"] = "mono"
    elif damage == "normalization":
        raw["preprocessing"]["std"][0] = 0
    elif damage == "shape":
        raw["input"]["shape"][2] = 33
    elif damage == "stride":
        raw["geometry"] = {
            "mode": "tiles",
            "version": 1,
            "stride": [33, 32],
            "merge": "mean_logits",
        }
    with pytest.raises(ContractError) as error:
        parse(raw, report)
    assert error.value.code == "invalid_schema"


@pytest.mark.parametrize(
    "field",
    ["model_id", "model_sha256", "checkpoint", "preprocessing", "geometry", "decision"],
)
def test_report_identity_and_settings_must_match(documents, field):
    _, raw, report = documents
    report = copy.deepcopy(report)
    if field == "model_id":
        report[field] = "00000000-0000-0000-0000-000000000001"
    elif field == "model_sha256":
        report[field] = "0" * 64
    elif field == "checkpoint":
        report[field] = {"status": "known", "value": "different checkpoint"}
    elif field == "preprocessing":
        report[field]["mean"][0] = 0.5
    elif field == "geometry":
        report[field] = {
            "mode": "tiles",
            "version": 1,
            "stride": [32, 32],
            "merge": "mean_logits",
        }
    else:
        report[field] = {
            "kind": "few_layer_threshold",
            "threshold": 0.2,
            "ties": "lower_id",
            "evidence_ref": "evaluation",
        }
    with pytest.raises(ContractError) as error:
        parse(raw, report)
    assert error.value.code == "evaluation_mismatch"


@pytest.mark.parametrize(
    "data",
    [
        b'{"schema_version":1,"schema_version":1}',
        b'{"value":NaN}',
        b'{"value":Infinity}',
        b"[]",
        b"\xff",
    ],
)
def test_strict_json_rejection(data, documents):
    _, _, report = documents
    with pytest.raises(ContractError) as error:
        parse_contract(data, json.dumps(report).encode())
    assert error.value.code == "invalid_json"


def test_reported_metrics_are_supplied_not_verified_and_zero_support_is_unavailable(
    documents,
):
    _, raw, report = documents
    for field in ("dataset_fingerprint", "split_fingerprint"):
        raw["provenance"][field] = {"status": "known", "value": field + "-fixture"}
    report["evidence"] = {
        "kind": "reported",
        "source": "fixture author supplied",
        "dataset_fingerprint": "dataset_fingerprint-fixture",
        "split_fingerprint": "split_fingerprint-fixture",
        "metrics": [
            {
                "name": "few-layer IoU",
                "value": None,
                "unit": "fraction",
                "support": 0,
                "definition": "intersection/union; no class support",
                "unavailable_reason": "No support",
                "support_unknown_reason": None,
            }
        ],
    }
    _, evaluation = parse(raw, report)
    assert evaluation.evidence.kind == "reported"
    report["evidence"]["metrics"][0]["value"] = 1.0
    with pytest.raises(ContractError):
        parse(raw, report)


def test_reported_evidence_cannot_invent_dataset_provenance(documents):
    _, raw, report = documents
    report["evidence"] = {
        "kind": "reported",
        "source": "supplied",
        "dataset_fingerprint": "fake",
        "split_fingerprint": "fake",
        "metrics": [
            {
                "name": "recall",
                "value": 0.9,
                "unit": "fraction",
                "support": 10,
                "definition": "TP/(TP+FN)",
                "unavailable_reason": None,
                "support_unknown_reason": None,
            }
        ],
    }
    with pytest.raises(ContractError) as error:
        parse(raw, report)
    assert error.value.code == "evaluation_mismatch"


@pytest.mark.parametrize("field", ["schema_version", "id", "scale", "shape"])
def test_boolean_does_not_masquerade_as_numeric_literal(documents, field):
    _, raw, report = documents
    if field == "schema_version":
        raw[field] = True
    elif field == "id":
        raw["classes"][1][field] = True
    elif field == "scale":
        raw["preprocessing"][field] = True
    else:
        raw["input"]["shape"][0] = True
    with pytest.raises(ContractError) as error:
        parse(raw, report)
    assert error.value.code == "invalid_schema"


def test_nonfinite_exponent_is_rejected_as_json(documents):
    _, raw, report = documents
    data = (
        json.dumps(raw)
        .replace('"schema_version": 1', '"schema_version": 1e999')
        .encode()
    )
    with pytest.raises(ContractError) as error:
        parse_contract(data, json.dumps(report).encode())
    assert error.value.code == "invalid_json"
