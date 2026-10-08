from __future__ import annotations

import importlib.abc
from pathlib import Path
import socket
import subprocess
import sys

from fastapi.testclient import TestClient
import pytest

from app.core.local_config import LocalSettings
from app.main import create_app
from app.services.workspace import Workspace


def test_health_frontend_no_accounts_or_cloud(tmp_path, monkeypatch, caplog):
    for key in ("SUPABASE_URL", "SUPABASE_KEY", "JWT_SECRET"):
        monkeypatch.setenv(key, "SECRET_VALUE_MUST_NOT_BE_LOGGED")
    def no_outbound(*_args, **_kwargs):
        raise AssertionError("Outbound network access attempted")
    monkeypatch.setattr(socket, "create_connection", no_outbound)
    frontend = tmp_path / "frontend"
    frontend.mkdir()
    (frontend / "index.html").write_text("<html>Local fixture</html>")
    app = create_app(LocalSettings(tmp_path / "data", frontend))
    with TestClient(app) as client:
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json() == {"status": "ok", "runtime": "local", "storage_ready": True,
                                   "schema_version": 1, "model_loaded": False, "model_framework": None}
        assert client.get("/").status_code == 200
        assert client.post("/auth/login", json={}).status_code == 405
        assert client.get("/registry/models").status_code == 404
        record = app.state.workspace.publish(b"fixture")
    assert not app.state.workspace.ready
    with TestClient(create_app(LocalSettings(tmp_path / "data", frontend))) as client:
        assert client.app.state.workspace.read(record.id) == b"fixture"
    assert "SECRET_VALUE" not in caplog.text
    assert not any(name in sys.modules for name in ("supabase", "torch", "tensorflow", "app.core.supabase_client"))


def test_cors_only_documented_loopback_origins(tmp_path):
    with TestClient(create_app(LocalSettings(tmp_path, tmp_path / "no-assets"))) as client:
        allowed = client.get("/health", headers={"Origin": "http://127.0.0.1:3000"})
        assert allowed.headers["access-control-allow-origin"] == "http://127.0.0.1:3000"
        assert "access-control-allow-credentials" not in allowed.headers
        denied = client.get("/health", headers={"Origin": "https://example.com"})
        assert "access-control-allow-origin" not in denied.headers


def test_failed_initialization_does_not_start_healthy_app(tmp_path):
    blocked = tmp_path / "not-a-directory"
    blocked.write_text("preserve")
    with pytest.raises(RuntimeError, match="Cannot initialize workspace") as error:
        with TestClient(create_app(LocalSettings(blocked, tmp_path / "absent"))):
            pytest.fail("Startup should fail")
    assert str(tmp_path) not in str(error.value)
    assert blocked.read_text() == "preserve"


def test_local_config_ignores_cloud_env_and_resolves_frontend(monkeypatch, tmp_path):
    monkeypatch.delenv("GRAPHENE_WORKSPACE_DIR", raising=False)
    monkeypatch.setenv("XDG_DATA_HOME", str(tmp_path))
    settings = LocalSettings.from_environment()
    assert settings.workspace_dir == tmp_path / "graphene-segmentation"
    assert settings.frontend_dir == Path(__file__).resolve().parents[2] / "frontend/dist"


def test_fresh_interpreter_blocks_legacy_imports_and_network(tmp_path):
    script = '''
import importlib.abc, socket, sys
from pathlib import Path
class BlockLegacy(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'supabase', 'torch', 'tensorflow', 'mlflow', 'jwt'} or fullname.startswith('app.api.routes'):
            raise AssertionError('Forbidden startup import: ' + fullname)
sys.meta_path.insert(0, BlockLegacy())
def blocked(*args, **kwargs):
    raise AssertionError('Outbound connection attempted')
socket.socket.connect = blocked
socket.socket.connect_ex = blocked
from app.core.local_config import LocalSettings
from app.main import create_app
from fastapi.testclient import TestClient
with TestClient(create_app(LocalSettings(Path(sys.argv[1]), Path(sys.argv[1])/'absent'))) as client:
    assert client.get('/health').json()['storage_ready']
print('isolated startup passed')
'''
    result = subprocess.run([sys.executable, "-c", script, str(tmp_path)], text=True, capture_output=True)
    assert result.returncode == 0, result.stderr
    assert "isolated startup passed" in result.stdout
