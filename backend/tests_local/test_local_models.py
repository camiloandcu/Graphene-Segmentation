from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sqlite3
import subprocess
import sys
import threading
import zipfile

from fastapi.testclient import TestClient
import pytest
from starlette.requests import Request, ClientDisconnect

from app.core.local_config import LocalSettings
from app.main import create_app
from app.services import local_models, local_schema
from app.services.workspace import Workspace, WorkspaceError

pytest.importorskip('onnx')
spec = importlib.util.spec_from_file_location('wi04_exporter', Path(__file__).parents[2] /
                                           'packages/graphene-model-contract/examples/make_synthetic_package.py')
exporter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(exporter)


def bundle(model, manifest, evaluation):
    output = io.BytesIO()
    with zipfile.ZipFile(output, 'w') as archive:
        for name, contents in [('model.onnx', model), ('manifest.json', json.dumps(manifest).encode()),
                               ('evaluation.json', json.dumps(evaluation).encode())]:
            archive.writestr(name, contents)
    return output.getvalue()


@pytest.fixture
def packages():
    model = exporter.identity_graph()
    manifest, evaluation = exporter.fixture_documents(model)
    other, other_eval = exporter.fixture_documents(model)
    other['name'] = 'Second synthetic model'
    return bundle(model, manifest, evaluation), bundle(model, other, other_eval), model, manifest, evaluation


def app_at(root):
    return create_app(LocalSettings(root, root / 'no-frontend'))


def upload(client, data):
    return client.post('/api/models/import', content=data, headers={'Content-Type': 'application/zip'})


def select(client, identity):
    return client.put('/api/models/selection', json={'model_id': identity})


def test_import_selection_details_restart_and_idempotence(tmp_path, packages):
    first, second, *_ = packages
    with TestClient(app_at(tmp_path)) as client:
        assert client.get('/api/models').json()['selected_model_id'] is None
        response = upload(client, first)
        assert response.status_code == 201
        model = response.json()['model']
        identity = model['model_id']
        assert model['bundle_sha256'] == hashlib.sha256(first).hexdigest()
        assert model['evidence_kind'] == 'unmeasured'
        assert not model['selected']
        assert upload(client, first).status_code == 200
        assert select(client, identity).status_code == 200
        another = upload(client, second).json()['model']
        assert client.get('/api/models').json()['selected_model_id'] == identity
        assert select(client, another['model_id']).status_code == 200
        detail = client.get(f'/api/models/{identity}').json()
        assert detail['manifest']['artifact']['sha256'] == detail['model_sha256']
        assert 'relative_path' not in json.dumps(detail)
        assert not client.get('/health').json()['model_loaded']
    with TestClient(app_at(tmp_path)) as client:
        state = client.get('/api/models').json()
        assert len(state['models']) == 2
        assert state['selected_model_id'] == another['model_id']
        assert next(m for m in state['models'] if m['selected'])['bundle_sha256'] == hashlib.sha256(second).hexdigest()
    assert not list((tmp_path / 'staging').iterdir())


def test_invalid_conflicting_unknown_and_oversized_preserve_selection(tmp_path, packages):
    first, _, model, manifest, evaluation = packages
    with TestClient(app_at(tmp_path)) as client:
        identity = upload(client, first).json()['model']['model_id']
        select(client, identity)
        manifest['name'] = 'Same ID different package'
        conflict = upload(client, bundle(model, manifest, evaluation))
        assert conflict.status_code == 409
        assert conflict.json()['code'] == 'identity_conflict'
        invalid = upload(client, b'bad zip')
        assert invalid.status_code == 422
        assert 'corrected ZIP' in invalid.json()['message']
        assert select(client, 'does-not-exist').status_code == 404
        assert client.post('/api/models/import', content=b'x', headers={'Content-Type': 'application/zip', 'Content-Length': '999999999'}).status_code == 413
        assert client.post('/api/models/import', content=b'x').status_code == 415
        assert client.get('/api/models').json()['selected_model_id'] == identity
        assert len(client.get('/api/models').json()['models']) == 1


