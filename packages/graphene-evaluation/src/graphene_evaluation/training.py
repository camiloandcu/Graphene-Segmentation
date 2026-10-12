"""Challenger epoch loop: WI-06 objective/selection with extra resource records."""
import time
from pathlib import Path
import numpy as np
import torch
from graphene_dataset_contract.common import write_json
from graphene_training.data import RoleDataset
from graphene_training.engine import rng_state
from graphene_training.objective import loss, evaluate
from graphene_training.storage import run_record, save_generation, persist, inspect, load_state


def train(dataset, config, output, model, optimizer, scheduler, scaler, generator,
          *, start, history, best_epoch, best_score, stop_after):
    if config.persistence_directory: persist(output, config.persistence_directory)
    expected=run_record(output)['dataset']['dataset_fingerprint']
    training=RoleDataset(dataset,'train',config,expected)
    validation=RoleDataset(dataset,'validation',config,expected)
    loader=torch.utils.data.DataLoader(training,batch_size=config.batch_size,shuffle=True,
                                       generator=generator,num_workers=0,drop_last=False)
    for epoch in range(start,config.epochs+1):
        began=time.monotonic(); model.train(); summed,examples=0.,0
        if config.device=='cuda': torch.cuda.reset_peak_memory_stats()
        for rgb,target in loader:
            rgb,target=rgb.to(config.device),target.to(config.device)
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type=config.device,dtype=torch.float16,enabled=config.precision=='amp-float16'):
                value=loss(model(rgb),target)
            if not torch.isfinite(value): raise ValueError('Nonfinite training loss')
            scaler.scale(value).backward(); scaler.step(optimizer); scaler.update()
            summed+=float(value.detach())*len(rgb); examples+=len(rgb)
        if config.device=='cuda': torch.cuda.synchronize()
        optimized=time.monotonic()
        measured=evaluate(model,validation,config)
        if config.device=='cuda': torch.cuda.synchronize()
        validated=time.monotonic()
        score=measured['foreground_macro_dice']
        if score is None or not np.isfinite(score): raise ValueError('Unavailable development metric')
        if score>best_score: best_epoch,best_score=epoch,score
        history.append({'epoch':epoch,'loss':summed/examples,'validation':measured,
                        'learning_rate':optimizer.param_groups[0]['lr'],
                        'elapsed_seconds':validated-began,'optimization_seconds':optimized-began,
                        'validation_seconds':validated-optimized,
                        'peak_cuda_bytes':torch.cuda.max_memory_allocated() if config.device=='cuda' else None,
                        'peak_cuda_reserved_bytes':torch.cuda.max_memory_reserved() if config.device=='cuda' else None,
                        'cuda_memory_unavailable_reason':None if config.device=='cuda' else 'CPU run'})
        scheduler.step()
        state={'schema_version':1,'epoch':epoch,'model':model.state_dict(),'optimizer':optimizer.state_dict(),
               'scheduler':scheduler.state_dict(),'scaler':scaler.state_dict(),'rng':rng_state(),
               'generator':generator.get_state()}
        save_generation(output,epoch,state,history,best_epoch,best_score)
        checkpointed=time.monotonic()
        if config.persistence_directory: persist(output,config.persistence_directory)
        # Sidecar is resource telemetry, never checkpoint/recovery authority. A
        # disconnected copy may omit it; epoch completion markers remain definitive.
        telemetry={'epoch':epoch,'checkpoint_seconds':checkpointed-validated,
                   'persistence_seconds':time.monotonic()-checkpointed,
                   'total_epoch_seconds':time.monotonic()-began}
        write_json(output/f'resources-epoch-{epoch:06d}.json',telemetry)
        if config.persistence_directory:
            write_json(Path(config.persistence_directory)/f'resources-epoch-{epoch:06d}.json',telemetry)
        if stop_after is not None and epoch>=stop_after: break
    status=inspect(output)
    if status['best']: model.load_state_dict(load_state(output,status['best'])['model'],strict=True)
    return status
