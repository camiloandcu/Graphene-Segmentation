"""Strict fixed-baseline configuration and runtime provenance."""
from __future__ import annotations
import hashlib
import platform
import subprocess
from importlib.metadata import version
from pathlib import Path
from typing import Annotated, Literal

import torch
from pydantic import Field, model_validator
from graphene_dataset_contract.schema import Strict
from graphene_model_contract.contract import Preprocessing

PREPROCESSING = Preprocessing(version=1, scale=1 / 255, mean=(.485, .456, .406),
                              std=(.229, .224, .225), padding_rgb=(0, 0, 0))


class TrainingConfig(Strict):
    schema_version: Literal[1] = 1
    architecture: Literal["unet-resnet18"] = "unet-resnet18"
    weights: Literal["imagenet-resnet18-v1"] = "imagenet-resnet18-v1"
    input_size: Annotated[int, Field(ge=64, le=1024)] = 512
    batch_size: Annotated[int, Field(ge=1, le=32)] = 2
    epochs: Annotated[int, Field(ge=1, le=1000)] = 30
    seed: Annotated[int, Field(ge=0, le=2**32-1)] = 42
    learning_rate: Annotated[float, Field(gt=0, le=1, allow_inf_nan=False)] = .001
    weight_decay: Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)] = .0001
    horizontal_flip: Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)] = 0.
    vertical_flip: Annotated[float, Field(ge=0, le=1, allow_inf_nan=False)] = 0.
    device: Literal["cpu", "cuda"] = "cpu"
    precision: Literal["float32", "amp-float16"] = "float32"
    persistence_directory: str | None = None

    @model_validator(mode="after")
    def constraints(self):
        if self.input_size % 32:
            raise ValueError("input_size must be divisible by 32")
        if self.precision == "amp-float16" and self.device != "cuda":
            raise ValueError("AMP requires CUDA; CPU uses float32 explicitly")
        return self


def environment(config):
    # Native single-thread CPU kernels make the baseline replay stable across processes.
    if config.device == "cpu":
        torch.set_num_threads(1)
        torch.backends.mkldnn.enabled = False
    if config.device == "cuda" and not torch.cuda.is_available():
        raise ValueError("CUDA requested but unavailable; select CPU explicitly")
    try:
        revision = subprocess.check_output(["git", "rev-parse", "HEAD"], stderr=subprocess.DEVNULL, text=True).strip()
    except (OSError, subprocess.CalledProcessError):
        revision = None
    source = hashlib.sha256()
    import graphene_dataset_contract, graphene_model_contract
    for package in (Path(__file__).parent, Path(graphene_dataset_contract.__file__).parent, Path(graphene_model_contract.__file__).parent):
        for p in sorted(package.glob('*.py')):
            source.update((package.name + '/' + p.name).encode()); source.update(p.read_bytes())
    return {"python": platform.python_version(), "packages": {n: version(n) for n in (
        "torch", "torchvision", "segmentation-models-pytorch", "timm", "numpy", "Pillow",
        "pydantic", "pycocotools", "graphene-training", "graphene-model-contract", "graphene-dataset-contract")},
        "torch_cuda": torch.version.cuda, "cudnn": torch.backends.cudnn.version(),
        "cpu_backend": "native-single-thread" if config.device == "cpu" else "cuda",
        "cpu_threads": torch.get_num_threads(), "cpu_interop_threads": torch.get_num_interop_threads(),
        "deterministic_policy": "deterministic algorithms; TF32 disabled; seeded RNG",
        "device_policy": config.device, "precision": config.precision,
        "gpu": torch.cuda.get_device_name(0) if config.device == "cuda" else None,
        "git_revision": revision, "training_source_sha256": source.hexdigest()}


def compatible(previous, current):
    # GPU model and checkout commit may differ; actual training source and package versions may not.
    ignored = {'gpu', 'git_revision'}
    if previous.get('device_policy') == current.get('device_policy') == 'cuda':
        ignored.update({'cpu_threads', 'cpu_interop_threads'})
    return {k: v for k, v in previous.items() if k not in ignored} == {
        k: v for k, v in current.items() if k not in ignored}
