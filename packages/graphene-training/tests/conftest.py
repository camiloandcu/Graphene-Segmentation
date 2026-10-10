"""Explicit synthetic reviewed dataset; never laboratory evidence."""
import io
import json
import zipfile
import numpy as np
import pytest
from PIL import Image
from graphene_dataset_contract import prepare


@pytest.fixture
def dataset(tmp_path):
    source = tmp_path / 'synthetic.zip'
    with zipfile.ZipFile(source, 'w') as archive:
        for role, n in [('train', 3), ('valid', 2), ('test', 1)]:
            doc = {'images': [], 'categories': [{'id': 1, 'name': 'few-layer'}, {'id': 2, 'name': 'bulk'}], 'annotations': []}
            for i in range(n):
                name = f'{i}.png'
                doc['images'].append({'id': i, 'file_name': name, 'height': 16, 'width': 24})
                for c, x in [(1, 2), (2, 12)]:
                    doc['annotations'].append({'id': i*2+c, 'image_id': i, 'category_id': c,
                                              'segmentation': [[x, 2, x+6, 2, x+6, 12, x, 12]]})
                rgb = np.random.default_rng(i + {'train': 10, 'valid': 100, 'test': 200}[role]).integers(0, 256, (16,24,3), dtype=np.uint8)
                b = io.BytesIO(); Image.fromarray(rgb).save(b, format='PNG')
                archive.writestr(f'{role}/{name}', b.getvalue())
            archive.writestr(f'{role}/_annotations.coco.json', json.dumps(doc))
    blocked = tmp_path / 'blocked'
    assert prepare(source, blocked, partial=True)['status'] == 'blocked'
    review = json.loads((blocked / 'review-template.json').read_text())
    inventory = {s['sample_id']: s for s in json.loads((blocked / 'validation.json').read_text())['inventory']}
    review.update(reference='synthetic only', reviewer='fixture author', date='2026-10-09',
                  mapping={'few-layer': 1, 'bulk': 2}, class_semantics_approved=True,
                  evaluation={'status': 'exploratory', 'evidence': 'Independent synthetic RGB',
                              'limitations': ['No laboratory or full-image accuracy evidence']})
    for d in review['samples']:
        d.update(role={'train':'train','valid':'validation','test':'test'}[d['sample_id'].split('-')[0]],
                 origin='human', origin_evidence='Synthetic fixture authored polygons', eligibility_approved=True,
                 completeness='non-exhaustive', group_status='known', group=d['sample_id'], group_evidence='Independent RNG seed',
                 background_anchors=[{'id':'blank-corner','class_id':0, 'image_sha256':inventory[d['sample_id']]['source_sha256'],
                     'polygons':[[0,0,2,0,2,16,0,16]],'evidence':'Synthetic empty strip',
                     'reviewer':'fixture author','date':'2026-10-09'}])
    path = tmp_path / 'review.json'; path.write_text(json.dumps(review))
    output = tmp_path / 'ready'
    assert prepare(source, output, review_path=path)['status'] == 'ready'
    return output
