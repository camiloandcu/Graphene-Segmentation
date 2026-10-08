# Reproduce the WI-03 audit

Checked: 2026-10-08. The 90-minute investigation limit was explicitly authorized.
The first audit action started at 18:05:34 UTC; the turn was interrupted and resumed
at 18:42 UTC. The gap is conservatively included in the wall-clock budget.

## Local source and environment

The source ZIP is under `.workspace/wi03/source/`; it was moved without changing
its contents. Source SHA-256 is recorded in the report and evidence manifest.
The audit reads ZIP members directly, validates member names/expanded size, and
never extracts or modifies source files. It supports this supplied COCO polygon
export, not arbitrary formats. RLE/crowd and box-only labels are reported unsupported.

Observed environment: Python 3.12.13, NumPy 2.5.3, Pillow 12.3.0 and pycocotools
2.0.10. Audit dependencies are pinned separately from the app in
`scripts/requirements-wi03.txt`. The isolated environment is ignored by Git.

From the repository root:

```bash
uv venv --python 3.12 .workspace/wi03/venv
uv pip install --python .workspace/wi03/venv/bin/python -r scripts/requirements-wi03.txt
.workspace/wi03/venv/bin/python scripts/audit_lab_dataset.py \
  '.workspace/wi03/source/2D Materials segmentation.v2i.coco-segmentation.zip' \
  .workspace/wi03/audit-new
.workspace/wi03/venv/bin/python -m pytest scripts/tests/test_lab_dataset_audit.py -q
```

Use a new output directory each time. Existing evidence is never overwritten.
Archive limits: at most 2,000 members / 100 MiB declared expanded bytes; at most
16 million pixels per decoded image. Unsafe paths, symlinks and duplicate ZIP
members fail. These are bounded audit defaults, not a hostile-input security claim.

## Evidence products

Two actual runs used `.workspace/wi03/audit-01/` and `audit-02/`.

- `inventory.json`: source IDs/paths, bytes and decoded-pixel checksums, geometry,
  annotation provenance, source split, explicit class support and issues.
- `metadata.json`: COCO category/license/version records and annotation-file hashes.
- `summary.json`: aggregate counts, environment and method settings.
- `duplicate_candidates.json`: candidate pairs requiring documented visual review.
- `proposed_split.json`: original role, unassigned proposed role and grouping cues.
- `masks/`: 40 original-resolution masks with 0/1/2/255 values.
- `overlays/`: 40 original-resolution overlays; cyan few-layer, orange bulk,
  magenta conflicting classes. Visualization blends 35% label color.
- `contact_sheets/`: four pages covering all 40 decoded images.
- `pair_sheets/`: 15 candidate comparisons.

Raw inventory and visual evidence stay local. Tracked reports use opaque audit
image IDs and aggregate counts. `05_DUPLICATE_REVIEW.json` records the actual
screening outcomes; freshly generated candidate files retain pending review until
the operator reviews them. The script never claims automatic expert review.

## Verification and scope limits

The two runs produced identical inventories, metadata, duplicate candidates,
proposed manifests, masks, overlays, contact sheets and pair sheets. The second
summary adds source-versus-associated annotation counts, dimensions and per-split
pixel support; overlapping summary fields agree.

Twenty focused tests passed: independent canonical-class expectations, ignored
overlap/order invariance, unknown source class, malformed/out-of-bounds/non-finite/
degenerate polygons, box-only labels, unsafe ZIP paths, expanded-byte bounds,
missing files, dimensions, no labels, orphan annotations, preserved input bytes,
no evidence overwrite, decoded-image duplicates with different bytes/conflicting
labels, and filename grouping cues.

pycocotools emits a NumPy array-interface deprecation warning in these tests.
Tests and actual decode runs succeeded; mask parity across independent reruns was
verified. This warning is retained as an upstream compatibility limitation.

No app runtime dependency, API or UI behavior changed, so app/frontend checks are
outside this change's affected execution path. Structural validation does not
prove polygon topology, physical thickness or exhaustive annotation. Similarity
retrieval does not guarantee discovery of rotated, cropped or partially overlapping
fields. No model performance was measured.
