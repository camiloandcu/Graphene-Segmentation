"""Explicit pretrained semantic adapters; no implicit label reduction or resizing."""
from pathlib import Path
import hashlib
import torch
import torch.nn.functional as F
import segmentation_models_pytorch as smp
from graphene_training.model import initialize as initialize_resnet
from graphene_training.storage import file_hash


class SegFormer(torch.nn.Module):
    def __init__(self):
        super().__init__()
        from transformers import SegformerConfig, SegformerForSemanticSegmentation
        self.network = SegformerForSemanticSegmentation(SegformerConfig(num_labels=3))

    def forward(self, rgb):
        logits = self.network(pixel_values=rgb).logits
        return F.interpolate(logits.float(), rgb.shape[-2:], mode='bilinear', align_corners=False)


class DinoProbe(torch.nn.Module):
    def __init__(self):
        super().__init__()
        from transformers import DINOv3ViTConfig, DINOv3ViTModel
        self.encoder = DINOv3ViTModel(DINOv3ViTConfig(hidden_size=384, num_hidden_layers=12,
                                      num_attention_heads=6, intermediate_size=1536, patch_size=16,
                                      num_register_tokens=4))
        self.encoder.requires_grad_(False)
        self.head = torch.nn.Conv2d(384, 3, 1)
        self.encoder.eval()

    def train(self, mode=True):
        super().train(mode)
        self.encoder.eval()
        return self

    def forward(self, rgb):
        with torch.no_grad():
            features = self.encoder(pixel_values=rgb).last_hidden_state
        h, w = rgb.shape[-2:]
        spatial = features[:, 1+self.encoder.config.num_register_tokens:]
        if spatial.shape[1] != (h//16)*(w//16):
            raise ValueError('DINO spatial tokens differ from declared patch grid')
        spatial = spatial.transpose(1, 2).reshape(len(rgb), 384, h//16, w//16)
        return F.interpolate(self.head(spatial).float(), (h, w), mode='bilinear', align_corners=False)


def architecture(name):
    if name == 'segformer-b0':
        return SegFormer()
    if name == 'dinov3-vits16-linear':
        return DinoProbe()
    if name == 'deeplabv3plus-resnet18':
        model = smp.DeepLabV3Plus(encoder_name='resnet18', encoder_weights=None, in_channels=3, classes=3)
        # The 31-image role ends with a singleton batch. Global-pool BatchNorm
        # cannot train on [1,C,1,1]; use a declared GroupNorm in this new head.
        from segmentation_models_pytorch.decoders.deeplabv3.decoder import ASPPPooling
        for module in model.modules():
            if isinstance(module, ASPPPooling):
                for key, child in list(module.named_children()):
                    if isinstance(child, torch.nn.BatchNorm2d):
                        module[int(key)] = torch.nn.GroupNorm(32, child.num_features)
        return model
    if name == 'unet-resnet18':
        from graphene_training.model import architecture as baseline
        return baseline()
    raise ValueError('Unsupported reviewed architecture')


def pretrained(config, cache):
    if not config.license_approved:
        raise ValueError('Pretrained use requires recorded stakeholder license approval')
    if config.architecture == 'unet-resnet18':
        # Initialize exactly once: an extra decoder construction consumes RNG
        # and changes the baseline's initialization/data-order state.
        model, evidence = initialize_resnet(cache)
        if config.weights_sha256 and evidence['sha256'] != config.weights_sha256:
            raise ValueError('Pretrained weight identity mismatch')
        return model, evidence
    model = architecture(config.architecture)
    if config.architecture == 'deeplabv3plus-resnet18':
        baseline, evidence = initialize_resnet(cache)
        model.encoder.load_state_dict(baseline.encoder.state_dict(), strict=True)
        return model, evidence
    from huggingface_hub import snapshot_download
    directory = Path(config.weights_directory) if config.weights_directory else Path(snapshot_download(
        config.weights, revision=config.weights_revision, cache_dir=str(cache),
        allow_patterns=['config.json', '*.safetensors', '*.safetensors.index.json', 'pytorch_model.bin']))
    files = sorted(directory.glob('*.safetensors'))
    safetensors = bool(files)
    if not files and config.architecture == 'segformer-b0':
        files = [directory/'pytorch_model.bin'] if (directory/'pytorch_model.bin').is_file() else []
    if not files:
        raise ValueError('Pinned author weights are unavailable; no random fallback')
    checksum = hashlib.sha256()
    for file in files:
        # Hugging Face cache uses symlinks; hash resolved immutable bytes explicitly.
        checksum.update(file.name.encode()); checksum.update(file_hash(file.resolve()).encode())
    digest = checksum.hexdigest()
    if config.weights_sha256 and digest != config.weights_sha256:
        raise ValueError('Pretrained weight identity mismatch')
    if config.architecture == 'segformer-b0':
        from transformers import SegformerForImageClassification
        source, loading = SegformerForImageClassification.from_pretrained(
            directory, local_files_only=True, use_safetensors=safetensors, weights_only=True, output_loading_info=True)
        if loading['missing_keys'] or loading['unexpected_keys'] or loading['mismatched_keys']:
            raise ValueError('Author encoder loading is incomplete')
        model.network.segformer.load_state_dict(source.segformer.state_dict(), strict=True)
    else:
        from transformers import DINOv3ViTModel
        source, loading = DINOv3ViTModel.from_pretrained(directory, local_files_only=True,
                                  use_safetensors=True, output_loading_info=True)
        if loading['missing_keys'] or loading['unexpected_keys'] or loading['mismatched_keys']:
            raise ValueError('Author DINO encoder loading is incomplete')
        model.encoder.load_state_dict(source.state_dict(), strict=True)
    return model, {'initialization': 'pretrained', 'identifier': config.weights,
                   'source': 'https://huggingface.co/'+config.weights,
                   'revision': config.weights_revision, 'sha256': digest,
                   'checksum_definition': 'SHA-256 of sorted weight filename + file SHA-256 pairs',
                   'format': 'safetensors' if safetensors else 'pytorch restricted weights_only=True',
                   'license_approved': config.license_approved}
