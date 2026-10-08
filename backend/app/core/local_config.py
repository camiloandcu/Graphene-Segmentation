"""Local configuration independent of cloud credentials and .env."""
from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class LocalSettings:
    workspace_dir: Path
    frontend_dir: Path

    @classmethod
    def from_environment(cls) -> "LocalSettings":
        data_home = Path(os.environ.get("XDG_DATA_HOME") or Path.home() / ".local/share")
        workspace = Path(os.environ.get("GRAPHENE_WORKSPACE_DIR") or data_home / "graphene-segmentation")
        frontend = Path(__file__).resolve().parents[3] / "frontend/dist"
        return cls(workspace.expanduser().resolve(), frontend)
