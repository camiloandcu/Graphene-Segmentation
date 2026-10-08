"""Disposable Linux CPU validation process. Never import this in an API worker."""

from __future__ import annotations

import json
import math
from pathlib import Path
import resource
import sys


def inspect_graph(graph, manifest, limits, onnx):
    from .errors import ContractError

    tensor_type = onnx.TensorProto
    if (
        graph.functions
        or graph.training_info
        or graph.graph.sparse_initializer
        or len(graph.graph.node) > limits["nodes"]
    ):
        raise ContractError(
            "unsupported_graph", "Graph constructs exceed the supported profile"
        )
    opsets = [(entry.domain, entry.version) for entry in graph.opset_import]
    if graph.ir_version != manifest.artifact.ir_version or opsets not in (
        [("", 17)],
        [("ai.onnx", 17)],
    ):
        raise ContractError("unsupported_graph", "Unsupported IR/opset")
    widths = {
        tensor_type.FLOAT: 4,
        tensor_type.DOUBLE: 8,
        tensor_type.FLOAT16: 2,
        tensor_type.INT64: 8,
        tensor_type.INT32: 4,
        tensor_type.INT16: 2,
        tensor_type.INT8: 1,
        tensor_type.UINT8: 1,
        tensor_type.UINT16: 2,
        tensor_type.UINT32: 4,
        tensor_type.UINT64: 8,
        tensor_type.BOOL: 1,
        tensor_type.BFLOAT16: 2,
    }
    total = 0

    def check_tensor(tensor):
        nonlocal total
        if tensor.external_data or tensor.data_location == tensor_type.EXTERNAL:
            raise ContractError("external_data", "External tensor data not supported")
        if (
            tensor.data_type not in widths
            or len(tensor.dims) > 8
            or any(d < 0 for d in tensor.dims)
        ):
            raise ContractError(
                "unsupported_graph", "Unsupported tensor representation"
            )
        size = math.prod(tensor.dims) * widths[tensor.data_type]
        total += size
        if size > limits["tensor_bytes"] or total > limits["tensor_bytes"]:
            raise ContractError(
                "tensor_limit", "Tensor declaration exceeds allocation policy"
            )

    for tensor in graph.graph.initializer:
        check_tensor(tensor)
    for node in graph.graph.node:
        if node.domain not in ("", "ai.onnx") or node.op_type in {"If", "Loop", "Scan"}:
            raise ContractError(
                "unsupported_graph", "Unsupported operator domain/control flow"
            )
        for attribute in node.attribute:
            if attribute.type in (
                onnx.AttributeProto.GRAPH,
                onnx.AttributeProto.GRAPHS,
                onnx.AttributeProto.SPARSE_TENSOR,
                onnx.AttributeProto.SPARSE_TENSORS,
            ):
                raise ContractError(
                    "unsupported_graph", "Subgraphs/sparse attributes not supported"
                )
            if attribute.type == onnx.AttributeProto.TENSOR:
                check_tensor(attribute.t)
            elif attribute.type == onnx.AttributeProto.TENSORS:
                for tensor in attribute.tensors:
                    check_tensor(tensor)
    for values, spec in (
        (graph.graph.input, manifest.input),
        (graph.graph.output, manifest.output),
    ):
        if len(values) != 1:
            raise ContractError(
                "graph_interface", "Graph requires exactly one input and one output"
            )
        value = values[0]
        shape = tuple(
            d.dim_value if d.HasField("dim_value") else None
            for d in value.type.tensor_type.shape.dim
        )
        if (
            value.name != spec.name
            or value.type.tensor_type.elem_type != tensor_type.FLOAT
            or shape != spec.shape
        ):
            raise ContractError(
                "graph_interface", "Declared graph interface disagrees with manifest"
            )
    for value in (*graph.graph.value_info, *graph.graph.input, *graph.graph.output):
        if not value.type.HasField("tensor_type"):
            raise ContractError(
                "unsupported_graph", "Non-tensor values are unsupported"
            )
        dims = value.type.tensor_type.shape.dim
        if len(dims) > 8 or any(
            d.HasField("dim_value") and d.dim_value < 0 for d in dims
        ):
            raise ContractError("tensor_limit", "Unsupported tensor dimensions")
        if all(d.HasField("dim_value") for d in dims):
            if math.prod(d.dim_value for d in dims) * 8 > limits["tensor_bytes"]:
                raise ContractError(
                    "tensor_limit",
                    "Declared intermediate tensor exceeds allocation policy",
                )


def check(root, job):
    import hashlib
    import numpy as np
    import onnx
    import onnxruntime as ort
    from .contract import Manifest
    from .errors import ContractError
    from .geometry import normalize, smoke_rgb

    manifest = Manifest.model_validate_json(json.dumps(job["manifest"]))
    graph = onnx.load_model(root / "model.onnx", load_external_data=False)
    inspect_graph(graph, manifest, job["limits"], onnx)
    onnx.checker.check_model(graph, full_check=True)
    options = ort.SessionOptions()
    options.intra_op_num_threads = options.inter_op_num_threads = 1
    options.execution_mode = ort.ExecutionMode.ORT_SEQUENTIAL
    options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_DISABLE_ALL
    options.log_severity_level = 4
    session = ort.InferenceSession(
        graph.SerializeToString(),
        sess_options=options,
        providers=["CPUExecutionProvider"],
    )
    tensor = normalize(smoke_rgb(manifest.input.shape[2:]), manifest.preprocessing)
    outputs = session.run([manifest.output.name], {manifest.input.name: tensor})
    output = outputs[0]
    if (
        output.shape != manifest.output.shape
        or output.dtype != np.float32
        or not np.isfinite(output).all()
    ):
        raise ContractError("invalid_logits", "Smoke output is incompatible/non-finite")
    return {
        "shape": list(output.shape),
        "dtype": "float32",
        "providers": session.get_providers(),
        "input_sha256": hashlib.sha256(tensor.tobytes()).hexdigest(),
        "output_sha256": hashlib.sha256(output.tobytes()).hexdigest(),
        "onnx": onnx.__version__,
        "onnxruntime": ort.__version__,
        "numpy": np.__version__,
    }


def main():
    root = Path(sys.argv[1])
    job = json.loads((root / "job.json").read_bytes())
    limits = job["limits"]
    # Apply before ONNX/NumPy/session import; no inherited model session or GPU.
    resource.setrlimit(
        resource.RLIMIT_AS, (limits["address_bytes"], limits["address_bytes"])
    )
    resource.setrlimit(
        resource.RLIMIT_CPU, (limits["cpu_seconds"], limits["cpu_seconds"])
    )
    resource.setrlimit(resource.RLIMIT_FSIZE, (8192, 8192))
    resource.setrlimit(resource.RLIMIT_CORE, (0, 0))
    try:
        smoke = check(root, job)
        result, status = {"ok": True, "smoke": smoke}, 0
    except MemoryError:
        result, status = {"ok": False, "code": "resource_limit"}, 1
    except ImportError:
        result, status = {"ok": False, "code": "missing_runtime"}, 1
    except Exception as error:
        result, status = (
            {"ok": False, "code": getattr(error, "code", "graph_invalid")},
            1,
        )
    (root / "result.json").write_text(json.dumps(result))
    return status


if __name__ == "__main__":
    sys.exit(main())
