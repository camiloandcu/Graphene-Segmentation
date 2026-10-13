"""New experiment configuration; WI-06 v1 configuration/source remains untouched."""
from typing import Literal
from pydantic import model_validator
from graphene_training.config import TrainingConfig


class ExperimentConfig(TrainingConfig):
    schema_version: Literal[2] = 2
    architecture: Literal['unet-resnet18', 'segformer-b0', 'dinov3-vits16-linear', 'deeplabv3plus-resnet18']
    weights: str
    weights_revision: str | None = None
    weights_sha256: str | None = None
    weights_directory: str | None = None
    license_approved: bool = False

    @model_validator(mode='after')
    def initialization(self):
        identifiers = {'unet-resnet18': 'imagenet-resnet18-v1', 'segformer-b0': 'nvidia/mit-b0',
                       'dinov3-vits16-linear': 'facebook/dinov3-vits16-pretrain-lvd1689m',
                       'deeplabv3plus-resnet18': 'imagenet-resnet18-v1'}
        if self.weights != identifiers[self.architecture]:
            raise ValueError('Architecture requires its explicitly reviewed pretrained identifier')
        if self.architecture not in ('unet-resnet18', 'deeplabv3plus-resnet18'):
            if not self.weights_revision or len(self.weights_revision) != 40 or any(c not in '0123456789abcdef' for c in self.weights_revision):
                raise ValueError('Pin the exact 40-hex author weight repository revision')
        if self.weights_sha256 is not None and (len(self.weights_sha256) != 64 or any(c not in '0123456789abcdef' for c in self.weights_sha256)):
            raise ValueError('Expected weight digest must be lowercase SHA-256')
        return self
