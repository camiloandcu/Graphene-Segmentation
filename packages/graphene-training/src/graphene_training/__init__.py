"""Offline baseline; Colab is a consumer of the same training engine."""
from .config import TrainingConfig
from .data import preflight
from .engine import run, resume

__all__ = ["TrainingConfig", "preflight", "run", "resume"]
