"""Partial annotations cannot manufacture background, including after resealing hashes."""
import json
import numpy as np
import pytest
from PIL import Image
from graphene_dataset_contract import check, prepare, iter_samples
from graphene_dataset_contract.common import DatasetError, digest, identity
from graphene_dataset_contract.partial import report_for
from graphene_dataset_contract.partial_schema import PartialManifest
from graphene_dataset_contract.schema import Manifest
from conftest import reviewed


def partial_review(source, tmp_path, *, anchors=True):
    path = reviewed(source, tmp_path)
    review = json.loads(path.read_text())
    blocked = tmp_path / 'partial-template'
    assert prepare(source, blocked, partial=True)['status'] == 'blocked'
    inventory = json.loads((blocked / 'validation.json').read_text())['inventory']
    review.update(schema_version=2, supervision_mode='partial')
    for d, s in zip(review['samples'], inventory):
        d['completeness'] = 'non-exhaustive'
        d['background_anchors'] = ([{'id': 'corner', 'class_id': 0, 'image_sha256': s['source_sha256'],
            'polygons': [[0, 0, 1, 0, 1, 1, 0, 1]], 'evidence': 'Synthetic known blank corner',
            'reviewer': 'fixture author', 'date': '2026-10-09'}] if anchors else [])
    path.write_text(json.dumps(review))
    return path


def test_partial_unknown_and_anchor(source, tmp_path):
    review = partial_review(source, tmp_path)
    output = tmp_path / 'partial-ready'
    assert prepare(source, output, review_path=review)['status'] == 'ready'
    manifest = check(output)
    assert manifest.schema_version == 2
    with pytest.raises(ValueError):
        Manifest.model_validate(manifest.model_dump())
    _, _, target = next(iter_samples(output, 'train'))
    assert target[0, 0] == 0
    assert target[5, 9] == 255
    assert target[1, 1] == 1
    assert target[1, 5] == 2
    assert manifest.samples[0].source_class_pixels['0'] > manifest.samples[0].class_pixels['0']


@pytest.mark.parametrize('mutation', ['stale', 'overlap', 'outside', 'bad-date'])
def test_anchor_rejection(source, tmp_path, mutation):
    path = partial_review(source, tmp_path)
    data = json.loads(path.read_text())
    a = data['samples'][0]['background_anchors'][0]
    if mutation == 'stale': a['image_sha256'] = '0' * 64
    if mutation == 'overlap': a['polygons'] = [[1, 1, 3, 1, 3, 3, 1, 3]]
    if mutation == 'outside': a['polygons'][0][0] = -1
    if mutation == 'bad-date': a['date'] = '2026-02-30'
    path.write_text(json.dumps(data))
    report = prepare(source, tmp_path / 'invalid', review_path=path)
    assert report['status'] == 'invalid'
    assert not (tmp_path / 'invalid' / 'manifest.json').exists()


def test_resealed_false_background_rejected(source, tmp_path):
    output = tmp_path / 'partial-ready'
    prepare(source, output, review_path=partial_review(source, tmp_path))
    m = check(output)
    s = m.samples[0]
    mask = np.array(Image.open(output / s.mask_path))
    mask[5, 9] = 0
    Image.fromarray(mask).save(output / s.mask_path)
    s.mask_sha256 = digest((output / s.mask_path).read_bytes())
    s.mask_pixels_sha256 = digest(mask.tobytes())
    s.class_pixels['255'] -= 1
    s.class_pixels['0'] += 1
    from graphene_dataset_contract.partial import supervision_fingerprint
    m.supervision_fingerprint = supervision_fingerprint(m.samples, m.review)
    m.dataset_fingerprint = identity(m.model_dump(exclude={'dataset_fingerprint'}))
    (output / 'manifest.json').write_text(m.model_dump_json())
    (output / 'validation.json').write_text(report_for(m.samples, m.source.sha256, m.review, []).model_dump_json())
    with pytest.raises(DatasetError, match='Supervision differs'):
        check(output)
