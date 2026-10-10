# Validated datasets for Colab

WI-05 provides an offline handoff for the occasional trainer. It supports the
supplied Roboflow-style `train/valid/test/_annotations.coco.json` polygon ZIP.
It produces either a validated dataset directory or an actionable diagnostic
report. WI-06 adds a separate [baseline trainer](14_COLAB_BASELINE_TRAINING.md); dataset preparation itself does not train a model.

Current source, 2026-10-09: the stakeholder supplied v3 and authorized removal of
the old ZIP. See [v3 review](review/wi06/01_DATASET_V3_REVIEW.md) for remapped IDs,
approved grouped 31/4/5 roles and coverage uncertainty. Dense dataset-v1
excludes non-exhaustive active samples and remains supported. Partial-v2 support
is implemented in WI-06; unannotated pixels remain unknown. Current v3 previews/partial review
therefore produce blocked diagnostics, not a ready training artifact. No instruction
below authorizes filling pending review fields with positive attestations.

## Install and start with validation

From the repository root, on Linux with Python 3.12 and `uv`:

```bash
uv venv --python 3.12 .workspace/wi05/venv
uv pip install --python .workspace/wi05/venv/bin/python \
  -r scripts/requirements-wi05.txt \
  -e packages/graphene-model-contract -e packages/graphene-dataset-contract
.workspace/wi05/venv/bin/graphene-dataset prepare \
  '.workspace/wi06/source/2D Materials segmentation.v3i.coco-segmentation.zip' \
  --groups .workspace/wi06/dataset-v3/group-evidence.json \
  --output .workspace/wi06/dataset-v3/review-needed
```

Use a new output directory each time. Without review, exit **2** means expected
blocked readiness. Read `validation.json`, `source.json`, `group-evidence.json`
and `review-template.json`. No `manifest.json`, images or masks are published in a
blocked directory. Templates contain null decisions and are never approval records.
Exit **0** means ready, **3** invalid source/review/artifact and **4** I/O failure.
The CLI prints JSON with specific affected records/remedies; keep full logs private.

Raw images, reviewer identities and manifests belong in ignored `.workspace/`;
current data is under `.workspace/wi06/`, historical WI-05 fixtures under `.workspace/wi05/`.
Keep source ZIPs unchanged; a corrected export has a new digest and needs a new
bound review. Prior output directories are never overwritten.

## Complete a genuine review record

Copy the template to a private review JSON and fill it with actual lab decisions.
Preserve all sample IDs and source paths. The record requires:

- `source_sha256`: exact source ZIP checksum. `schema_version`: 1.
- `reference`, `reviewer`, `date`: review evidence reference, reviewer identifier,
  and ISO calendar date. These are recorded statements, not authenticated signatures.
- `mapping`: exactly `{"few-layer": 1, "bulk": 2}`; explicit
  `class_semantics_approved: true` after physical categories are reviewed.
- `evaluation`: status `exploratory` or `independence-reviewed`, evidence and
  limitations. Exploratory mode requires a nonempty limitations list. Reviewed
  independence requires affirmative known acquisition groups for active samples.
- One `samples` decision for **every** source image, including exclusions.
- One `dispositions` decision per grouping candidate in `group-evidence.json`.

Active sample decisions need `role` (`train`, `validation` or `test`),
`origin: "human"`, `origin_evidence`, `eligibility_approved: true`, and
`completeness: "exhaustive"`. An annotation-free negative image instead needs
`completeness: "verified-background"`; missing polygons do not prove background.
Non-exhaustive images, saved predictions and unknown origins must be excluded in
v1. An excluded sample uses `role: "excluded"` and `exclusion_reason`; it remains
traceable in the manifest, with no copied image/mask files.

`conflict_policy` defaults to `reject`. For overlapping bulk/few-layer labels,
either correct the source, exclude the image, or explicitly set `ignore` with a
`conflict_rationale`. Ignored pixels are 255, independent of annotation order;
255 is never a fourth output class. Entirely ignored masks cannot be included.

For each active sample, set `group_status` to `known` with `group` identity and
`group_evidence`, or `unknown` with `group: null` and evidence explaining the gap.
Nonempty train and validation roles are required; test is optional. Exact byte or
decoded RGB duplicates and known groups cannot cross active roles. Duplicate
images with conflicting masks also require correction/exclusion.

Candidate dispositions contain `left`, `right`, `decision` and `rationale`.
`co-group` requires the same known group and effective role for active candidates;
`excluded` requires at least one exclusion. `unrelated` records a reviewed
finding, while `uncertain` is allowed only with explicit exploratory limitations
when both images remain active. No random split fractions or automatic shuffling
are applied. Original roles are preserved separately from effective assignments.

For the historical v2 export, all 15 WI-03 candidate pairs are bundled with source-bound
evidence, including `test-000/train-007` and `test-001/valid-002`. They cannot be
silently omitted by supplying an empty evidence record. Other exports may supply
additional source-bound evidence with `--groups groups.json`; its schema contains
`schema_version`, `source_sha256` and `pairs` (`left`, `right`, `evidence`). V1 does
not search new near-duplicates. Missing acquisition/duplicate evidence must remain
an explicit review limitation, rather than a claim of independence.

