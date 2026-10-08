"""Local startup excludes cloud/auth and optional model runtimes."""
from __future__ import annotations

from contextlib import asynccontextmanager
import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.core.local_config import LocalSettings
from app.services.workspace import Workspace, WorkspaceError
from app.services.workspace import SCHEMA_VERSION
from app.services.local_models import LocalModels
from app.local_model_routes import router, install_errors

logger = logging.getLogger(__name__)


def create_app(settings: LocalSettings | None = None) -> FastAPI:
    settings = settings or LocalSettings.from_environment()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        workspace = Workspace(settings.workspace_dir)
        try:
            workspace.open()
        except WorkspaceError as error:
            logger.error("Local startup failed: %s", error)
            raise RuntimeError(str(error)) from None
        app.state.workspace = workspace
        app.state.models = LocalModels(workspace)
        try:
            yield
        finally:
            workspace.close()

    app = FastAPI(title="Graphene Workspace", version="0.2.0", lifespan=lifespan)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://127.0.0.1:3000", "http://localhost:3000"],
        allow_credentials=False,
        allow_methods=["GET", "POST", "PUT"],
        allow_headers=["Content-Type"],
    )

    @app.get("/health")
    def health():
        return {"status": "ok", "runtime": "local", "storage_ready": app.state.workspace.ready,
                "schema_version": SCHEMA_VERSION, "model_loaded": False, "model_framework": None}

    install_errors(app)
    app.include_router(router)

    if settings.frontend_dir.is_dir():
        app.mount("/", StaticFiles(directory=settings.frontend_dir, html=True), name="frontend")
    return app
