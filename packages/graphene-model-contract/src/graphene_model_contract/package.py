"""Bounded ZIP contract validation and producer bundling; no extraction paths."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import hashlib
import io
import json
import math
import os
from pathlib import Path
import stat
import struct
import subprocess
import sys
import tempfile
import zipfile

from .contract import Evaluation, Manifest, parse_contract
from .errors import ContractError

MiB = 1024 * 1024
MEMBERS = {"model.onnx", "manifest.json", "evaluation.json"}


@dataclass(frozen=True)
class ValidationLimits:
    archive_bytes: int = 256 * MiB
    model_bytes: int = 256 * MiB
    json_bytes: int = MiB
    expanded_bytes: int = 258 * MiB
    wall_seconds: float = 30
    cpu_seconds: int = 20
    address_bytes: int = 4 * 1024 * MiB
    nodes: int = 10_000
    tensor_bytes: int = 512 * MiB

    def __post_init__(self):
        for name, value in asdict(self).items():
            if (
                isinstance(value, bool)
                or not isinstance(value, (int, float))
                or not math.isfinite(value)
                or value <= 0
                or (name != "wall_seconds" and type(value) is not int)
            ):
                raise ValueError(
                    "Validation bounds must be positive finite values; sizes/counts are integers"
                )


@dataclass(frozen=True)
class ValidatedPackage:
    manifest: Manifest
    evaluation: Evaluation
    model_bytes: bytes
    bundle_sha256: str
    smoke: dict

    @property
    def evidence_kind(self) -> str:
        return self.evaluation.evidence.kind


def _archive_members(data: bytes, limits: ValidationLimits) -> dict[str, bytes]:
    if len(data) > limits.archive_bytes:
        raise ContractError(
            "archive_limit", "Package exceeds the configured archive limit."
        )
    # Bound central-directory parsing before ZipFile allocates an entry list.
    end = data.rfind(b"PK\x05\x06", max(0, len(data) - 65557))
    if end < 0 or end + 22 > len(data) or not data.startswith(b"PK\x03\x04"):
        raise ContractError(
            "archive_integrity", "Package is not a supported ZIP archive."
        )
    _, disk, directory_disk, count_disk, count, directory_size, offset, comment = (
        struct.unpack("<4s4H2IH", data[end : end + 22])
    )
    if (
        disk
        or directory_disk
        or count_disk != 3
        or count != 3
        or directory_size > MiB
        or offset + directory_size != end
        or end + 22 + comment != len(data)
    ):
        raise ContractError(
            "archive_members",
            "ZIP directory must describe exactly three bounded root members.",
        )
    try:
        with zipfile.ZipFile(io.BytesIO(data)) as archive:
            infos = archive.infolist()
            if len(infos) != 3 or {info.filename for info in infos} != MEMBERS:
                raise ContractError(
                    "archive_members",
                    "Package must contain exactly the three declared root files.",
                )
            total = 0
            result = {}
            for info in infos:
                mode = (info.external_attr >> 16) & 0xFFFF
                if (
                    info.is_dir()
                    or info.flag_bits & 1
                    or (stat.S_IFMT(mode) not in (0, stat.S_IFREG))
                    or info.compress_type
                    not in (zipfile.ZIP_STORED, zipfile.ZIP_DEFLATED)
                ):
                    raise ContractError(
                        "archive_members",
                        "Archive members must be regular, unencrypted supported files.",
                    )
                bound = (
                    limits.model_bytes
                    if info.filename == "model.onnx"
                    else limits.json_bytes
                )
                if (
                    info.file_size > bound
                    or total + info.file_size > limits.expanded_bytes
                ):
                    raise ContractError(
                        "expanded_limit",
                        "Expanded package exceeds the configured member/total limit.",
                    )
                chunks = []
                actual = 0
                with archive.open(info) as stream:
                    while chunk := stream.read(min(64 * 1024, bound + 1 - actual)):
                        actual += len(chunk)
                        if actual > bound or total + actual > limits.expanded_bytes:
                            raise ContractError(
                                "expanded_limit",
                                "Streamed member exceeds the configured expansion limit.",
                            )
                        chunks.append(chunk)
                if actual != info.file_size:
                    raise ContractError(
                        "archive_integrity", "Archive member size is inconsistent."
                    )
                total += actual
                result[info.filename] = b"".join(chunks)
            return result
    except (zipfile.BadZipFile, RuntimeError, EOFError, NotImplementedError, OSError):
        raise ContractError(
            "archive_integrity",
            "Package is malformed or failed archive integrity checks.",
        ) from None


def _run_worker(model: bytes, manifest: Manifest, limits: ValidationLimits) -> dict:
    # Child uses private files only, and has no stdout/stderr pipe to fill.
    with tempfile.TemporaryDirectory(prefix="graphene-contract-") as directory:
        root = Path(directory)
        (root / "model.onnx").write_bytes(model)
        (root / "job.json").write_text(
            json.dumps(
                {"manifest": manifest.model_dump(mode="json"), "limits": asdict(limits)}
            )
        )
        environment = os.environ.copy()
        environment.update(
            OPENBLAS_NUM_THREADS="1", OMP_NUM_THREADS="1", MKL_NUM_THREADS="1"
        )
        process = subprocess.Popen(
            [sys.executable, "-m", "graphene_model_contract._worker", str(root)],
            env=environment,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            try:
                process.wait(timeout=limits.wall_seconds)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
                raise ContractError(
                    "validation_timeout",
                    "CPU model validation exceeded its wall-time limit.",
                ) from None
            result = root / "result.json"
            if not result.is_file() or result.stat().st_size > 8192:
                raise ContractError(
                    "worker_failed",
                    "CPU validation worker stopped without a bounded result.",
                )
            response = json.loads(result.read_bytes())
            if process.returncode != 0 or not response.get("ok"):
                code = response.get("code", "worker_failed")
                public = {
                    "external_data",
                    "unsupported_graph",
                    "graph_interface",
                    "tensor_limit",
                    "graph_invalid",
                    "invalid_logits",
                    "invalid_normalization",
                    "resource_limit",
                    "missing_runtime",
                }
                if code not in public:
                    code = "worker_failed"
                raise ContractError(
                    code, f"CPU model validation rejected the artifact ({code})."
                )
            return response["smoke"]
        except ContractError:
            raise
        except (OSError, ValueError, KeyError, TypeError):
            raise ContractError(
                "worker_failed", "CPU validation worker returned an invalid result."
            ) from None
        finally:
            if process.poll() is None:
                process.kill()
                process.wait()


def validate_package(
    data: bytes, limits: ValidationLimits = ValidationLimits()
) -> ValidatedPackage:
    members = _archive_members(data, limits)
    manifest, evaluation = parse_contract(
        members["manifest.json"], members["evaluation.json"]
    )
    model = members["model.onnx"]
    if (
        len(model) != manifest.artifact.size
        or hashlib.sha256(model).hexdigest() != manifest.artifact.sha256
    ):
        raise ContractError(
            "checksum_mismatch",
            "Model byte size or SHA-256 disagrees with the manifest.",
        )
    smoke = _run_worker(model, manifest, limits)
    return ValidatedPackage(
        manifest, evaluation, model, hashlib.sha256(data).hexdigest(), smoke
    )


def validate_file(
    path: Path, limits: ValidationLimits = ValidationLimits()
) -> ValidatedPackage:
    with path.open("rb") as stream:
        data = stream.read(limits.archive_bytes + 1)
    return validate_package(data, limits)


def build_package(
    model: bytes,
    manifest: Manifest,
    evaluation: Evaluation,
    limits: ValidationLimits = ValidationLimits(),
) -> bytes:
    """Producer bundles an already exported ONNX graph, not a training checkpoint.

    Both producer and consumer independently validate before considering it usable.
    """
    if len(model) > limits.model_bytes:
        raise ContractError(
            "expanded_limit", "Exported model exceeds the configured member limit."
        )
    manifest_bytes = manifest.model_dump_json().encode()
    evaluation_bytes = evaluation.model_dump_json().encode()
    parse_contract(manifest_bytes, evaluation_bytes)
    if (
        len(model) != manifest.artifact.size
        or hashlib.sha256(model).hexdigest() != manifest.artifact.sha256
    ):
        raise ContractError(
            "checksum_mismatch",
            "Producer graph does not match declared identity/digest.",
        )
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", compression=zipfile.ZIP_STORED) as archive:
        for name, data in (
            ("model.onnx", model),
            ("manifest.json", manifest_bytes),
            ("evaluation.json", evaluation_bytes),
        ):
            archive.writestr(name, data)
    bundle = buffer.getvalue()
    validate_package(bundle, limits)
    return bundle
