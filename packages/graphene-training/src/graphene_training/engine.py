"""Training, complete-epoch resume, and distinct winning/last model identities."""
from __future__ import annotations
import random
import os
import time
from pathlib import Path

import numpy as np
import torch
from graphene_dataset_contract.common import identity, write_json
from .config import TrainingConfig, compatible, environment
from .data import RoleDataset, preflight
from .model import architecture, initialize
from .objective import evaluate, loss
from .storage import inspect, load_state, lock, persist, run_record, save_generation, separate_destination, verify_generation


def seed_all(seed):
    os.environ.setdefault("CUBLAS_WORKSPACE_CONFIG", ":4096:8")
    torch.backends.cuda.matmul.allow_tf32 = False
    torch.backends.cudnn.allow_tf32 = False
    random.seed(seed); np.random.seed(seed); torch.manual_seed(seed)
    if torch.cuda.is_available(): torch.cuda.manual_seed_all(seed)
    torch.backends.cudnn.benchmark = False
    torch.backends.cudnn.deterministic = True
    torch.use_deterministic_algorithms(True)


def rng_state():
    n = np.random.get_state()
    return {'python': random.getstate(), 'numpy': [n[0], n[1].tolist(), n[2], n[3], n[4]],
            'torch': torch.get_rng_state(),
            'cuda': torch.cuda.get_rng_state_all() if torch.cuda.is_available() else []}


def restore_rng(state):
    random.setstate(state['python'])
    n = state['numpy']; np.random.set_state((n[0], np.asarray(n[1], dtype=np.uint32), n[2], n[3], n[4]))
    torch.set_rng_state(state['torch'])
    if state['cuda']: torch.cuda.set_rng_state_all(state['cuda'])


def components(model, config):
    model.to(config.device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=config.learning_rate, weight_decay=config.weight_decay)
    scheduler = torch.optim.lr_scheduler.CosineAnnealingLR(optimizer, T_max=config.epochs)
    scaler = torch.amp.GradScaler('cuda', enabled=config.precision == 'amp-float16')
    generator = torch.Generator().manual_seed(config.seed)
    return optimizer, scheduler, scaler, generator


def run(dataset, config, output, *, _fixture_factory=None, _stop_after=None):
    """Internal fixture hooks never appear in CLI or real-lab notebooks."""
    config = TrainingConfig.model_validate(config) if isinstance(config, dict) else config
    evidence = preflight(dataset, config)  # No model, download or output mutation before support gates.
    env = environment(config)
    output = Path(output)
    if output.exists() or output.is_symlink(): raise ValueError('Use a new run output')
    if config.persistence_directory: separate_destination(output, config.persistence_directory)
    seed_all(config.seed)
    if _fixture_factory:
        model = _fixture_factory()
        weights = {'initialization': 'synthetic-random-fixture', 'source': 'test fixture', 'sha256': None}
    else:
        model, weights = initialize(output.parent / '.imagenet-weights')
    record = {'schema_version': 1, 'config': config.model_dump(), 'dataset': evidence,
              'environment': env, 'weights': weights,
              'preprocessing': PREPROCESSING_RECORD, 'selection': 'validation foreground macro Dice; earliest exact tie'}
    record['run_fingerprint'] = identity(record)
    output.mkdir(parents=True, exist_ok=False)
    (output / 'epochs').mkdir()
    write_json(output / 'run.json', record)
    with (output / 'run.json').open('rb') as stream: os.fsync(stream.fileno())
    directory_fd = os.open(output, os.O_DIRECTORY)
    try: os.fsync(directory_fd)
    finally: os.close(directory_fd)
    with lock(output):
        optimizer, scheduler, scaler, generator = components(model, config)
        return train(dataset, config, output, model, optimizer, scheduler, scaler, generator,
                     start=1, history=[], best_epoch=0, best_score=-1., stop_after=_stop_after)


from .config import PREPROCESSING
PREPROCESSING_RECORD = PREPROCESSING.model_dump(mode='json')


