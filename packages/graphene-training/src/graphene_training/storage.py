"""Immutable epoch generations; checksum-first recovery and completion-last copies."""
from __future__ import annotations
import contextlib
import fcntl
import os
import pickle
import shutil
import tempfile
from pathlib import Path

import torch
from graphene_dataset_contract.artifact import publish
from graphene_dataset_contract.common import digest, identity, read_json, write_json

MEMBERS = {'checkpoint.pt', 'history.json', 'metadata.json'}


def file_hash(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 2_000_000_000:
        raise ValueError('Checkpoint member is not a bounded regular file')
    import hashlib
    h = hashlib.sha256()
    with path.open('rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''): h.update(block)
    return h.hexdigest()


def run_record(run):
    run = Path(run)
    if run.is_symlink() or not run.is_dir():
        raise ValueError('Run must be a regular directory')
    data = read_json(run / 'run.json')
    if data.get('schema_version') != 1 or type(data['schema_version']) is not int:
        raise ValueError('Unsupported run schema')
    if data.get('run_fingerprint') != identity({k:v for k,v in data.items() if k != 'run_fingerprint'}):
        raise ValueError('Run record fingerprint mismatch')
    return data


def verify_generation(run, generation):
    run = Path(run)
    record = run_record(run)
    path = run / 'epochs' / generation
    if not generation.startswith('epoch-') or len(generation) != 12 or not generation[6:].isdigit():
        raise ValueError('Use an epoch-NNNNNN generation identity')
    if path.is_symlink() or not path.is_dir():
        raise ValueError('Missing regular generation directory')
    marker = read_json(path / 'complete.json')
    if set(marker) != {'schema_version', 'files'} or type(marker['schema_version']) is not int or marker['schema_version'] != 1 or set(marker['files']) != MEMBERS:
        raise ValueError('Unsupported generation completion marker')
    if set(p.name for p in path.iterdir()) != MEMBERS | {'complete.json'}:
        raise ValueError('Unexpected generation members')
    for name in MEMBERS:
        if file_hash(path / name) != marker['files'][name]:
            raise ValueError(f'Generation checksum mismatch: {name}')
    meta, history = read_json(path / 'metadata.json'), read_json(path / 'history.json')
    epoch = int(generation[6:])
    metadata_keys = {'schema_version', 'epoch', 'next_epoch', 'run_fingerprint', 'best_epoch', 'best_score', 'best_checkpoint_sha256'}
    if set(meta) != metadata_keys or any(type(meta.get(k)) is not int for k in ('schema_version', 'epoch', 'next_epoch', 'best_epoch')) or meta.get('schema_version') != 1:
        raise ValueError('Unsupported checkpoint schema')
    if meta.get('epoch') != epoch or meta.get('next_epoch') != epoch+1 or meta.get('run_fingerprint') != record['run_fingerprint']:
        raise ValueError('Generation/run identity mismatch')
    if not isinstance(history, list) or len(history) != epoch or [r.get('epoch') for r in history] != list(range(1, epoch+1)):
        raise ValueError('Incomplete or contradictory completed-epoch history')
    scores = [r['validation']['foreground_macro_dice'] for r in history]
    import math
    if not all(type(s) in (int,float) and math.isfinite(s) and 0 <= s <= 1 for s in scores):
        raise ValueError('Unavailable or invalid development selection score')
    winner = max(range(epoch), key=lambda i: scores[i]) + 1
    if meta.get('best_epoch') != winner or meta.get('best_score') != scores[winner-1]:
        raise ValueError('Best identity differs from completed development history')
    best = run / 'epochs' / f'epoch-{winner:06d}' / 'checkpoint.pt'
    if meta.get('best_checkpoint_sha256') != file_hash(best):
        raise ValueError('Best checkpoint digest mismatch')
    return meta, history, path


def inspect(run):
    run = Path(run)
    record = run_record(run)
    epochs = run / 'epochs'
    if epochs.is_symlink() or not epochs.is_dir():
        raise ValueError('Invalid epoch storage')
    generations = sorted(p.name for p in epochs.iterdir() if p.name.startswith('epoch-') and (p / 'complete.json').exists())
    for name in generations: verify_generation(run, name)
    if [int(n[6:]) for n in generations] != list(range(1, len(generations)+1)):
        raise ValueError('Completed generation sequence has a gap')
    if not generations:
        return {'run': record, 'last': None, 'best': None}
    meta, history, _ = verify_generation(run, generations[-1])
    return {'run': record, 'last': generations[-1], 'best': f"epoch-{meta['best_epoch']:06d}",
            'best_score': meta['best_score'], 'best_checkpoint_sha256': meta['best_checkpoint_sha256'],
            'completed_epochs': len(history)}


@contextlib.contextmanager
def lock(run):
    path = Path(run) / '.writer.lock'
    if path.is_symlink(): raise ValueError('Writer lock cannot be a symlink')
    with path.open('a+b') as stream:
        try:
            fcntl.flock(stream, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise ValueError('Another writer owns this run') from exc
        try: yield
        finally: fcntl.flock(stream, fcntl.LOCK_UN)


def save_generation(run, epoch, state, history, best_epoch, best_score):
    run = Path(run)
    stage = Path(tempfile.mkdtemp(prefix='.staging-', dir=run / 'epochs'))
    try:
        torch.save(state, stage / 'checkpoint.pt')
        checksum = file_hash(stage / 'checkpoint.pt')
        best_checksum = checksum if best_epoch == epoch else file_hash(run / 'epochs' / f'epoch-{best_epoch:06d}' / 'checkpoint.pt')
        write_json(stage / 'history.json', history)
        write_json(stage / 'metadata.json', {'schema_version': 1, 'epoch': epoch, 'next_epoch': epoch+1,
                   'run_fingerprint': run_record(run)['run_fingerprint'], 'best_epoch': best_epoch,
                   'best_score': best_score, 'best_checkpoint_sha256': best_checksum})
        files = {name: file_hash(stage / name) for name in sorted(MEMBERS)}
        # Flush every member before the completion marker and publication.
        for name in MEMBERS:
            with (stage / name).open('rb') as stream: os.fsync(stream.fileno())
        write_json(stage / 'complete.json', {'schema_version': 1, 'files': files})
        with (stage / 'complete.json').open('rb') as stream: os.fsync(stream.fileno())
        staging_fd = os.open(stage, os.O_DIRECTORY)
        try: os.fsync(staging_fd)
        finally: os.close(staging_fd)
        publish(stage, run / 'epochs' / f'epoch-{epoch:06d}')
        fd = os.open(run / 'epochs', os.O_DIRECTORY)
        try: os.fsync(fd)
        finally: os.close(fd)
    finally:
        if stage.exists(): shutil.rmtree(stage)


def load_state(run, generation):
    _, _, path = verify_generation(run, generation)
    try:
        state = torch.load(path / 'checkpoint.pt', weights_only=True, map_location='cpu')
    except (pickle.UnpicklingError, EOFError, RuntimeError) as exc:
        raise ValueError('Checkpoint is not a safe supported tensor/state mapping') from exc
    keys = {'schema_version', 'epoch', 'model', 'optimizer', 'scheduler', 'scaler', 'rng', 'generator'}
    if not isinstance(state, dict) or set(state) != keys or type(state['schema_version']) is not int or state['schema_version'] != 1 or type(state['epoch']) is not int or state['epoch'] != int(generation[6:]):
        raise ValueError('Unsupported/contradictory state checkpoint')
    return state


def separate_destination(run, destination):
    source, target = Path(run).resolve(), Path(destination).resolve()
    if source == target or source in target.parents or target in source.parents:
        raise ValueError("Persistence destination must be separate from the run and its parents/children")


def persist(run, destination):
    """Copy and verify members; never assume Drive rename/fsync semantics."""
    run, destination = Path(run), Path(destination)
    status = inspect(run)
    separate_destination(run, destination)
    if destination.is_symlink(): raise ValueError('Persistence destination cannot be a symlink')
    destination.mkdir(parents=True, exist_ok=True)
    def copy_member(source, target):
        expected = file_hash(source)
        if target.exists():
            if file_hash(target) != expected: raise ValueError(f'Persistence collision: {target}')
        else:
            shutil.copyfile(source, target)
        if file_hash(target) != expected: raise OSError(f'Persistence copy verification failed: {target}')
    copy_member(run / 'run.json', destination / 'run.json')
    (destination / 'epochs').mkdir(exist_ok=True)
    for epoch in range(1, status.get('completed_epochs', 0)+1):
        name = f'epoch-{epoch:06d}'
        _, _, source = verify_generation(run, name)
        target = destination / 'epochs' / name
        if target.is_symlink(): raise ValueError('Persistence generation cannot be a symlink')
        target.mkdir(exist_ok=True)
        for member in sorted(MEMBERS): copy_member(source / member, target / member)
        copy_member(source / 'complete.json', target / 'complete.json')  # Always last.
        verify_generation(destination, name)
    return inspect(destination)
