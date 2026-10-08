"""Immutable local registry, atomic publication and selection.

Optional ONNX dependencies are imported only for an explicit validation action.
The service slot spans receiving, validating and publishing each mutation.
"""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
import os
from pathlib import Path
import sqlite3
import stat
import threading
import uuid

from app.services.workspace import GENERATED_STAGING, Workspace, WorkspaceError

ARCHIVE_BYTES = 256 * 1024 * 1024
UPLOAD_SECONDS = 60
INSTALL_ACTION = "Install model support: cd backend and run uv sync --locked --extra models --python 3.12."


class ModelError(Exception):
    def __init__(self, code: str, message: str, status: int = 422):
        self.code, self.message, self.status = code, message, status


def runtime_available() -> bool:
    try:
        return all(importlib.util.find_spec(name) is not None for name in
                   ("graphene_model_contract", "onnx", "onnxruntime"))
    except (ImportError, ValueError):
        return False


def validate(path: Path):
    if not runtime_available():
        raise ModelError("missing_runtime", INSTALL_ACTION, 503)
    from graphene_model_contract.errors import ContractError
    from graphene_model_contract.package import validate_file
    try:
        return validate_file(path)
    except ContractError as error:
        if error.code == "missing_runtime":
            raise ModelError(error.code, INSTALL_ACTION, 503) from None
        raise ModelError(error.code, f"{error} Check the package with its exporter and import a corrected ZIP.") from None


def check_cancelled(cancelled):
    if cancelled is not None and cancelled.is_set():
        raise ModelError("operation_interrupted", "Model check was interrupted. Refresh Models before retrying.", 400)


