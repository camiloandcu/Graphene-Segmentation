import hashlib
import io
import json
import stat
import subprocess
import sys
import zipfile

import numpy as np
import onnx
from onnx import TensorProto, helper
import pytest

from graphene_model_contract import ContractError, parse_contract
from graphene_model_contract.package import (
    ValidationLimits,
    build_package,
    validate_file,
    validate_package,
)


def archive(
    model,
    manifest,
    report,
    compression=zipfile.ZIP_STORED,
    name="model.onnx",
    info=None,
):
    output = io.BytesIO()
    with zipfile.ZipFile(output, "w", compression=compression) as z:
        z.writestr(info or name, model)
        z.writestr("manifest.json", json.dumps(manifest))
        z.writestr("evaluation.json", json.dumps(report))
    return output.getvalue()


def changed_graph(documents, graph):
    _, manifest, report = documents
    model = graph.SerializeToString()
    manifest["artifact"]["size"] = len(model)
    manifest["artifact"]["sha256"] = report["model_sha256"] = hashlib.sha256(
        model
    ).hexdigest()
    return model, manifest, report


def test_producer_to_distinct_cli_consumer_and_golden_smoke(documents, tmp_path):
    model, raw, report = documents
    manifest, evaluation = parse_contract(
        json.dumps(raw).encode(), json.dumps(report).encode()
    )
    bundle = build_package(model, manifest, evaluation)
    target = tmp_path / "synthetic.zip"
    target.write_bytes(bundle)
    consumed = validate_file(target)
    assert consumed.manifest == manifest and consumed.evidence_kind == "unmeasured"
    expected = np.empty((1, 3, 32, 32), dtype=np.float32)
    for y in range(32):
        for x in range(32):
            expected[0, :, y, x] = np.array([x, y, x + y], np.float32) * np.float32(
                1 / 255
            )
    digest = hashlib.sha256(expected.tobytes()).hexdigest()
    assert consumed.smoke["input_sha256"] == consumed.smoke["output_sha256"] == digest
    result = subprocess.run(
        [sys.executable, "-m", "graphene_model_contract.cli", str(target)],
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr
    parsed = json.loads(result.stdout)
    assert parsed["compatible"] and not parsed["evaluation_verified"]
    assert parsed["evaluation"] == "unmeasured"
    assert parsed["smoke"]["providers"] == ["CPUExecutionProvider"]


@pytest.mark.parametrize(
    "name", ["../model.onnx", "/model.onnx", "folder/model.onnx", "model\\onnx"]
)
def test_unsafe_members_rejected(documents, name):
    model, raw, report = documents
    with pytest.raises(ContractError) as error:
        validate_package(archive(model, raw, report, name=name))
    assert error.value.code == "archive_members"


def test_symlink_encryption_duplicate_and_extra_members_rejected(documents):
    model, raw, report = documents
    info = zipfile.ZipInfo("model.onnx")
    info.create_system = 3
    info.external_attr = (stat.S_IFLNK | 0o777) << 16
    with pytest.raises(ContractError, match="regular"):
        validate_package(archive(model, raw, report, info=info))
    buf = io.BytesIO(archive(model, raw, report))
    with zipfile.ZipFile(buf, "a") as z:
        z.writestr("notes.txt", "extra")
    with pytest.raises(ContractError):
        validate_package(buf.getvalue())
    with pytest.warns(UserWarning):
        buf = io.BytesIO(archive(model, raw, report))
        with zipfile.ZipFile(buf, "a") as z:
            z.writestr("model.onnx", model)
    with pytest.raises(ContractError):
        validate_package(buf.getvalue())
    data = bytearray(archive(model, raw, report))
    data[6] |= 1
    center = data.index(b"PK\x01\x02")
    data[center + 8] |= 1
    with pytest.raises(ContractError):
        validate_package(bytes(data))


@pytest.mark.parametrize("limit", ["archive", "model", "json", "expanded"])
def test_configured_limits_reject_before_worker(documents, limit, monkeypatch):
    from graphene_model_contract import package

    monkeypatch.setattr(
        package,
        "_run_worker",
        lambda *_: pytest.fail("Native execution must not start"),
    )
    model, raw, report = documents
    kwargs = {
        "archive": {"archive_bytes": 20},
        "model": {"model_bytes": 20},
        "json": {"json_bytes": 20},
        "expanded": {"expanded_bytes": 20},
    }[limit]
    with pytest.raises(ContractError) as error:
        validate_package(archive(model, raw, report), ValidationLimits(**kwargs))
    assert error.value.code in ("archive_limit", "expanded_limit")


def test_compressed_expansion_crc_and_checksum_failures(documents):
    model, raw, report = documents
    with pytest.raises(ContractError) as error:
        validate_package(
            archive(b"0" * 100000, raw, report, compression=zipfile.ZIP_DEFLATED),
            ValidationLimits(model_bytes=500),
        )
    assert error.value.code == "expanded_limit"
    damaged = bytearray(archive(model, raw, report))
    offset = damaged.index(model)
    damaged[offset] ^= 1
    with pytest.raises(ContractError) as error:
        validate_package(bytes(damaged))
    assert error.value.code == "archive_integrity"
    raw["artifact"]["sha256"] = report["model_sha256"] = "0" * 64
    with pytest.raises(ContractError) as error:
        validate_package(archive(model, raw, report))
    assert error.value.code == "checksum_mismatch"


@pytest.mark.parametrize(
    "damage",
    ["binary", "dynamic", "external", "domain", "subgraph", "huge", "nan", "malformed"],
)
def test_onnx_graph_rejections(documents, damage, tmp_path, monkeypatch):
    import tempfile

    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    model, raw, report = documents
    graph = onnx.load_model_from_string(model)
    expected = "graph_invalid"
    if damage == "binary":
        graph.graph.output[0].type.tensor_type.shape.dim[1].dim_value = 1
        expected = "graph_interface"
    elif damage == "dynamic":
        graph.graph.input[0].type.tensor_type.shape.dim[2].dim_param = "height"
        expected = "graph_interface"
    elif damage == "external":
        tensor = helper.make_tensor("unread", TensorProto.FLOAT, [1], [0.0])
        tensor.ClearField("float_data")
        tensor.data_location = TensorProto.EXTERNAL
        tensor.external_data.add(key="location", value="/private/secret.bin")
        graph.graph.initializer.append(tensor)
        expected = "external_data"
    elif damage == "domain":
        graph.graph.node[0].domain = "private.custom"
        expected = "unsupported_graph"
    elif damage == "subgraph":
        graph.graph.node[0].attribute.append(
            helper.make_attribute("hidden", helper.make_graph([], "nested", [], []))
        )
        expected = "unsupported_graph"
    elif damage == "huge":
        tensor = TensorProto()
        tensor.name = "huge"
        tensor.data_type = TensorProto.FLOAT
        tensor.dims.extend([1_000_000_000])
        graph.graph.initializer.append(tensor)
        expected = "tensor_limit"
    elif damage == "nan":
        graph.graph.node.clear()
        graph.graph.node.append(
            helper.make_node(
                "Constant",
                [],
                ["logits"],
                value=helper.make_tensor(
                    "nan", TensorProto.FLOAT, [1, 3, 32, 32], [float("nan")] * 3072
                ),
            )
        )
        expected = "invalid_logits"
    model, raw, report = changed_graph(documents, graph)
    if damage == "malformed":
        model = b"not-a-protobuf"
        raw["artifact"]["size"] = len(model)
        raw["artifact"]["sha256"] = report["model_sha256"] = hashlib.sha256(
            model
        ).hexdigest()
    with pytest.raises(ContractError) as error:
        validate_package(archive(model, raw, report))
    assert error.value.code == expected
    assert "/private/" not in str(error.value)
    assert list(tmp_path.iterdir()) == []


def test_worker_timeout_termination_and_temporary_cleanup(
    documents, tmp_path, monkeypatch
):
    import tempfile

    monkeypatch.setattr(tempfile, "tempdir", str(tmp_path))
    original = subprocess.Popen
    workers = []

    def capture_worker(*args, **kwargs):
        process = original(*args, **kwargs)
        workers.append(process)
        return process

    monkeypatch.setattr(subprocess, "Popen", capture_worker)
    model, raw, report = documents
    with pytest.raises(ContractError) as error:
        validate_package(
            archive(model, raw, report), ValidationLimits(wall_seconds=0.001)
        )
    assert error.value.code == "validation_timeout"
    assert list(tmp_path.iterdir()) == []
    assert workers and all(process.poll() is not None for process in workers)


def test_worker_memory_failure_is_bounded(documents):
    model, raw, report = documents
    with pytest.raises(ContractError) as error:
        validate_package(
            archive(model, raw, report),
            ValidationLimits(address_bytes=32 * 1024 * 1024),
        )
    assert error.value.code in ("resource_limit", "worker_failed", "graph_invalid")


def test_zip_directory_cannot_allocate_an_unbounded_entry_list(documents, monkeypatch):
    model, raw, report = documents
    data = bytearray(archive(model, raw, report))
    end = data.rfind(b"PK\x05\x06")
    data[end + 10 : end + 12] = (65535).to_bytes(2, "little")
    monkeypatch.setattr(
        zipfile,
        "ZipFile",
        lambda *_: pytest.fail("Central directory must be rejected first"),
    )
    with pytest.raises(ContractError) as error:
        validate_package(bytes(data))
    assert error.value.code == "archive_members"


@pytest.mark.parametrize(
    "mode,hw",
    [
        ("letterbox", (32, 32)),
        ("letterbox", (17, 32)),
        ("letterbox", (32, 17)),
        ("tiles", (33, 49)),
    ],
)
def test_consumer_actual_cpu_graph_and_original_coordinate_masks(documents, mode, hw):
    import onnxruntime as ort
    from graphene_model_contract.geometry import (
        TileAccumulator,
        decide,
        prepare_letterbox,
        prepare_tiles,
        restore_letterbox,
    )

    model, raw, report = documents
    if mode == "tiles":
        raw["geometry"] = report["geometry"] = {
            "mode": "tiles",
            "version": 1,
            "stride": [16, 16],
            "merge": "mean_logits",
        }
    manifest, evaluation = parse_contract(
        json.dumps(raw).encode(), json.dumps(report).encode()
    )
    accepted = validate_package(build_package(model, manifest, evaluation))
    options = ort.SessionOptions()
    options.intra_op_num_threads = options.inter_op_num_threads = 1
    # Only our tiny known Identity graph is run here; uploaded graphs use the bounded child.
    session = ort.InferenceSession(
        accepted.model_bytes, sess_options=options, providers=["CPUExecutionProvider"]
    )
    y, x = np.indices(hw)
    rgb = np.stack(
        ((x * 8) % 256, (y * 16) % 256, ((x + y) * 6) % 256), axis=-1
    ).astype(np.uint8)
    if mode == "letterbox":
        prepared = prepare_letterbox(rgb, accepted.manifest)
        output = session.run(["logits"], {"rgb": prepared.tensor})[0]
        restored = restore_letterbox(output, prepared.geometry)
    else:
        accumulated = TileAccumulator(hw, accepted.manifest)
        for prepared in prepare_tiles(rgb, accepted.manifest):
            output = session.run(["logits"], {"rgb": prepared.tensor})[0]
            accumulated.add(output, prepared.geometry)
        restored = accumulated.finish()
    # Original uint8 pixel channels independently determine our Identity graph's classes.
    expected = np.empty(hw, np.uint8)
    for row in range(hw[0]):
        for col in range(hw[1]):
            expected[row, col] = max(
                range(3), key=lambda channel: int(rgb[row, col, channel])
            )
    np.testing.assert_array_equal(decide(restored, accepted.manifest), expected)
