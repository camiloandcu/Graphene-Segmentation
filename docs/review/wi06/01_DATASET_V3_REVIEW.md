# Dataset v3 source transition and training readiness

Checked: 2026-10-09. This is measured data-review evidence, not a training result.

## Active source and replacement

The stakeholder supplied the refined version-3 COCO polygon export and explicitly
authorized removal of the previous version. The new ZIP was moved unchanged from
the repository root to the ignored private path
`.workspace/wi06/source/2D Materials segmentation.v3i.coco-segmentation.zip`.
After validating/comparing it, the v2 source ZIP was deleted as authorized.
Historical audit records/panels remain traceable; reproduction of the deleted v2
source requires separately obtaining that old export. No cloud data was accessed.

Active source SHA-256:
`344b2ff3bfcf0d18ac206894b92f0b89892f706bc8ef8dbb540a3a7a40da6a34`.
Historical source SHA-256:
`bc362e5e774e63cd62e677522abbf2bc632422cadd7b5e9642bbfa3ca97eede3`.

## Verified facts

| Property | v2 historical | v3 active |
| --- | ---: | ---: |
| Referenced/decoded images | 40 | 40 |
| Image dimensions | 2560 x 1920 | 2560 x 1920 |
| Polygon annotations | 759 | 621 |
| Conflicting-label images | 10 | 6 |
| Conflicting-label pixels | 10,578 | 1,792 |
| Exact duplicate pairs | 0 | 0 |
| Grouping candidate pairs | 15 | 15 |
| Original train/validation/test counts | 32/5/3 | 32/5/3 |

All 40 original image names match one-to-one and all image bytes are unchanged.
However, 39 source sample IDs changed. Numeric-ID copying would apply old decisions
to the wrong images. Decisions were transferred through original name plus exact
image-byte SHA-256; source paths and IDs are freshly bound to the v3 digest.
The same 15 grouping candidates are recovered after identity remapping.

Thirty-eight rasterized masks changed, totaling 2,833,813 changed pixels. Both
target classes still occur in every image. Source category 1 is bulk and maps to
canonical 2; category 2 is few-layer and maps to canonical 1. The declared parent
category is unused by annotations. Fewer polygons/overlaps do not establish
physical correctness or exhaustive coverage.

Read-only audit: `.workspace/wi03/venv/bin/python scripts/audit_lab_dataset.py`
on the new ZIP, output `.workspace/wi06/dataset-v3/audit/`. All 40 images decoded,
all 621 records were accounted for, and `issue_count` was zero. Environment:
Python 3.12.13, NumPy 2.5.3, Pillow 12.3.0, pycocotools 2.0.10.

## Recorded stakeholder decisions and effective roles

The stakeholder confirmed the two cross-role pairs share physical samples and
accepted the minimal reorganization that retains both groups in test:

| Historical identity | Current identity | Effective role |
| --- | --- | --- |
| test-001 | test-001 | test |
| valid-002 | valid-003 | test, moved from validation |
| test-000 | test-002 | test |
| train-007 | train-028 | test, moved from train |

All other original roles remain unchanged. Result: **31 train / 4 validation /
5 test**. Confirmed group members share a single role. Other 13 filename-derived
pairs remain uncertain, with both members in train; they are not automatically
confirmed physical groups. Evaluation remains explicitly exploratory.

The approved overlap policy is reapplied to current polygons: all remaining
bulk/few-layer intersections are 255, without class precedence. Old overlap
locations are not copied into refined masks. The stakeholder reconfirmed that
coverage cannot be guaranteed even with the new relatively refined export.
Unannotated regions therefore remain unknown. Few-layer includes monolayer;
the bulk above-10-layer boundary remains an assumption requiring annotation
provenance confirmation.

## Partial preview and limits

`.workspace/wi06/dataset-v3/lab-review.json` is now a source-bound schema-v2 partial review:
roles/groups/overlap policy and exploratory limitations are recorded; annotation
eligibility/completeness and full physical semantics are not fabricated.
`group-evidence.json` binds all 15 current candidates to this new source, so the
v2-specific bundled evidence is not silently reused or omitted.

Forty analysis masks in `partial-mask-preview/` retain current labels 1/2 and
overlap 255, but convert all 157,743,569 unannotated pixels to unknown 255.
No source images/annotations were edited. These previews are **not** published
ground truth or a ready training manifest. They have zero supervised background
pixels, so they do not yet satisfy a viable three-class training prerequisite.

Known labels/overlaps were checked for exact preservation, all 40 preview masks
were generated, both confirmed groups are isolated, and the partial review/groups
pass schema checks. Private `version-comparison.json` and `source-transition.json`
retain per-image reconciliation and replacement evidence. The active ZIP checksum
was rechecked after v2 deletion. No trained-model quality is claimed.

Installed WI-05 v1 preparation was also executed against the actual v3 ZIP,
partial review and all 15 supplied candidate records. It correctly emitted only
blocked diagnostics at `.workspace/wi06/dataset-v3/v1-blocked-review/`, with 81
pending semantics/eligibility/completeness decisions and no ready manifest.
No cross-role known-group or co-group violation occurred. Strict validation of
the revised WI-06 OpenSpec change passed, as did local links/whitespace across
18 Markdown files. No training dependencies, UI code or accounts were changed.

## Remaining work and downstream consumers

WI-05 v1 excludes non-exhaustive active samples. WI-06 implements
the explicit partial-v2 contract. Its actual v3 preparation remains blocked by
41 unresolved eligibility/semantic decisions; there is no ready manifest. Preserve v1 compatibility and distinguish
unknown pixels from confirmed background; never relabel a v1 handoff silently.

For real training, obtain reviewed origin/eligibility and independently supported
background anchors in train and validation, with geometry/provenance. Complete
pixel-precise manual refinement is not required; regions or material-free controls
can provide evidence if they can genuinely be identified. Without such evidence,
retain a blocked result instead of training a claimed three-class baseline.
Masked development metrics measure only supervised support, not full-image
coverage or complete false-positive/flake recall. Real Colab execution remains
unverified. The full revised proposal requires approval before implementation.

Human-in-the-loop regional opinions are a requested future screening capability,
described in the UX/architecture review. They remain separate from pixel ground
truth and do not silently alter this dataset, splits, checkpoints or frozen test.

## Partial-v2 implementation verification, 2026-10-09

The active review was migrated to explicit schema 2 with `supervision_mode: partial`,
`non-exhaustive` coverage and empty background anchors. All missing approvals remain
missing. Preparation against the unchanged v3 ZIP and approved groups produced
`.workspace/wi06/dataset-v3/partial-v2-blocked-review/`, with 41 blockers.
Source counts remain 40 images/621 polygons/1,792 conflicts. Supervised support:

| Role | Images | Background | Few-layer | Bulk | Unknown |
| --- | ---: | ---: | ---: | ---: | ---: |
| Train | 31 | 0 | 993,405 | 27,819,254 | 123,558,541 |
| Validation | 4 | 0 | 549,443 | 4,831,254 | 14,280,103 |
| Test | 5 | 0 | 84,933 | 4,584,350 | 19,906,717 |

The 157,745,361 unknown pixels include unannotated area and source conflicts;
only 1,792 are magenta cross-class conflicts. No images were generated and no
source foreground was erased by uncertainty outside its annotation. Zero background
in train/validation also blocks the trainer before model/download/output mutation.
See [WI-06 verification](../14_WI_06_VERIFICATION.md) for software and real-trial status.
