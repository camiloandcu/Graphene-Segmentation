"""Incremental verified copies within one writer session; full checks on recovery."""
import hashlib
from pathlib import Path

from graphene_dataset_contract.common import read_json
from graphene_training.storage import (
    MEMBERS, file_hash, inspect, separate_destination, verify_generation,
)


def copy_checked(source, target, expected):
    if target.is_symlink():
        raise ValueError('Persistence member cannot be a symlink')
    if target.exists():
        if file_hash(target) != expected:
            raise ValueError(f'Persistence collision: {target}')
        return
    checksum = hashlib.sha256()
    with source.open('rb') as reader, target.open('xb') as writer:
        for block in iter(lambda: reader.read(1024 * 1024), b''):
            checksum.update(block)
            writer.write(block)
        writer.flush()
    if checksum.hexdigest() != expected or file_hash(target) != expected:
        raise OSError(f'Persistence copy verification failed: {target}')


class IncrementalPersistence:
    """Fully inspect once, then verify only each newly completed generation.

    Previously acknowledged generations remain subject to full checksum-first
    inspection at the next recovery. No marker-only recovery shortcut is added.
    Drive's current-mount acknowledgement is not proof of remote durability.
    """

    def __init__(self, run, destination):
        self.run, self.destination = Path(run), Path(destination)
        separate_destination(self.run, self.destination)
        source = inspect(self.run)
        if self.destination.is_symlink():
            raise ValueError('Persistence destination cannot be a symlink')
        self.destination.mkdir(parents=True, exist_ok=True)
        copy_checked(self.run/'run.json', self.destination/'run.json', file_hash(self.run/'run.json'))
        epochs = self.destination/'epochs'
        if epochs.is_symlink():
            raise ValueError('Persistence epochs cannot be a symlink')
        epochs.mkdir(exist_ok=True)
        retained = inspect(self.destination)
        self.last = retained.get('completed_epochs', 0)
        completed = source.get('completed_epochs', 0)
        if self.last > completed:
            raise ValueError('Persistence destination advanced beyond source')
        for epoch in range(1, self.last + 1):
            generation = f'epoch-{epoch:06d}'
            if read_json(self.run/'epochs'/generation/'complete.json') != read_json(epochs/generation/'complete.json'):
                raise ValueError('Persistence generation differs from source')
        for epoch in range(self.last + 1, completed + 1):
            self.append(epoch)

    def append(self, epoch):
        if epoch != self.last + 1:
            raise ValueError('Persist only the next completed generation')
        generation = f'epoch-{epoch:06d}'
        _, _, source = verify_generation(self.run, generation)
        target = self.destination/'epochs'/generation
        if target.is_symlink():
            raise ValueError('Persistence generation cannot be a symlink')
        target.mkdir(exist_ok=True)
        marker = read_json(source/'complete.json')
        for member in sorted(MEMBERS):
            copy_checked(source/member, target/member, marker['files'][member])
        # The marker is acknowledged only after all three members verify.
        copy_checked(source/'complete.json', target/'complete.json', file_hash(source/'complete.json'))
        verify_generation(self.destination, generation)
        self.last = epoch
