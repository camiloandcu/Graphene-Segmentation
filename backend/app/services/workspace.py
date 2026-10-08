"""Durable metadata and opaque artifacts for one local server.

An artifact is not a validated model. Publish files before committing metadata;
exclusive startup recovery handles the gap between filesystem and SQLite.
"""
from __future__ import annotations

import fcntl
import hashlib
import json
import logging
import os
import re
import sqlite3
import stat
import threading
import uuid
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterator

logger = logging.getLogger(__name__)
SCHEMA_VERSION = 1
GENERATED_ARTIFACT = re.compile(r"[0-9a-f]{32}\.bin\Z")
GENERATED_STAGING = re.compile(r"[0-9a-f]{32}\.tmp\Z")


class WorkspaceError(RuntimeError):
    """Operator-safe message without internal paths or contents."""


@dataclass(frozen=True)
class Artifact:
    id: str
    relative_path: str
    size: int
    sha256: str
    created_at: str
    metadata: dict[str, Any]


class Workspace:
    def __init__(self, root: Path):
        self.root = root.expanduser().resolve()
        self.artifacts = self.root / "artifacts"
        self.staging = self.root / "staging"
        self.database = self.root / "workspace.sqlite3"
        self._lock_file = None
        self._thread_lock = threading.RLock()
        self.ready = False

    def open(self) -> "Workspace":
        with self._thread_lock:
            if self.ready:
                return self
            try:
                self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
                descriptor = os.open(self.root / ".workspace.lock", os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW, 0o600)
                self._lock_file = os.fdopen(descriptor, "a+")
                try:
                    fcntl.flock(self._lock_file, fcntl.LOCK_EX | fcntl.LOCK_NB)
                except BlockingIOError:
                    raise WorkspaceError("Workspace is already open. Stop the other server first.") from None
                for folder in (self.artifacts, self.staging):
                    if folder.is_symlink():
                        raise WorkspaceError("Workspace storage directories cannot be symbolic links.")
                    folder.mkdir(exist_ok=True, mode=0o700)
                if self.database.is_symlink():
                    raise WorkspaceError("Workspace database cannot be a symbolic link.")
                self._initialize_schema()
                self._recover()
                self.ready = True
                logger.info("Local workspace initialized (schema %d).", SCHEMA_VERSION)
                return self
            except WorkspaceError:
                self.close()
                raise
            except (OSError, sqlite3.Error):
                self.close()
                raise WorkspaceError("Cannot initialize workspace. Check local disk permissions and capacity.") from None

    def close(self) -> None:
        with self._thread_lock:
            self.ready = False
            if self._lock_file:
                self._lock_file.close()  # Never unlink the lock inode.
                self._lock_file = None

    def __enter__(self) -> "Workspace":
        return self.open()

    def __exit__(self, *_args) -> None:
        self.close()

    @contextmanager
    def _connection(self) -> Iterator[sqlite3.Connection]:
        connection = sqlite3.connect(self.database)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA synchronous = FULL")
        try:
            with connection:
                yield connection
        finally:
            connection.close()

    def _initialize_schema(self) -> None:
        with self._connection() as connection:
            connection.execute("BEGIN IMMEDIATE")
            version = connection.execute("PRAGMA user_version").fetchone()[0]
            if version not in (0, SCHEMA_VERSION):
                raise WorkspaceError("Unsupported workspace schema. Use a compatible application version.")
            if version == 0:
                tables = connection.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()
                if tables:
                    raise WorkspaceError("Unrecognized database. Choose a new workspace directory.")
                connection.execute("""CREATE TABLE artifacts (
                    id TEXT PRIMARY KEY, relative_path TEXT NOT NULL UNIQUE,
                    size INTEGER NOT NULL CHECK(size >= 0), sha256 TEXT NOT NULL,
                    created_at TEXT NOT NULL, metadata TEXT NOT NULL,
                    available INTEGER NOT NULL DEFAULT 1 CHECK(available IN (0, 1))
                )""")
                connection.execute(f"PRAGMA user_version = {SCHEMA_VERSION}")
        self._sync_directory(self.root)

    @staticmethod
    def _sync_directory(folder: Path) -> None:
        descriptor = os.open(folder, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(descriptor)
        finally:
            os.close(descriptor)

    def _artifact_path(self, relative: str) -> Path:
        path = Path(relative)
        if len(path.parts) != 2 or path.parts[0] != "artifacts" or not GENERATED_ARTIFACT.fullmatch(path.parts[1]):
            raise WorkspaceError("Invalid artifact reference.")
        if self.artifacts.is_symlink():
            raise WorkspaceError("Invalid artifact storage directory.")
        return self.root / path

    def _intact(self, record: sqlite3.Row) -> bool:
        try:
            descriptor = os.open(self._artifact_path(record["relative_path"]), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
            with os.fdopen(descriptor, "rb") as stream:
                info = os.fstat(stream.fileno())
                if not stat.S_ISREG(info.st_mode) or info.st_size != record["size"]:
                    return False
                return hashlib.file_digest(stream, "sha256").hexdigest() == record["sha256"]
        except (OSError, WorkspaceError):
            return False

    def _recover(self) -> None:
        with self._connection() as connection:
            records = connection.execute("SELECT * FROM artifacts").fetchall()
            referenced = {record["relative_path"] for record in records}
            invalid = 0
            for record in records:
                if not self._intact(record):
                    connection.execute("UPDATE artifacts SET available=0 WHERE id=?", (record["id"],))
                    invalid += 1
            removed = 0
            for folder, pattern in ((self.artifacts, GENERATED_ARTIFACT), (self.staging, GENERATED_STAGING)):
                for path in folder.iterdir():
                    relative = path.relative_to(self.root).as_posix()
                    if pattern.fullmatch(path.name) and relative not in referenced and not path.is_symlink() and path.is_file():
                        path.unlink()
                        removed += 1
                self._sync_directory(folder)
        if removed or invalid:
            logger.warning("Workspace recovery: %d orphan files removed; %d artifacts unavailable.", removed, invalid)

    def _insert(self, artifact: Artifact) -> None:
        with self._connection() as connection:
            connection.execute(
                "INSERT INTO artifacts(id,relative_path,size,sha256,created_at,metadata) VALUES(?,?,?,?,?,?)",
                (artifact.id, artifact.relative_path, artifact.size, artifact.sha256,
                 artifact.created_at, json.dumps(artifact.metadata, allow_nan=False)),
            )

    def publish(self, data: bytes, metadata: dict[str, Any] | None = None) -> Artifact:
        with self._thread_lock:
            self._require_ready()
            if self.staging.is_symlink():
                raise WorkspaceError("Invalid staging directory.")
            clean_metadata = json.loads(json.dumps(metadata or {}, allow_nan=False))
            identity = uuid.uuid4().hex
            artifact = Artifact(identity, f"artifacts/{identity}.bin", len(data), hashlib.sha256(data).hexdigest(),
                                datetime.now(timezone.utc).isoformat(), clean_metadata)
            temporary = self.staging / f"{identity}.tmp"
            final = self._artifact_path(artifact.relative_path)
            try:
                with temporary.open("xb") as stream:
                    stream.write(data)
                    stream.flush()
                    os.fsync(stream.fileno())
                os.replace(temporary, final)
                self._sync_directory(self.artifacts)
                self._insert(artifact)
            except (OSError, sqlite3.Error):
                for path in (temporary, final):
                    try:
                        path.unlink(missing_ok=True)
                    except OSError:
                        pass  # Exclusive startup recovery handles generated orphans.
                raise WorkspaceError("Artifact write failed. Check disk capacity and retry.") from None
            return artifact

    def _require_ready(self) -> None:
        if not self.ready:
            raise WorkspaceError("Workspace is not initialized.")

    def lookup(self, identity: str) -> Artifact | None:
        with self._thread_lock:
            self._require_ready()
            with self._connection() as connection:
                record = connection.execute("SELECT * FROM artifacts WHERE id=? AND available=1", (identity,)).fetchone()
                if record is None:
                    return None
                if not self._intact(record):
                    connection.execute("UPDATE artifacts SET available=0 WHERE id=?", (identity,))
                    logger.warning("Artifact unavailable: integrity verification failed.")
                    return None
                return Artifact(record["id"], record["relative_path"], record["size"], record["sha256"],
                                record["created_at"], json.loads(record["metadata"]))

    def read(self, identity: str) -> bytes:
        with self._thread_lock:
            artifact = self.lookup(identity)
            if artifact is None:
                raise WorkspaceError("Artifact is unavailable.")
            try:
                descriptor = os.open(self._artifact_path(artifact.relative_path), os.O_RDONLY | os.O_NOFOLLOW | os.O_NONBLOCK)
                with os.fdopen(descriptor, "rb") as stream:
                    if not stat.S_ISREG(os.fstat(stream.fileno()).st_mode):
                        raise WorkspaceError("Artifact is unavailable.")
                    data = stream.read()
            except OSError:
                raise WorkspaceError("Artifact is unavailable.") from None
            if hashlib.sha256(data).hexdigest() != artifact.sha256:
                raise WorkspaceError("Artifact is unavailable.")
            return data
