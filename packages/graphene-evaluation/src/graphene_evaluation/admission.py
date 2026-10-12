"""Actual reviewed pretrained forward/backward admission; no random substitute."""
import time
import torch
from graphene_training.engine import seed_all
from graphene_training.objective import loss
from .candidates import pretrained
from .experiments import environment


def admit(config, cache):
    env=environment(config)
    seed_all(config.seed)
    started=time.monotonic()
    model, weights=pretrained(config,cache)
    model.to(config.device).train()
    if config.device=='cuda': torch.cuda.reset_peak_memory_stats()
    rgb=torch.zeros(config.batch_size,3,config.input_size,config.input_size,device=config.device)
    target=torch.zeros(config.batch_size,config.input_size,config.input_size,dtype=torch.long,device=config.device)
    target[:,32:128,32:128]=1; target[:,160:256,160:256]=2; target[:,::3,::3]=255
    result=model(rgb)
    if result.shape != (config.batch_size,3,config.input_size,config.input_size):
        raise ValueError('Admission output contract mismatch')
    result.retain_grad()
    value=loss(result,target); value.backward()
    if not torch.isfinite(value) or not torch.isfinite(result.grad).all():
        raise ValueError('Admission loss/gradient is not finite')
    if torch.any(result.grad.permute(0,2,3,1)[target==255]!=0):
        raise ValueError('Ignored output pixels contributed objective gradients')
    if config.architecture=='dinov3-vits16-linear':
        if model.encoder.training or any(p.grad is not None for p in model.encoder.parameters()):
            raise ValueError('DINO encoder was not frozen')
    if config.device=='cuda': torch.cuda.synchronize()
    return {'schema_version':1,'status':'admitted','config':config.model_dump(), 'weights':weights,
            'environment':env,'parameters':sum(p.numel() for p in model.parameters()),
            'trainable_parameters':sum(p.numel() for p in model.parameters() if p.requires_grad),
            'finite_loss':float(value.detach()),'ignore_gradients_zero':True,
            'seconds':time.monotonic()-started,
            'peak_cuda_allocated_bytes':torch.cuda.max_memory_allocated() if config.device=='cuda' else None,
            'peak_cuda_reserved_bytes':torch.cuda.max_memory_reserved() if config.device=='cuda' else None,
            'scope':'Synthetic input admission of real pretrained bytes, not real-data quality evidence'}