@pytest.mark.parametrize('damage', ['missing', 'corrupt'])
def test_unavailable_selection_kept_and_alternative_works(tmp_path, packages, damage):
    first, second, *_ = packages
    with TestClient(app_at(tmp_path)) as client:
        identity = upload(client, first).json()['model']['model_id']
        other = upload(client, second).json()['model']['model_id']
        select(client, identity)
        with sqlite3.connect(tmp_path / 'workspace.sqlite3') as db:
            relative = db.execute('SELECT relative_path FROM artifacts JOIN models ON artifact_id=id WHERE model_id=?', (identity,)).fetchone()[0]
    path = tmp_path / relative
    if damage == 'missing':
        path.unlink()
    else:
        path.write_bytes(b'0' * len(first))
    with TestClient(app_at(tmp_path)) as client:
        state = client.get('/api/models').json()
        assert state['selected_model_id'] == identity
        assert not next(m for m in state['models'] if m['model_id'] == identity)['available']
        assert select(client, identity).status_code == 409
        repeated = upload(client, first)
        assert repeated.status_code == 200 and not repeated.json()['model']['available']
        assert select(client, other).json()['selected_model_id'] == other


def test_missing_runtime_keeps_metadata_and_selected_id(tmp_path, packages, monkeypatch):
    with TestClient(app_at(tmp_path)) as client:
        identity = upload(client, packages[0]).json()['model']['model_id']
        select(client, identity)
        monkeypatch.setattr(local_models, 'runtime_available', lambda: False)
        assert not client.get('/api/models').json()['validation_available']
        assert 'manifest' in client.get(f'/api/models/{identity}').json()
        for response in (upload(client, packages[0]), select(client, identity)):
            assert response.status_code == 503
            assert 'uv sync' in response.json()['message']
        assert client.get('/api/models').json()['selected_model_id'] == identity
        assert client.get('/health').status_code == 200


def test_busy_validation_does_not_block_health_or_duplicate_import(tmp_path, packages, monkeypatch):
    entered, release = threading.Event(), threading.Event()
    original = local_models.validate
    def wait(path):
        entered.set()
        assert release.wait(10)
        return original(path)
    with TestClient(app_at(tmp_path)) as client, ThreadPoolExecutor() as pool:
        monkeypatch.setattr(local_models, 'validate', wait)
        future = pool.submit(upload, client, packages[0])
        try:
            assert entered.wait(5)
            assert client.get('/health').status_code == 200
            assert client.get('/api/models').json()['models'] == []
            assert upload(client, packages[0]).json()['code'] == 'busy'
            assert select(client, 'anything').json()['code'] == 'busy'
        finally:
            release.set()
        assert future.result(timeout=10).status_code == 201
        assert len(client.get('/api/models').json()['models']) == 1


def test_real_worker_timeout_preserves_selection(tmp_path, packages, monkeypatch):
    from graphene_model_contract.errors import ContractError
    from graphene_model_contract.package import ValidationLimits, validate_file
    with TestClient(app_at(tmp_path)) as client:
        identity = upload(client, packages[0]).json()['model']['model_id']
        select(client, identity)
        def timeout(path):
            try:
                return validate_file(path, ValidationLimits(wall_seconds=0.001))
            except ContractError as error:
                raise local_models.ModelError(error.code, str(error))
        monkeypatch.setattr(local_models, 'validate', timeout)
        assert upload(client, packages[1]).json()['code'] == 'validation_timeout'
        assert select(client, identity).json()['code'] == 'validation_timeout'
        assert client.get('/api/models').json()['selected_model_id'] == identity
        assert not list((tmp_path / 'staging').iterdir())


@pytest.mark.parametrize('failure', ['chunked_limit', 'disconnect', 'deadline'])
def test_receiving_failures_clean_slot_and_staging(tmp_path, monkeypatch, failure):
    with TestClient(app_at(tmp_path)) as client:
        service = client.app.state.models
        service.archive_bytes = 3
        service.upload_seconds = 0.01
        async def stream(_request):
            if failure == 'deadline':
                await asyncio.sleep(10)
            yield b'123'
            if failure == 'disconnect':
                raise ClientDisconnect()
            yield b'4'
        monkeypatch.setattr(Request, 'stream', stream)
        response = client.post('/api/models/import', headers={'Content-Type': 'application/zip'})
        assert response.status_code == {'chunked_limit': 413, 'disconnect': 400, 'deadline': 408}[failure]
        assert not list(service.workspace.staging.iterdir())
        assert not service.slot.locked()


