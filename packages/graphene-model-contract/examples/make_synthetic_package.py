"""Export/contract fixture only. This identity graph is NOT a trained lab model."""

import argparse
import hashlib
import json
from pathlib import Path
from uuid import uuid4

from onnx import TensorProto, helper

from graphene_model_contract import parse_contract
from graphene_model_contract.package import build_package


def fixture_documents(model: bytes, geometry=None, shape=(1, 3, 32, 32)):
    unknown = {
        "status": "unknown",
        "reason": "Synthetic contract fixture; no training or lab evidence",
    }
    manifest = {
        "schema_version": 1,
        "model_id": str(uuid4()),
        "name": "Synthetic identity fixture",
        "model_version": "1.0.0",
        "architecture": "synthetic-identity-not-trained",
        "artifact": {
            "filename": "model.onnx",
            "sha256": hashlib.sha256(model).hexdigest(),
            "size": len(model),
            "opset": 17,
            "ir_version": 8,
        },
        "classes": [
            {"id": 0, "name": "background", "color": [0, 0, 0]},
            {"id": 1, "name": "few-layer", "color": [55, 183, 255]},
            {"id": 2, "name": "bulk", "color": [255, 180, 84]},
        ],
        "input": {
            "name": "rgb",
            "color_space": "RGB",
            "dtype": "float32",
            "layout": "NCHW",
            "shape": list(shape),
        },
        "output": {
            "name": "logits",
            "dtype": "float32",
            "layout": "NCHW",
            "semantics": "logits",
            "shape": list(shape),
        },
        "preprocessing": {
            "version": 1,
            "scale": 1 / 255,
            "mean": [0.0, 0.0, 0.0],
            "std": [1.0, 1.0, 1.0],
            "padding_rgb": [0, 0, 0],
        },
        "geometry": geometry
        or {"mode": "letterbox", "version": 1, "interpolation": "pillow_bilinear"},
        "decision": {
            "kind": "argmax",
            "ties": "lower_id",
            "evidence_ref": "evaluation",
        },
        "provenance": {
            "sources": [{"name": "Synthetic fixture", "license": unknown}],
            **{
                field: unknown
                for field in (
                    "dataset_fingerprint",
                    "split_fingerprint",
                    "checkpoint",
                    "checkpoint_selection",
                    "run_config",
                    "environment",
                    "seed",
                )
            },
        },
        "metadata": {"purpose": "Contract verification only; not graphene screening"},
    }
    evaluation = {
        "schema_version": 1,
        "model_id": manifest["model_id"],
        "model_sha256": manifest["artifact"]["sha256"],
        "checkpoint": unknown,
        **{
            field: manifest[field]
            for field in ("preprocessing", "geometry", "decision")
        },
        "evidence": {
            "kind": "unmeasured",
            "reason": "Synthetic graph; no lab accuracy measurements",
        },
    }
    return manifest, evaluation


def identity_graph(shape=(1, 3, 32, 32)):
    graph = helper.make_graph(
        [helper.make_node("Identity", ["rgb"], ["logits"])],
        "synthetic",
        [helper.make_tensor_value_info("rgb", TensorProto.FLOAT, shape)],
        [helper.make_tensor_value_info("logits", TensorProto.FLOAT, shape)],
    )
    return helper.make_model(
        graph, opset_imports=[helper.make_opsetid("", 17)], ir_version=8
    ).SerializeToString()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    model = identity_graph()
    raw_manifest, raw_evaluation = fixture_documents(model)
    manifest, evaluation = parse_contract(
        json.dumps(raw_manifest).encode(), json.dumps(raw_evaluation).encode()
    )
    args.output.write_bytes(build_package(model, manifest, evaluation))
    print("Created an unmeasured synthetic package; never use it for lab predictions.")
