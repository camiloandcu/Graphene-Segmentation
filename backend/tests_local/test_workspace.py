from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import sqlite3
import subprocess
import sys
import textwrap
from contextlib import contextmanager

import pytest

from app.services.workspace import Workspace, WorkspaceError


def test_committed_bytes_survive_restart_and_relocation(tmp_path):
    original = tmp_path / "original"
    with Workspace(original) as store:
        artifact = store.publish(b"opaque fixture\x00", {"name": "../../outside.bin", "purpose": "fixture"})
        assert store.read(artifact.id) == b"opaque fixture\x00"
        assert not Path(artifact.relative_path).is_absolute()
    copy = tmp_path / "restored"
    shutil.copytree(original, copy)
    with Workspace(copy) as store:
        assert store.lookup(artifact.id) == artifact
        assert store.read(artifact.id) == b"opaque fixture\x00"
    assert not (tmp_path / "outside.bin").exists()


@pytest.mark.parametrize("boundary", ["replace", "sync", "file-sync", "commit"])
def test_failed_publish_has_no_usable_record(tmp_path, monkeypatch, boundary):
    with Workspace(tmp_path) as store:
        def fail(*_args):
            raise sqlite3.OperationalError("private secret path") if boundary == "commit" else OSError("disk full")
        with monkeypatch.context() as patch:
            if boundary == "replace":
                patch.setattr(os, "replace", fail)
            elif boundary == "sync":
                patch.setattr(store, "_sync_directory", fail)
            elif boundary == "file-sync":
                patch.setattr(os, "fsync", fail)
            else:
                patch.setattr(store, "_insert", fail)
            with pytest.raises(WorkspaceError, match="Artifact write failed") as error:
                store.publish(b"failed")
            assert "secret" not in str(error.value)
        with sqlite3.connect(store.database) as connection:
            assert connection.execute("SELECT count(*) FROM artifacts").fetchone()[0] == 0
        assert not list(store.artifacts.iterdir())
        assert not list(store.staging.iterdir())
        good = store.publish(b"retry")
        assert store.read(good.id) == b"retry"


def test_failure_after_metadata_insert_rolls_back_transaction(tmp_path, monkeypatch):
    with Workspace(tmp_path) as store:
        @contextmanager
        def interrupted_commit():
            connection = sqlite3.connect(store.database)
            try:
                yield connection
                # Insertion has really happened, but the transaction cannot commit.
                connection.rollback()
                raise sqlite3.OperationalError("injected commit failure")
            finally:
                connection.close()
        with monkeypatch.context() as patch:
            patch.setattr(store, "_connection", interrupted_commit)
            with pytest.raises(WorkspaceError):
                store.publish(b"transaction fixture")
        with sqlite3.connect(store.database) as connection:
            assert connection.execute("SELECT count(*) FROM artifacts").fetchone()[0] == 0
        assert not list(store.artifacts.iterdir())


@pytest.mark.parametrize("boundary", ["staging", "published", "committed"])
def test_real_process_interruption_and_recovery(tmp_path, boundary):
    # A separate interpreter exits without context cleanup at each durability boundary.
    script = textwrap.dedent("""
        import os, sys
        from pathlib import Path
        from app.services.workspace import Workspace
        store = Workspace(Path(sys.argv[1])).open()
        if sys.argv[2] == 'staging':
            (store.staging / ('a' * 32 + '.tmp')).write_bytes(b'incomplete')
            os._exit(23)
        if sys.argv[2] == 'published':
            store._insert = lambda artifact: os._exit(23)
        result = store.publish(b'persisted', {'source': 'process fixture'})
        (store.root / 'fixture-id.txt').write_text(result.id)
        os._exit(23)
    """)
    result = subprocess.run([sys.executable, "-c", script, str(tmp_path), boundary], capture_output=True)
    assert result.returncode == 23, result.stderr.decode()
    unrelated = tmp_path / "artifacts" / "operator-notes.txt"
    unrelated.write_text("preserve this")
    with Workspace(tmp_path) as store:
        assert not list(store.staging.glob("*.tmp"))
        if boundary == "committed":
            identity = (tmp_path / "fixture-id.txt").read_text()
            assert store.read(identity) == b"persisted"
        else:
            assert not list(store.artifacts.glob("*.bin"))
        assert unrelated.read_text() == "preserve this"


@pytest.mark.parametrize("damage", ["missing", "corrupt", "symlink", "fifo"])
def test_damaged_artifact_is_never_usable(tmp_path, damage):
    with Workspace(tmp_path) as store:
        artifact = store.publish(b"good")
    path = tmp_path / artifact.relative_path
    path.unlink()
    if damage == "corrupt":
        path.write_bytes(b"evil")  # same size: checksum must detect damage
    elif damage == "symlink":
        external = tmp_path / "outside"
        external.write_bytes(b"good")
        path.symlink_to(external)
    elif damage == "fifo":
        os.mkfifo(path)
    with Workspace(tmp_path) as store:
        assert store.lookup(artifact.id) is None
        with pytest.raises(WorkspaceError, match="unavailable"):
            store.read(artifact.id)
    if damage == "missing":
        assert not path.exists()


def test_second_writer_cannot_recover_first_writers_workspace(tmp_path):
    with Workspace(tmp_path) as first:
        second = Workspace(tmp_path)
        with pytest.raises(WorkspaceError, match="already open"):
            second.open()
        # The rejected writer must not accidentally release the first one's lock.
        with pytest.raises(WorkspaceError, match="already open"):
            Workspace(tmp_path).open()
        artifact = first.publish(b"first writer")
    with Workspace(tmp_path) as third:
        assert third.read(artifact.id) == b"first writer"


def test_newer_schema_is_rejected_without_modification(tmp_path):
    with Workspace(tmp_path) as store:
        artifact = store.publish(b"preserved")
    with sqlite3.connect(tmp_path / "workspace.sqlite3") as connection:
        connection.execute("PRAGMA user_version = 99")
    with pytest.raises(WorkspaceError, match="Unsupported workspace schema"):
        Workspace(tmp_path).open()
    with sqlite3.connect(tmp_path / "workspace.sqlite3") as connection:
        assert connection.execute("PRAGMA user_version").fetchone()[0] == 99
        assert connection.execute("SELECT id FROM artifacts").fetchone()[0] == artifact.id


def test_path_escape_and_replaced_staging_directory(tmp_path):
    outside = tmp_path / "external"
    outside.mkdir()
    with Workspace(tmp_path / "workspace") as store:
        for path in ["../external", "/etc/passwd", "artifacts/../../external", "artifacts/name.bin"]:
            with pytest.raises(WorkspaceError, match="Invalid artifact reference"):
                store._artifact_path(path)
        store.staging.rmdir()
        store.staging.symlink_to(outside, target_is_directory=True)
        with pytest.raises(WorkspaceError, match="Invalid staging"):
            store.publish(b"escape")
        assert not list(outside.iterdir())


def test_integrity_loss_during_running_session(tmp_path):
    with Workspace(tmp_path) as store:
        artifact = store.publish(b"fixture")
        (tmp_path / artifact.relative_path).unlink()
        assert store.lookup(artifact.id) is None
        assert not (tmp_path / artifact.relative_path).exists()