class LocalModels:
    def __init__(self, workspace: Workspace):
        self.workspace = workspace
        self.slot = threading.Lock()
        self.archive_bytes = ARCHIVE_BYTES
        self.upload_seconds = UPLOAD_SECONDS

    @contextmanager
    def mutation(self):
        if not self.slot.acquire(blocking=False):
            raise ModelError("busy", "Another model is being checked. Wait for it to finish, then retry.", 409)
        try:
            if not runtime_available():
                raise ModelError("missing_runtime", INSTALL_ACTION, 503)
            yield
        finally:
            self.slot.release()

    def staging_path(self) -> Path:
        if self.workspace.staging.is_symlink():
            raise WorkspaceError("Invalid staging directory.")
        return self.workspace.staging / f"{uuid.uuid4().hex}.tmp"

    def _rows(self, connection):
        return connection.execute("""SELECT m.*, a.relative_path, a.size, a.sha256, a.available
            FROM models m JOIN artifacts a ON a.id=m.artifact_id ORDER BY m.imported_at,m.model_id""").fetchall()

    def _public(self, row, selected, *, details=True):
        result = {key: row[key] for key in
                  ("model_id", "bundle_sha256", "model_sha256", "name", "version", "imported_at")}
        result.update(available=bool(row["available"]), selected=row["model_id"] == selected)
        documents = json.loads(row["documents"])
        result["evidence_kind"] = documents["evaluation"]["evidence"]["kind"]
        if details:
            result.update(documents)
        return result

    def list(self):
        store = self.workspace
        with store._thread_lock, store._connection() as connection:
            store._require_ready()
            rows = self._rows(connection)
            for row in rows:
                if row["available"] and not store._intact(row):
                    connection.execute("UPDATE artifacts SET available=0 WHERE id=?", (row["artifact_id"],))
            rows = self._rows(connection)
            selected = connection.execute("SELECT model_id FROM model_selection WHERE singleton=1").fetchone()[0]
            return {"models": [self._public(row, selected, details=False) for row in rows],
                    "selected_model_id": selected, "validation_available": runtime_available(),
                    "installation_action": INSTALL_ACTION}

    def detail(self, identity: str):
        # Refresh integrity, including while the app stays open.
        self.list()
        with self.workspace._thread_lock, self.workspace._connection() as connection:
            selected = connection.execute("SELECT model_id FROM model_selection WHERE singleton=1").fetchone()[0]
            row = next((row for row in self._rows(connection) if row["model_id"] == identity), None)
            if row is None:
                raise ModelError("unknown_model", "Model not found. Refresh Models and choose an imported model.", 404)
            return self._public(row, selected)

    def _commit_import(self, connection, artifact, checked, documents):
        connection.execute("""INSERT INTO artifacts(id,relative_path,size,sha256,created_at,metadata)
            VALUES(?,?,?,?,?,?)""", artifact)
        connection.execute("""INSERT INTO models VALUES(?,?,?,?,?,?,?,?)""",
                           (str(checked.manifest.model_id), artifact[0], checked.bundle_sha256,
                            checked.manifest.artifact.sha256, checked.manifest.name,
                            checked.manifest.model_version, artifact[4], json.dumps(documents, allow_nan=False)))

    def import_file(self, path: Path, cancelled=None):
        checked = validate(path)
        check_cancelled(cancelled)
        documents = {"manifest": checked.manifest.model_dump(mode="json"),
                     "evaluation": checked.evaluation.model_dump(mode="json"),
                     "validation": {"contract_version": 1, "cpu_smoke": checked.smoke}}
        store = self.workspace
        identity = str(checked.manifest.model_id)
        final = None
        created = False
        with store._thread_lock:
            store._require_ready()
            if path.parent != store.staging or not GENERATED_STAGING.fullmatch(path.name):
                raise WorkspaceError("Invalid staged model reference.")
            try:
                with store._connection() as connection:
                    connection.execute("BEGIN IMMEDIATE")
                    existing = connection.execute("SELECT bundle_sha256 FROM models WHERE model_id=?", (identity,)).fetchone()
                    if existing:
                        if existing[0] != checked.bundle_sha256:
                            raise ModelError("identity_conflict", "This model ID already has a different package. Export changed models with a new ID.", 409)
                    else:
                        descriptor = os.open(path, os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                        with os.fdopen(descriptor, "rb") as stream:
                            info = os.fstat(stream.fileno())
                            if not stat.S_ISREG(info.st_mode) or hashlib.file_digest(stream, "sha256").hexdigest() != checked.bundle_sha256:
                                raise WorkspaceError("Staged package changed. Import the ZIP again.")
                            os.fsync(stream.fileno())
                        artifact_id = uuid.uuid4().hex
                        relative = f"artifacts/{artifact_id}.bin"
                        final = store._artifact_path(relative)
                        os.replace(path, final)
                        store._sync_directory(store.artifacts)
                        timestamp = datetime.now(timezone.utc).isoformat()
                        check_cancelled(cancelled)
                        self._commit_import(connection, (artifact_id, relative, info.st_size,
                                            checked.bundle_sha256, timestamp, "{}"), checked, documents)
                        created = True
            except (OSError, sqlite3.Error, ModelError) as error:
                if final:
                    try:
                        final.unlink(missing_ok=True)
                    except OSError:
                        pass  # Startup recovers generated orphans.
                if isinstance(error, ModelError):
                    raise
                raise WorkspaceError("Model write failed. Check disk capacity and retry.") from None
        return self.detail(identity), created

    def select(self, identity: str, cancelled=None):
        record = self.detail(identity)
        if not record["available"]:
            raise ModelError("unavailable_model", "Model file is missing or damaged. Select another intact model or restore a workspace backup.", 409)
        store = self.workspace
        with store._connection() as connection:
            row = connection.execute("SELECT a.* FROM models m JOIN artifacts a ON a.id=m.artifact_id WHERE model_id=?", (identity,)).fetchone()
        checked = validate(store._artifact_path(row["relative_path"]))
        check_cancelled(cancelled)
        if checked.bundle_sha256 != record["bundle_sha256"]:
            raise ModelError("unavailable_model", "Model file changed. Restore a workspace backup or select another model.", 409)
        with store._thread_lock, store._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            if not store._intact(row):
                raise ModelError("unavailable_model", "Model file changed during checking. Select another model.", 409)
            check_cancelled(cancelled)
            connection.execute("UPDATE model_selection SET model_id=? WHERE singleton=1", (identity,))
        return self.list()
