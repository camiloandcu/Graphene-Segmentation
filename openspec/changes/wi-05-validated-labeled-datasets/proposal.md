# WI-05 — validated labeled datasets for the trainer

Status: proposal/design/specs explicitly approved by stakeholder on 2026-10-08.
Parent: INC-01 / F-01. Type: Enabler. Reuses [Issue #5](https://github.com/camiloandcu/Graphene-Segmentation/issues/5).
Consumer: occasional lab trainer and the WI-06 Colab data loader.

## Why

The accepted WI-03 audit found 40 images, reversed source numeric class IDs,
10 images with conflicting polygons, two cross-split grouping candidates, and
unknown acquisition identity/annotation completeness. The legacy cloud converter
copies numeric IDs and lets the last annotation win. Audit masks and saved
predictions cannot become ground truth merely because a PNG exists.

Outcome: a trainer receives an inspectable, reproducible dataset handoff whose
classes, original geometry, annotation origin, review decisions and split identity
are validated; unresolved inputs produce explicit blockers instead of a usable
training dataset. Technical validity and independent evaluation readiness are
separate properties.

## What changes

- Add an offline Python dataset contract and CLI for the supplied Roboflow-style
  COCO polygon ZIP, with bounded validation and original-resolution conversion.
- Add a versioned review record for class meaning, annotation origin/completeness,
  conflict policy and explicit split/group assignments or exclusions.
- Publish an immutable, checksummed dataset directory only after required reviews
  and structural checks pass; provide a consumer validator/loader for WI-06.
- Preserve original source roles, reviewed effective roles, license/attribution,
  unknowns and evidence references. Never generate random splits or infer physical
  acquisition identity from filenames.
- Deliver real-export blocked-path evidence, reviewed synthetic ready-path
  evidence, reproducibility/error regressions and a documented training handoff.
  A real ready-path run also requires an actual lab review record; synthetic
  reviewer statements must never be applied to the real export.

## Scope and exclusions

Scope: one local dataset preparation/consumption contract, CLI, source adapter,
review validation, masks, manifests, failure recovery, tests and usage documentation.
The supported input is the audited polygon format, not every COCO variant.
Exclude app dataset UI/API/storage migration, annotation editor/campaign,
cloud/account access, Figshare, pseudo-labeling, new split ratios, training,
augmentation/patches, model architecture and performance evaluation. WI-06 consumes
this artifact; WI-13 later guides the end-to-end user workflow.

## Dependencies and review decisions

WI-02 contract and WI-03 audit are merged; WI-03 and WI-04 were stakeholder accepted
on 2026-10-08. WI-04 is not a prerequisite. Existing canonical classes remain
0 background, 1 few-layer and 2 bulk; 255 is an annotation ignore value, never a
fourth model output class.

Proposed policies for approval:

1. Default to blocked readiness until class semantics, human annotation origin,
   completeness/background treatment, conflict handling and splits are reviewed.
2. Reject conflicting labels by default. A documented reviewer decision may allow
   255 for conflicting pixels; no class gets annotation-order precedence.
3. Require an explicit effective role per image (train/validation/test/excluded),
   with original roles retained. Known groups and exact duplicates cannot cross
   roles. Candidate grouping conflicts require review; source splits alone do
   not prove independence. Exploratory use may be explicitly acknowledged.
4. Exclude predictions and unknown annotation origins from training/evaluation.
   Reviewed model-assisted labels/pseudo-labels are outside this initial contract.
5. Build CLI/library support now; collect real lab decisions through the review
   record. Acceptance of this proposal authorizes software implementation, not
   fabricated reviewer attestations or training/evaluation approval.

## Acceptance criteria

| Criterion | Observable contract | Verification evidence |
| --- | --- | --- |
| WI-05-AC-1 | The real export is structurally validated with explicit name-based category mapping, original image/mask geometry and legal 0/1/2/255 labels; every source image/annotation is accounted for, and unresolved classes or malformed records prevent publication. | Real 40-image/759-annotation run reconciled with WI-03; synthetic reversed-ID, non-square and invalid-label cases; decoded masks inspected. |
| WI-05-AC-2 | A published handoff retains source/version/license, source and artifact digests, class mapping, image identity, original/effective roles, group evidence, annotation origin, review decisions and explicit unknowns. Repeated preparation with identical inputs/settings yields the same dataset/split fingerprints. | Manifest inspection and two runs; source unchanged; differing masks/reviews/assignments change the appropriate identity. |
| WI-05-AC-3 | Explicit reviewed assignments are preserved without random reassignment; missing roles, cross-role exact duplicates/known groups and unresolved candidate conflicts block readiness. Exploratory artifacts carry an explicit independence limitation. | Split/group fixtures, exact decoded duplicate cases and real-export deferred split evidence; consumer verifies the split fingerprint. |
| WI-05-AC-4 | Only explicitly human-annotated, reviewed eligible samples enter the handoff. Missing review, unresolved conflicts/completeness or prediction/unknown origin blocks eligible inclusion. Default conflict rejection and reviewed ignore behavior are deterministic. | Real-export blocker report, reviewed synthetic ready run, background/ignore checks and saved-prediction contamination regressions. |
| WI-05-AC-5 | The documented local workflow produces either an actionable blocked report or a complete artifact accepted by the consumer validator; malformed/tampered/partial artifacts are rejected, and failures preserve source and prior outputs. | Clean offline CLI/loader trial, tamper and interrupted-publication checks; real ready-path evidence if genuine lab review is supplied, otherwise explicitly pending. |

All criteria are currently unverified. Real source validation/blocking is required;
real training readiness remains pending if lab decisions are unavailable. Synthetic
ready-path proof establishes the software contract, not real-label certification.
Shared gates: G-01 affected policy review; G-02 proposal approval; G-03 criterion
and human acceptance evidence; G-04 checks/docs/commits/spec sync/archive. G-05
release and WI-06 real training remain separate.

## Impact

Add capability `validated-labeled-datasets`; reuse canonical model class definitions
without changing ONNX semantics. Expected code: `packages/graphene-dataset-contract/`
and focused tests, with CLI documentation in `docs/13_VALIDATED_DATASETS.md` and
verification in `docs/review/13_WI_05_VERIFICATION.md`. Raw images, masks, review
identities and private manifests remain ignored under `.workspace/wi05/`.
Issue #5 is reused; implementation branch `feat/wi-05-validated-labeled-datasets`
is linked with `gh issue develop 5`. Push and PR use `Closes #5`. No protected branch update is authorized.