def test_publication_commit_failure_rolls_back_both_rows(tmp_path, packages, monkeypatch):
    with TestClient(app_at(tmp_path)) as client:
        identity = upload(client, packages[0]).json()['model']['model_id']
        select(client, identity)
        service = client.app.state.models
        original = service._commit_import
        def fail(*args):
            original(*args)
            raise sqlite3.OperationalError('private internal path')
        monkeypatch.setattr(service, '_commit_import', fail)
        result = upload(client, packages[1])
        assert result.status_code == 503 and 'private' not in result.text
        assert client.get('/api/models').json()['selected_model_id'] == identity
        with sqlite3.connect(service.workspace.database) as db:
            assert db.execute('SELECT count(*) FROM artifacts').fetchone()[0] == 1
            assert db.execute('SELECT count(*) FROM models').fetchone()[0] == 1
        assert len(list(service.workspace.artifacts.iterdir())) == 1


def make_v1(root):
    root.mkdir(exist_ok=True)
    (root / 'artifacts').mkdir()
    relative = f"artifacts/{'a' * 32}.bin"
    (root / relative).write_bytes(b'old opaque artifact')
    with sqlite3.connect(root / 'workspace.sqlite3') as db:
        db.execute('''CREATE TABLE artifacts (id TEXT PRIMARY KEY, relative_path TEXT NOT NULL UNIQUE,
            size INTEGER NOT NULL, sha256 TEXT NOT NULL, created_at TEXT NOT NULL, metadata TEXT NOT NULL,
            available INTEGER NOT NULL DEFAULT 1)''')
        db.execute('INSERT INTO artifacts VALUES(?,?,?,?,?,?,1)', ('old', relative, 19,
                   hashlib.sha256(b'old opaque artifact').hexdigest(), '2026-01-01', '{"note":"preserved"}'))
        db.execute('PRAGMA user_version=1')


def test_v1_migration_rolls_back_then_preserves_artifact(tmp_path, monkeypatch):
    make_v1(tmp_path)
    original = local_schema.add_model_registry
    def fail(db):
        original(db)
        raise sqlite3.OperationalError('migration interrupted')
    with monkeypatch.context() as patch:
        patch.setattr(local_schema, 'add_model_registry', fail)
        with pytest.raises(WorkspaceError):
            Workspace(tmp_path).open()
    with sqlite3.connect(tmp_path / 'workspace.sqlite3') as db:
        assert db.execute('PRAGMA user_version').fetchone()[0] == 1
        assert not db.execute("SELECT name FROM sqlite_master WHERE name='models'").fetchall()
    with Workspace(tmp_path) as store:
        assert store.read('old') == b'old opaque artifact'
        assert store.lookup('old').metadata == {'note': 'preserved'}
        with store._connection() as db:
            assert db.execute('PRAGMA user_version').fetchone()[0] == 2


@pytest.mark.parametrize('boundary', ['staging', 'published', 'committed'])
def test_registry_real_process_crash_recovery(tmp_path, packages, boundary):
    zip_path = tmp_path / 'fixture.zip'
    zip_path.write_bytes(packages[0])
    root = tmp_path / 'workspace'
    script = '''
import os, sys
from pathlib import Path
from app.services.workspace import Workspace
from app.services.local_models import LocalModels
store=Workspace(Path(sys.argv[1])).open()
service=LocalModels(store)
path=service.staging_path()
path.write_bytes(Path(sys.argv[2]).read_bytes())
if sys.argv[3]=='staging': os._exit(23)
if sys.argv[3]=='published': service._commit_import=lambda *args: os._exit(23)
service.import_file(path)
os._exit(23)
'''
    result = subprocess.run([sys.executable, '-c', script, str(root), str(zip_path), boundary], capture_output=True)
    assert result.returncode == 23, result.stderr.decode()
    with TestClient(app_at(root)) as client:
        state = client.get('/api/models').json()
        assert len(state['models']) == (1 if boundary == 'committed' else 0)
        assert state['selected_model_id'] is None
        assert not list((root / 'staging').iterdir())
        assert len(list((root / 'artifacts').iterdir())) == len(state['models'])


