## Why

The model trainer needs trustworthy labels and an honest evaluation split before
training. The lab dataset's actual masks, class support and overlap remain
unverified. Its reported image count cannot establish label quality or independent
samples. This spike supplies evidence for WI-05 and later training decisions.

## Work Item and Review State

- WI-03 / Spike, parent INC-01 / F-01;
  [Issue #3](https://github.com/camiloandcu/Graphene-Segmentation/issues/3).
- Consumers: model trainer and stakeholder.
- Question: can the supplied masks/taxonomy support training, and what evaluation
  independence can be supported without acquisition metadata?
- Status: proposal explicitly approved by the stakeholder on 2026-10-08.
  Two local audit runs are technically verified; stakeholder acceptance is pending.
- Source: [scope and acceptance criteria](../../../../docs/review/06_DECISIONS_AND_WORK_ITEMS.md#wi-03--spike-establish-what-the-lab-dataset-can-support).
- Execution inputs resolved: stakeholder supplied the version-2 COCO ZIP and
  authorized relocation to `.workspace/wi03/source/` and a 90-minute limit.
  Physical label/group definitions remain explicit downstream lab-review questions.

## What Changes

- Inspect the supplied export locally without modifying source data, accessing
  dataset accounts, or invoking the legacy Supabase converter.
- Produce a reproducible inventory of image/label counts, dimensions, class
  mappings/support, invalid or missing labels, provenance and unknowns.
- Review representative overlays and exact/near-duplicate candidates; distinguish
  confirmed overlap from suspected similarity and unknown acquisition grouping.
- Deliver a proposed split manifest, exclusions, leakage limitations and a
  supported readiness recommendation or inconclusive result with next steps.
- Persist the audit procedure and evidence with explicit acceptance status.

## Capabilities

### New Capabilities

- `lab-dataset-audit`: evidence requirements for a reproducible lab dataset audit
  and split recommendation. This specifies the spike deliverable, not an app API.

### Modified Capabilities

None. Runtime model contracts and the local workspace remain unchanged.

## Impact

Expected implementation areas: a local audit entry point under `scripts/`,
focused fixtures where needed, and evidence under `docs/review/wi03/` with a
verification record linked from the review index. Exact format support depends on
the supplied export; this item does not promise a universal dataset importer.
Raw images, masks and private visual evidence stay outside Git unless publication
is explicitly authorized. Track source paths/fingerprints and evidence locations
without copying private acquisition data into public reports.

Excluded: annotation campaigns, production import, Figshare inspection, model
training/comparison, cloud writes and physical thickness validation by inference.
Implementation, Issue-linked branch, commits/push and PR follow proposal approval.

## Acceptance

- WI-03-AC-1: actual inventory, mapping/support, geometry, label/provenance issues
  and version/license are evidenced or explicitly unknown.
- WI-03-AC-2: overlap evidence supports a proposed split manifest with exclusions
  and remaining leakage uncertainty.
- WI-03-AC-3: a reviewable readiness recommendation or inconclusive conclusion
  identifies blocking questions and the next action.

AC-1 through AC-3 have technical evidence in
[the verification record](../../../../docs/review/11_WI_03_VERIFICATION.md).
Human review and G-01 through G-04 remain separate from automated checks. The
supported inconclusive evaluation finding does not certify dataset/model quality.
