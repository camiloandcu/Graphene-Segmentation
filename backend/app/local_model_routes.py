"""Local-only model routes, mounted ahead of the SPA."""
import asyncio
import os
import sqlite3
import threading

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict
from starlette.concurrency import run_in_threadpool
from starlette.requests import ClientDisconnect

from app.services.local_models import ModelError
from app.services.workspace import WorkspaceError

router = APIRouter(prefix="/api/models")


async def owned_thread(function, *args, on_cancel=None):
    """A cancelled caller must retain ownership until validation has reaped its worker."""
    task = asyncio.create_task(run_in_threadpool(function, *args))
    try:
        return await asyncio.shield(task)
    except asyncio.CancelledError as cancelled:
        if on_cancel:
            on_cancel()
        try:
            await asyncio.shield(task)
        except Exception:
            pass  # The original cancellation owns the response; cleanup still completed.
        raise cancelled


def install_errors(app):
    @app.exception_handler(ModelError)
    async def model_error(_request, error):
        return JSONResponse({"code": error.code, "message": error.message}, status_code=error.status)

    @app.exception_handler(WorkspaceError)
    @app.exception_handler(sqlite3.Error)
    @app.exception_handler(OSError)
    async def storage_error(_request, _error):
        return JSONResponse({"code": "storage_error", "message": "Local model storage failed. Check disk permissions and capacity, then retry."}, status_code=503)


@router.get("")
def list_models(request: Request):
    return request.app.state.models.list()


class Selection(BaseModel):
    model_config = ConfigDict(extra="forbid")
    model_id: str


@router.put("/selection")
async def select_model(request: Request, selection: Selection):
    service = request.app.state.models
    with service.mutation():
        cancelled = threading.Event()
        return await owned_thread(service.select, selection.model_id, cancelled, on_cancel=cancelled.set)


@router.post("/import")
async def import_model(request: Request):
    service = request.app.state.models
    with service.mutation():
        if request.headers.get("content-type", "").split(";")[0] != "application/zip":
            raise ModelError("unsupported_upload", "Choose a v1 model ZIP. Other model formats are not supported.", 415)
        declared = request.headers.get("content-length")
        if declared:
            try:
                length = int(declared)
            except ValueError:
                raise ModelError("invalid_size", "Upload size is invalid. Choose the ZIP again.") from None
            if length < 0 or length > service.archive_bytes:
                raise ModelError("archive_limit", "Model ZIP exceeds the 256 MiB upload limit. Export a smaller model.", 413)
        path = service.staging_path()
        try:
            async def receive():
                with path.open("xb") as stream:
                    total = 0
                    async for chunk in request.stream():
                        total += len(chunk)
                        if total > service.archive_bytes:
                            raise ModelError("archive_limit", "Model ZIP exceeds the upload limit. Export a smaller model.", 413)
                        await owned_thread(stream.write, chunk)
                    await owned_thread(stream.flush)
                    await owned_thread(os.fsync, stream.fileno())
            await asyncio.wait_for(receive(), timeout=service.upload_seconds)
            cancelled = threading.Event()
            model, created = await owned_thread(service.import_file, path, cancelled, on_cancel=cancelled.set)
            return JSONResponse({"model": model, "created": created}, status_code=201 if created else 200)
        except TimeoutError:
            raise ModelError("upload_timeout", "Upload took too long. Check the local connection and retry.", 408) from None
        except ClientDisconnect:
            raise ModelError("upload_interrupted", "Upload interrupted. Choose the ZIP and retry.", 400) from None
        finally:
            path.unlink(missing_ok=True)


@router.get("/{model_id}")
def model_detail(request: Request, model_id: str):
    return request.app.state.models.detail(model_id)
