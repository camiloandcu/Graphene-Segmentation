"""Explicit ImageNet weight download, safe tensor loading and byte identity."""
from pathlib import Path
import os
import tempfile
from graphene_dataset_contract.artifact import publish
import torch
import segmentation_models_pytorch as smp
from graphene_dataset_contract.common import digest

EXPECTED_SHA256 = 'f37072fd47e89c5e827621c5baffa7500819f7896bbacec160b1a16c560e07ec'
URL = 'https://download.pytorch.org/models/resnet18-f37072fd.pth'


def architecture():
    return smp.Unet(encoder_name='resnet18', encoder_weights=None, in_channels=3, classes=3, activation=None)


def initialize(cache):
    cache = Path(cache)
    cache.mkdir(parents=True, exist_ok=True)
    file = cache / URL.rsplit('/', 1)[1]
    if not file.exists():
        descriptor, temporary = tempfile.mkstemp(prefix='.weights-', dir=cache)
        os.close(descriptor)
        temporary = Path(temporary)
        try:
            torch.hub.download_url_to_file(URL, str(temporary), hash_prefix='f37072fd')
            if digest(temporary.read_bytes()) != EXPECTED_SHA256:
                raise ValueError('Downloaded ImageNet weight digest mismatch')
            try:
                publish(temporary, file)
            except FileExistsError:
                pass  # A concurrent publisher won; verify its bytes below.
        finally:
            temporary.unlink(missing_ok=True)
    if file.is_symlink() or not file.is_file():
        raise ValueError('Weights must be a regular file')
    checksum = digest(file.read_bytes())
    if checksum != EXPECTED_SHA256:
        raise ValueError('ImageNet weight digest differs from official torchvision identity')
    state = torch.load(file, map_location='cpu', weights_only=True)
    model = architecture()
    model.encoder.load_state_dict(state, strict=True)
    return model, {'source': URL, 'sha256': checksum, 'identifier': 'ResNet18_Weights.IMAGENET1K_V1',
                   'initialization': 'pretrained'}