def test_cors_mutations_and_validation_error(tmp_path):
    with TestClient(app_at(tmp_path)) as client:
        for method in ('POST', 'PUT'):
            response = client.options('/api/models/import', headers={'Origin': 'http://127.0.0.1:3000', 'Access-Control-Request-Method': method, 'Access-Control-Request-Headers': 'Content-Type'})
            assert response.status_code == 200
        assert client.put('/api/models/selection', json={'model_id': 'x', 'extra': 'bad'}).status_code == 422


def test_binary_contract_rejected_at_api_preserving_selection(tmp_path, packages):
    first, _, _, manifest, evaluation = packages
    model = exporter.identity_graph(shape=(1, 1, 32, 32))
    manifest['artifact']['sha256'] = hashlib.sha256(model).hexdigest()
    manifest['artifact']['size'] = len(model)
    evaluation['model_sha256'] = manifest['artifact']['sha256']
    # A new model ID avoids the identity-conflict path and exercises native validation.
    from uuid import uuid4
    manifest['model_id'] = evaluation['model_id'] = str(uuid4())
    with TestClient(app_at(tmp_path)) as client:
        identity = upload(client, first).json()['model']['model_id']
        select(client, identity)
        response = upload(client, bundle(model, manifest, evaluation))
        assert response.status_code == 422
        assert response.json()['code'] == 'graph_interface'
        assert client.get('/api/models').json()['selected_model_id'] == identity


def test_failed_selection_commit_and_integrity_change_preserve_prior_model(tmp_path, packages, monkeypatch):
    from contextlib import contextmanager
    with TestClient(app_at(tmp_path)) as client:
        first = upload(client, packages[0]).json()['model']['model_id']
        second = upload(client, packages[1]).json()['model']['model_id']
        select(client, first)
        store = client.app.state.workspace
        original = store._connection
        @contextmanager
        def fail_commit():
            with original() as db:
                yield db
                if db.in_transaction:
                    raise sqlite3.OperationalError('commit interrupted')
        with monkeypatch.context() as patch:
            patch.setattr(store, '_connection', fail_commit)
            assert select(client, second).status_code == 503
        assert client.get('/api/models').json()['selected_model_id'] == first
        original_validate = local_models.validate
        def damage_after_validation(path):
            checked = original_validate(path)
            path.write_bytes(b'changed during validation')
            return checked
        with monkeypatch.context() as patch:
            patch.setattr(local_models, 'validate', damage_after_validation)
            assert select(client, second).json()['code'] == 'unavailable_model'
        assert client.get('/api/models').json()['selected_model_id'] == first


def test_cancelled_request_retains_slot_until_worker_finishes(tmp_path):
    from app.local_model_routes import owned_thread
    entered, release = threading.Event(), threading.Event()
    with Workspace(tmp_path) as store:
        service = local_models.LocalModels(store)
        def work():
            entered.set()
            assert release.wait(5)
        async def exercise():
            async def request():
                with service.mutation():
                    await owned_thread(work)
            task = asyncio.create_task(request())
            while not entered.is_set():
                await asyncio.sleep(.01)
            task.cancel()
            await asyncio.sleep(.01)
            assert service.slot.locked()
            assert not task.done()
            release.set()
            with pytest.raises(asyncio.CancelledError):
                await task
            assert not service.slot.locked()
        asyncio.run(exercise())


def test_cancelled_validation_cannot_commit_import_or_selection(tmp_path, packages, monkeypatch):
    original = local_models.validate
    cancelled = threading.Event()
    with TestClient(app_at(tmp_path)) as client:
        first = upload(client, packages[0]).json()['model']['model_id']
        second = upload(client, packages[1]).json()['model']['model_id']
        select(client, first)
        service = client.app.state.models
        path = service.staging_path()
        path.write_bytes(packages[0])
        def cancel_after_check(path):
            checked = original(path)
            cancelled.set()
            return checked
        monkeypatch.setattr(local_models, 'validate', cancel_after_check)
        with pytest.raises(local_models.ModelError, match='') as error:
            service.import_file(path, cancelled)
        assert error.value.code == 'operation_interrupted'
        cancelled.clear()
        with pytest.raises(local_models.ModelError) as error:
            service.select(second, cancelled)
        assert error.value.code == 'operation_interrupted'
        assert service.list()['selected_model_id'] == first
        assert len(service.list()['models']) == 2
        path.unlink()
