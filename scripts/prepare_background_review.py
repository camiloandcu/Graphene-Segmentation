"""Produce source-bound candidate figures; proposals never become background labels."""
from __future__ import annotations

import argparse
import os
from pathlib import Path

import numpy as np
from PIL import Image

from graphene_dataset_contract import check, iter_samples
from graphene_dataset_contract.common import digest, identity, write_json
from graphene_dataset_contract.partial import raw


def propose(rgb, source_mask, size=256, margin=64):
    """Rank clear-looking unannotated patches, without claiming they are substrate."""
    h, w = source_mask.shape
    median = np.median(rgb[::16, ::16], axis=(0, 1))
    candidates = []
    for y in range(margin, h-size-margin+1, 64):
        for x in range(margin, w-size-margin+1, 64):
            if np.any(source_mask[y-margin:y+size+margin, x-margin:x+size+margin] != 0):
                continue
            patch = rgb[y:y+size, x:x+size].astype(np.float32)
            # Reject strongly clipped acquisition artifacts; uniform material can still pass.
            if np.mean((patch < 8) | (patch > 247)) > .01:
                continue
            texture = np.mean(np.abs(np.diff(patch, axis=0))) + np.mean(np.abs(np.diff(patch, axis=1)))
            color_deviation = np.mean(np.abs(patch.mean(axis=(0, 1)) - median))
            candidates.append((float(texture + .1*color_deviation), x, y))
    if not candidates:
        raise ValueError('No unannotated candidate with an annotation-free margin; select manually')
    _, x, y = min(candidates)
    return [x, y, x+size, y+size]


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('dataset', type=Path)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args(argv)
    if args.output.exists() or args.output.is_symlink():
        raise ValueError('Use a new gallery destination')
    manifest = check(args.dataset)
    if manifest.schema_version != 2:
        raise ValueError('This source-bound review uses the explicit partial-v2 contract')
    # The whole artifact is checked, but no test image is displayed or proposed.
    training = [s for s in manifest.samples if s.role == 'train']
    indices = sorted(set([0, len(training)//3, 2*len(training)//3, len(training)-1]))
    selected = {training[i].sample_id for i in indices}
    selected.update(s.sample_id for s in manifest.samples if s.role == 'validation')
    args.output.mkdir(parents=True, exist_ok=False)
    os.environ.setdefault('MPLCONFIGDIR', str(args.output / '.matplotlib-cache'))
    import matplotlib
    matplotlib.use('Agg')
    import matplotlib.pyplot as plt
    from matplotlib.patches import Rectangle

    records, views = [], []
    for role in ('train', 'validation'):
        for sample, rgb, _ in iter_samples(args.dataset, role):
            if sample.sample_id not in selected:
                continue
            source_mask = raw(sample)
            box = propose(rgb, source_mask)
            x0, y0, x1, y1 = box
            crop = rgb[y0:y1, x0:x1]
            proposal_id = f'A{len(records)+1}'
            record = {'id': proposal_id, 'sample_id': sample.sample_id, 'role': role,
                      'source_path': sample.source_path, 'image_sha256': sample.source_sha256,
                      'rgb_sha256': sample.rgb_sha256, 'box_xyxy': box,
                      'polygons': [[x0,y0,x1,y0,x1,y1,x0,y1]],
                      'crop_pixels_sha256': digest(crop.tobytes()),
                      'source_foreground_or_conflict_pixels': int(np.count_nonzero(source_mask[y0:y1,x0:x1])),
                      'status': 'pending-human-review', 'reviewer': None, 'date': None,
                      'evidence': None, 'decision': None}
            records.append(record); views.append((rgb, record))
            Image.fromarray(crop).save(args.output / f'{proposal_id}-native-crop.png')
    pages = []
    for start in range(0, len(views), 4):
        batch = views[start:start+4]
        fig, axes = plt.subplots(len(batch), 3, figsize=(16, 3.6*len(batch)), squeeze=False)
        for row, (rgb, record) in enumerate(batch):
            x0,y0,x1,y1 = record['box_xyxy']
            h,w = rgb.shape[:2]
            ax = axes[row,0]
            ax.imshow(rgb, interpolation='nearest')
            ax.add_patch(Rectangle((x0,y0),x1-x0,y1-y0,fill=False,edgecolor='yellow',linewidth=2))
            ax.set_title(f"{record['id']} | {record['sample_id']} | {record['role']}\nOriginal: proposed region in yellow",fontsize=11)
            cx,cy = (x0+x1)//2,(y0+y1)//2
            left,top = max(0,min(w-768,cx-384)),max(0,min(h-768,cy-384))
            ax = axes[row,1]
            ax.imshow(rgb[top:top+768,left:left+768],interpolation='nearest')
            ax.add_patch(Rectangle((x0-left,y0-top),x1-x0,y1-y0,fill=False,edgecolor='yellow',linewidth=2))
            ax.set_title('Nearby context: inspect possible faint flake edges',fontsize=11)
            axes[row,2].imshow(rgb[y0:y1,x0:x1],interpolation='nearest')
            axes[row,2].set_title(f"Exact proposed patch: 256 x 256 pixels\n(x,y) [{x0},{y0}] to [{x1},{y1}], end exclusive",fontsize=11)
            for ax in axes[row]: ax.set_axis_off()
        fig.suptitle('BACKGROUND CANDIDATES — pending human review; original colors; no model predictions',fontsize=13)
        fig.tight_layout(rect=(0,0,1,.965))
        name=f'page-{len(pages)+1:02d}.png'
        fig.savefig(args.output/name,dpi=120);plt.close(fig);pages.append(name)
    record = {'schema_version':1,'source_sha256':manifest.source.sha256,
              'dataset_fingerprint':manifest.dataset_fingerprint,'split_fingerprint':manifest.split_fingerprint,
              'purpose':'Regional review of possible substrate; not ground truth and not model evaluation',
              'selection':'Four evenly spaced train sample IDs and all validation samples; no test proposals',
              'heuristic':'Unannotated patch + 64px source-annotation-free margin, low texture/color deviation; not proof of substrate',
              'decisions':['background-confirmed','not-background','uncertain'],
              'pages':pages,'candidates':records}
    record['proposal_fingerprint']=identity(record)
    write_json(args.output/'candidates.json',record)
    print(f'{len(records)} pending candidates; {len(pages)} figures; {args.output}')


if __name__ == '__main__': main()
