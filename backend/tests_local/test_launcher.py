"""Real process smoke: the documented launcher with outbound access blocked."""
from __future__ import annotations

import json
import os
from pathlib import Path
import socket
import subprocess
import time
from urllib.request import urlopen

from app.services.workspace import Workspace

PROJECT = Path(__file__).resolve().parents[2]


def test_launcher_offline_start_restart_and_secret_free_logs(tmp_path):
    guard = tmp_path / "guard"
    guard.mkdir()
    (guard / "sitecustomize.py").write_text('''
import importlib.abc, socket, sys
class BlockLegacy(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split('.')[0] in {'supabase', 'torch', 'tensorflow', 'mlflow', 'jwt'}:
            raise AssertionError('Forbidden external/ML startup import')
sys.meta_path.insert(0, BlockLegacy())
original = socket.socket.connect
def local_only(sock, address):
    if sock.family in (socket.AF_INET, socket.AF_INET6) and address[0] not in ('127.0.0.1', '::1'):
        raise AssertionError('Outbound connection forbidden')
    return original(sock, address)
socket.socket.connect = local_only
socket.socket.connect_ex = lambda sock, address: (local_only(sock, address) or 0)
''')
    workspace = tmp_path / "data"
    with Workspace(workspace) as store:
        artifact = store.publish(b"restart fixture", {"origin": "launcher smoke"})
    with socket.socket() as temporary:
        temporary.bind(("127.0.0.1", 0))
        port = temporary.getsockname()[1]
    environment = os.environ.copy()
    for name in ("SUPABASE_URL", "SUPABASE_KEY", "JWT_SECRET"):
        environment.pop(name, None)
    environment.update(GRAPHENE_WORKSPACE_DIR=str(workspace), GRAPHENE_PORT=str(port),
                       PYTHONPATH=f"{guard}:{PROJECT / 'backend'}")
    for iteration in range(2):
        if iteration:
            for name in ("SUPABASE_URL", "SUPABASE_KEY", "JWT_SECRET"):
                environment[name] = "SMOKE_SECRET_DO_NOT_LOG"
        log_path = tmp_path / f"server-{iteration}.log"
        with log_path.open("w") as log:
            process = subprocess.Popen([str(PROJECT / "scripts/start-local.sh")], cwd=PROJECT,
                                       env=environment, stdout=log, stderr=log)
            try:
                deadline = time.monotonic() + 10
                while time.monotonic() < deadline:
                    assert process.poll() is None, log_path.read_text()
                    try:
                        with urlopen(f"http://127.0.0.1:{port}/health", timeout=1) as response:
                            health = json.load(response)
                        break
                    except OSError:
                        time.sleep(0.05)
                else:
                    raise AssertionError("Local launcher did not become ready")
                assert health["storage_ready"] and not health["model_loaded"]
                with urlopen(f"http://127.0.0.1:{port}/", timeout=1) as response:
                    assert "Graphene Workspace" in response.read().decode()
            finally:
                process.terminate()
                process.wait(timeout=10)
        logs = log_path.read_text()
        assert "127.0.0.1" in logs
        assert "SMOKE_SECRET" not in logs
        assert "Forbidden" not in logs and "Traceback" not in logs
        with Workspace(workspace) as store:
            assert store.read(artifact.id) == b"restart fixture"


def test_launcher_explains_missing_frontend_assets(tmp_path):
    script = tmp_path / "scripts/start-local.sh"
    script.parent.mkdir()
    script.write_bytes((PROJECT / "scripts/start-local.sh").read_bytes())
    script.chmod(0o755)
    result = subprocess.run([str(script)], capture_output=True, text=True)
    assert result.returncode == 1
    assert "Frontend assets are missing" in result.stderr
    assert "npm run build" in result.stderr