For current v3, supply `.workspace/wi06/dataset-v3/group-evidence.json` explicitly:
it binds the 15 remapped candidates to the new checksum. The confirmed pairs are
`test-001/valid-003` and `test-002/train-028`, assigned together to test in the
partial review. Source IDs from v2 must not be copied directly.

WI-03 stakeholder acceptance accepted its conditional/inconclusive audit result.
It did not confirm class semantics, conflicts, annotation completeness or acquisition
identity. Never copy synthetic fixture attestations into the real lab review.

## Publish and verify the handoff

The current v3 partial-v2 review intentionally remains blocked because genuine
eligibility/semantic approvals and reviewed background evidence are absent. This
command demonstrates validation; it publishes a ready handoff only after genuine
review decisions are present. Schema-2 review selects partial preparation explicitly.
Do not mark coverage exhaustive or invent reviewer attestations to get past a check.

```bash
.workspace/wi05/venv/bin/graphene-dataset prepare \
  '.workspace/wi06/source/2D Materials segmentation.v3i.coco-segmentation.zip' \
  --review .workspace/wi06/dataset-v3/lab-review.json \
  --groups .workspace/wi06/dataset-v3/group-evidence.json \
  --output .workspace/wi06/dataset-v3/prepared-new
.workspace/wi05/venv/bin/graphene-dataset check .workspace/wi06/dataset-v3/prepared-new
```

A ready directory contains `manifest.json`, `validation.json`, `images/` and
`masks/`. Images preserve original source bytes; grayscale PNG masks use
0 background, 1 few-layer, 2 bulk and optional 255 ignored. Source categories in
the supplied export are numerically reversed: source 1 bulk becomes canonical 2,
and source 2 few-layer becomes canonical 1. Neither masks nor images are resized.

The manifest preserves raw source category/license/version metadata, attribution
text, annotation file hashes, explicit unknowns, converter/environment settings,
review decisions, source/effective roles, group evidence, per-image geometry,
annotation/class support and byte/decoded-pixel digests. Dataset identity hashes
UTF-8 JSON with sorted keys, compact separators, no NaN and stable sample/review
ordering, excluding its own digest. Split identity hashes sample/content/role/
exclusion/group/disposition records. Output paths and run timestamps are excluded.
Source/review/settings/label changes affect dataset identity; role/group changes
also affect split identity. Retain both IDs in the later training configuration.

Consumer validation verifies the complete directory before yielding samples.
Missing/changed files, extra prediction PNGs, symlinks, invalid masks, mismatched
review or fingerprints, and partial/diagnostic directories are rejected. Hashes
check integrity, not authenticated provenance: a false user attestation remains
outside what local software can detect. Keep ready artifacts immutable.

```python
from graphene_dataset_contract import check, iter_samples

manifest = check("/path/to/a/genuinely-ready-dataset")
print(manifest.dataset_fingerprint, manifest.split_fingerprint)
for sample, rgb, mask in iter_samples("/path/to/a/genuinely-ready-dataset", "train"):
    # Apply any later resize/patch/augmentation after split isolation.
    # WI-06 loss and metrics must honor ignore label 255.
    pass
```

Upload the complete directory to Colab using the trainer's chosen local file route;
install both packages there, then call the same validator/loader. No Colab account
or cloud action is performed by preparation. PNG folders must not be discovered
as ground truth by globbing around this contract.

## Limits, recovery and verification

Source limits: 100 MiB ZIP/read/expanded bytes, 2,000 members, 16 million pixels
per decoded image. Converted/consumer artifacts: 512 MiB total, 2,000 files,
100 MiB per-file reads and the same pixel limit. RLE/crowd/box-only annotations,
oriented/multi-frame images, unresolved annotated classes and unsafe members fail
explicitly. Unused parent categories are retained without mapping to background.

Publication stages complete files beside the new output and atomically renames
without replacement on Linux (also supported on Windows, unverified). I/O failure
or interruption cleans only owned staging and preserves source/prior outputs.
A process kill may leave a staging directory; incomplete contents fail consumer
validation. Use a new destination for retry. Supported package Python range is
3.10–3.13; actual verification used Linux/Python 3.12.

Reproduce software and private real-source evidence:

```bash
.workspace/wi05/venv/bin/python -m pytest \
  packages/graphene-dataset-contract/tests scripts/tests/test_lab_dataset_audit.py -q
.workspace/wi03/venv/bin/python scripts/audit_lab_dataset.py \
  '.workspace/wi06/source/2D Materials segmentation.v3i.coco-segmentation.zip' \
  .workspace/wi06/dataset-v3/audit-new
```

The v3 audit reads the current source without modifying it. Historical WI-05
checker evidence used v2, whose source ZIP was deleted with authorization; do not
run that v2-specific reconciliation against the new IDs/polygons. Genuine real ready
real ready handoff, background anchors and real Colab training remain pending.
Partial-mode preparation and the separate trainer are implemented and CPU-verified.
See [WI-05 verification](review/13_WI_05_VERIFICATION.md) for measured results.
