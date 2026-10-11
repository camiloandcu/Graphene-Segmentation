# WI-05 validated dataset verification

Checked: 2026-10-08. Proposal/design/specs explicitly approved by stakeholder.
Status: software contract implemented, technically verified and merged via PR #19;
stakeholder item acceptance and genuine real-label/split readiness remain separate.
Issue: [#5](https://github.com/camiloandcu/Graphene-Segmentation/issues/5).
Branch: `feat/wi-05-validated-labeled-datasets`, linked with `gh issue develop 5`.
Approved-design commit: `8447823`. Implementation commit: `b17453f`.
[PR #19](https://github.com/camiloandcu/Graphene-Segmentation/pull/19) is merged with `Closes #5`; GitHub confirms the closing Issue
association. Both commits are pushed; handoff references are committed separately.
No automated GitHub checks are configured on this PR (checked via `gh`).

## Observable result

The offline Python package/CLI validates the supplied polygon ZIP, requires an
explicit source-bound human review, and publishes a complete immutable directory
only when annotation eligibility and split invariants pass. The same consumer
validator rejects missing/tampered files, prediction contamination, invalid masks
and incomplete/diagnostic directories before yielding training samples.

Two real-source preparations reproduced **40 images, 759 annotations, 10 conflict
images and 10,578 conflict pixels**, with all source bytes, decoded RGB digests,
class support and all 40 decoded masks matching WI-03. The source was unchanged.
All 15 WI-03 grouping candidates are retained, including the two cross-split pairs.
The real source correctly produces a **blocked** report and no ready manifest:
physical-category, eligibility/completeness and split/group decisions remain
pending. Conflict handling was subsequently approved as described below.
Stakeholder acceptance of WI-03 was not substituted for the remaining decisions.

Two reviewed synthetic handoffs reproduced dataset and split fingerprints. The
consumer iterated one sample each in train, validation and test with original
6×10 geometry and canonical 0/1/2 masks. Fixture reviews explicitly describe
synthetic data and exploratory limitations; they are never applied to real labels.

## Acceptance evidence

| Criterion | Software status | Evidence / limit |
| --- | --- | --- |
| AC-1 — Canonical validation | Passed | Complete real-export accounting and exact WI-03 mask agreement; reversed source IDs, non-square geometry, malformed polygons/categories/references and bounded archives exercised. |
| AC-2 — Traceability/reproducibility | Passed | Source metadata/license/attribution and unknowns retained; real reports identical, synthetic dataset/split IDs identical; label/review/role changes alter relevant IDs; source unchanged. |
| AC-3 — Reviewed split isolation | Passed | Explicit assignments/original roles preserved; exact byte/decoded duplicates and known groups crossing roles block readiness; all known-source candidates cannot be omitted; real assignments remain deferred. |
| AC-4 — Human eligibility | Passed | Prediction/unknown/missing origins rejected for active inclusion; stale/missing reviews blocked; default conflict rejection, deterministic reviewed ignore, verified negatives and all-ignore rejection exercised. Genuine lab review remains pending. |
| AC-5 — Complete offline handoff | Passed for software; real ready handoff unverified | CLI and consumer ready/blocked/invalid paths, schema/inventory/fingerprints/geometry/tamper checks, write/interruption/rename failures and no-overwrite competition pass. Fresh installed wheels consume the handoff. A real ready artifact needs a genuine lab review. |

Software verification is not stakeholder acceptance or certification of label truth.
The conditional real-ready evidence remains unverified, as allowed by the approved
proposal when genuine review is unavailable. WI-06 real training and G-05 release
remain blocked by the separate real-data human gate; no training ran.

## Checks performed

- Editable package plus unchanged WI-03 audit regression suite: **84 passed**
  (64 dataset checks and 20 audit checks), Linux/Python 3.12.13.
- Built model/dataset source distributions and wheels. A fresh wheel-only environment
  passed all **64 dataset checks** and the installed CLI consumed the existing
  synthetic handoff with matching identities. No ONNX, cloud/backend or frontend
  runtime dependency was installed for this path.
- `scripts/check-dataset-handoff.py`: two complete real blocked runs, all 40 masks
  reconciled, two synthetic ready runs and all active roles consumed.
- Strict OpenSpec validation passed all five synced specifications; documentation
  links and `git diff --check` passed. Verified software change is archived at
  `openspec/changes/archive/2026-10-08-wi-05-validated-labeled-datasets/`.
  App runtime/UI and the WI-03 audit implementation are unchanged; app build/tests
  were not needed for this isolated package.

Actual versions: NumPy 2.5.3, Pillow 12.3.0, pycocotools 2.0.11, Pydantic 2.14.0.
`requirements-wi05.txt` pins the verification environment separately from the app
and WI-03. pycocotools differs from WI-03's 2.0.10; all 40 real decoded masks still
agree exactly. Its existing NumPy `__array__` deprecation warning is non-blocking;
a duplicate-ZIP warning comes from the intentionally malformed test fixture.
Python 3.10/3.11/3.13 and Windows publication are unverified.

## Reproduction and private evidence

Follow [dataset preparation and consumption](../13_VALIDATED_DATASETS.md).

```bash
.workspace/wi05/venv/bin/python -m pytest \
  packages/graphene-dataset-contract/tests scripts/tests/test_lab_dataset_audit.py -q
.workspace/wi05/venv/bin/python scripts/check-dataset-handoff.py \
  --source '.workspace/wi03/source/2D Materials segmentation.v2i.coco-segmentation.zip' \
  --audit .workspace/wi03/audit-02 --output .workspace/wi05/verification-new
.workspace/wi05/wheel-venv/bin/graphene-dataset check .workspace/wi05/verification-01/synthetic-1
```

Private outputs: `.workspace/wi05/verification-01/`, including `summary.json`,
`real-1/`, `real-2/` and `synthetic-1/`, `synthetic-2/`. Ready synthetic artifacts
and source/review fixtures are local; raw data, paths and reviewer records are
excluded from Git. The checked summary contains:

- Real report fingerprint: `0c7b71f58c9b339bdd354c56afce2768a1f3e6e0370f60d181e0c821b276d710`.
- Synthetic dataset fingerprint: `27f19ab8d33d098c3ba946880121ef5daa6dabba232afbb1b67c2695523f86cf`.
- Synthetic split fingerprint: `c93c87856267941592823579392088e20da22e943756b17f167b78a2a4fdda7f`.

## Remaining human decisions

Current source update, 2026-10-09: v3 now supersedes this historical v2 evidence.
The old source ZIP was deleted with stakeholder authorization. See the
[current source review](wi06/01_DATASET_V3_REVIEW.md) for remapped decisions,
approved grouped 31/4/5 assignments, six remaining overlap images and partial-label
uncertainty. The old private review and numeric IDs are historical records only.
WI-05 v1 software remains verified; the v3 partial dataset is not a ready v1 handoff.

On 2026-10-08, the stakeholder approved ignoring only magenta overlap pixels in
the 10 affected real images, keeping all other labels and image content. The
source-bound partial review is saved privately at `.workspace/wi05/lab-review.json`:
only these samples receive `conflict_policy: ignore` and the decision rationale.
Class semantics, eligibility/completeness, effective roles, groups and evaluation
remain unapproved in that record; this decision does not authorize training or
approve the WI-06 proposal.

Targeted verification passed: all 40 regenerated masks match the WI-03 audit,
all original image bytes are preserved, and exactly 10,578 pixels in 10 images
are 255 with the approved ignore rationale. Preparation with the partial review
produced only blocked diagnostics at `.workspace/wi05/conflict-policy-review-01/`,
with no ready manifest. The source ZIP digest matches the review. No new code or
training was needed; `git diff --check` passed.

Additional stakeholder clarification, 2026-10-08: few-layer includes monolayer
and few-layer graphene. Bulk above 10 layers is a stakeholder assumption attributed
to literature, not a confirmed criterion used by the annotators. The stakeholder
tentatively considers bulk annotation complete but suspects unmarked few-layer
regions based on non-expert visual inspection. Missing regions are not confirmed,
and exhaustive background/foreground coverage is not approved; completeness stays
unresolved in the private review rather than being promoted to `exhaustive`.

The two cross-role candidates share original filename tokens `070524/Amostra-1`
(`test-001/valid-002`) and `070524/Amostra-3` (`test-000/train-007`), with
`Floco-1` versus `Floco-2` in each pair. On 2026-10-08, after reviewing that
evidence, the stakeholder confirmed shared physical samples and requested grouped
reorganization. Both pairs now have `co-group` dispositions and matching known
sample-group identities in the partial review. Final effective roles remain
pending; confirmed members must be placed in the same role. The other candidate
groups are not automatically approved by confirmation of these two pairs.

The stakeholder also states that manual pixel-precise labeling/refinement cannot
be considered reliable. Treating unannotated regions as confirmed background
therefore remains unsupported. Partial-label supervision with unknown pixels
ignored and independently supported background anchors is a possible revised
design, not implemented behavior. WI-05 v1 excludes non-exhaustive samples and
WI-06 currently assumes its ready dataset; supporting partial supervision requires
review of the affected dataset/training/evaluation contracts before code changes.

Supply a real source-bound lab review confirming physical categories, annotation
origin/completeness, acquisition/
candidate grouping, and explicit split assignments or exclusions. Unknown physical
facts cannot be resolved by successful PNG conversion. Then run real preparation/
consumer checks and record genuine readiness before WI-06 real training.
The WI-06 proposal is now separately pending approval. No protected branch update,
model training or cloud action is included in recording this dataset decision.