def resume(dataset, run_directory, generation, *, _fixture_factory=None, _stop_after=None):
    output = Path(run_directory)
    status = inspect(output)
    record = status['run']
    config = TrainingConfig.model_validate(record['config'])
    if generation != status['last']: raise ValueError('Resume the latest completed generation; earlier generations remain immutable')
    evidence = preflight(dataset, config)
    env = environment(config)
    if evidence != record['dataset']: raise ValueError('Dataset/split/supervision/configuration support changed')
    if not compatible(record['environment'], env): raise ValueError('Environment or training source is incompatible')
    if (_fixture_factory is None) != (record['weights']['initialization'] != 'synthetic-random-fixture'):
        raise ValueError('Fixture and pretrained runs cannot be interchanged')
    # Validate and safely deserialize before acquiring writer lock or touching output.
    state = load_state(output, generation)
    meta, history, _ = verify_generation(output, generation)
    seed_all(config.seed)
    model = _fixture_factory() if _fixture_factory else architecture()  # No pretrained download on resume.
    optimizer, scheduler, scaler, generator = components(model, config)
    model.load_state_dict(state['model'], strict=True)
    optimizer.load_state_dict(state['optimizer'])
    scheduler.load_state_dict(state['scheduler'])
    scaler.load_state_dict(state['scaler'])
    generator.set_state(state['generator'])
    restore_rng(state['rng'])
    with lock(output):
        if inspect(output)['last'] != generation: raise ValueError('Run advanced during resume validation')
        return train(dataset, config, output, model, optimizer, scheduler, scaler, generator,
                     start=meta['next_epoch'], history=history, best_epoch=meta['best_epoch'],
                     best_score=meta['best_score'], stop_after=_stop_after)


def train(dataset, config, output, model, optimizer, scheduler, scaler, generator,
          *, start, history, best_epoch, best_score, stop_after):
    if config.persistence_directory: persist(output, config.persistence_directory)
    expected = run_record(output)['dataset']['dataset_fingerprint']
    training = RoleDataset(dataset, 'train', config, expected)
    validation = RoleDataset(dataset, 'validation', config, expected)
    loader = torch.utils.data.DataLoader(training, batch_size=config.batch_size, shuffle=True,
                                        generator=generator, num_workers=0, drop_last=False)
    for epoch in range(start, config.epochs+1):
        begin = time.monotonic()
        model.train(); summed, examples = 0., 0
        if config.device == 'cuda': torch.cuda.reset_peak_memory_stats()
        for image, target in loader:
            image, target = image.to(config.device), target.to(config.device)
            optimizer.zero_grad(set_to_none=True)
            with torch.autocast(device_type=config.device, dtype=torch.float16, enabled=config.precision == 'amp-float16'):
                value = loss(model(image), target)
            if not torch.isfinite(value): raise ValueError('Nonfinite training loss')
            scaler.scale(value).backward(); scaler.step(optimizer); scaler.update()
            summed += float(value.detach()) * len(image); examples += len(image)
        measured = evaluate(model, validation, config)
        score = measured['foreground_macro_dice']
        if score is None or not np.isfinite(score): raise ValueError('Unavailable development selection metric')
        if score > best_score: best_epoch, best_score = epoch, score
        history.append({'epoch': epoch, 'loss': summed / examples, 'validation': measured,
                        'learning_rate': optimizer.param_groups[0]['lr'], 'elapsed_seconds': time.monotonic()-begin,
                        'peak_cuda_bytes': torch.cuda.max_memory_allocated() if config.device == 'cuda' else None,
                        'cuda_memory_unavailable_reason': None if config.device == 'cuda' else 'CPU run; CUDA memory not applicable'})
        scheduler.step()
        state = {'schema_version': 1, 'epoch': epoch, 'model': model.state_dict(), 'optimizer': optimizer.state_dict(),
                 'scheduler': scheduler.state_dict(), 'scaler': scaler.state_dict(), 'rng': rng_state(),
                 'generator': generator.get_state()}
        save_generation(output, epoch, state, history, best_epoch, best_score)
        if config.persistence_directory: persist(output, config.persistence_directory)
        if stop_after is not None and epoch >= stop_after: break
    status = inspect(output)
    if status['best']:
        winning = load_state(output, status['best'])
        model.load_state_dict(winning['model'], strict=True)
    status['runtime_environment'] = environment(config)
    return status
