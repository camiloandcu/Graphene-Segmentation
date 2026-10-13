# WI-07 — measured selection of a feasible graphene segmentation model

Status: full proposal/design/specifications explicitly approved by the stakeholder
on 2026-10-11, including finite stages, metric proxies, resource gates and test freeze.
Type: Spike. Parent: INC-01 / F-02. Reuses
[Issue #7](https://github.com/camiloandcu/Graphene-Segmentation/issues/7).
Consumer: stakeholder choosing an exploratory screening model and WI-08 exporter.

## Why

WI-06 produced a traceable pretrained U-Net/ResNet-18 checkpoint. Its development
Dice alone cannot establish best feasible few-layer detection, false-detection
burden, resource use or operating settings. The stakeholder requested current
2D-material and related-microscopy evidence rather than assuming U-Net is SOTA.
The [source review](../../../docs/review/wi07/01_LITERATURE_AND_CANDIDATES.md)
motivates both pretrained semantic challengers and domain-specific feasibility
checks. Current labels are partial visual categories, not measured layer counts.

Question: among the reviewed candidates/settings that fit interactive Colab and
the local application contract, which trade-off is supported by our fixed lab
data, and what remains unknowable without better labels or more held-out groups?
Outcome: reproducible comparison, error/resource evidence and a supported model/
setting recommendation, or an explicitly inconclusive answer with a next step.
An improvement or a claim of globally optimal/SOTA performance is not required.

## What changes

- Add offline evaluation/reporting and a thin interactive Colab comparison
  notebook, retaining dataset/split/supervision and checkpoint identities.
- Evaluate the exact WI-06 baseline; train SegFormer-B0 and a gated frozen
  DINOv3 ViT-S/16 semantic probe sequentially on the same partial supervision.
- Assess 2D-TLK as a fourth semantic challenger, gated by reproducibility,
  licensing, pretrained identity, ignore-aware optimization, recovery and export
  interface feasibility. Assess MaskTerial's domain relevance and compatibility;
  it is not automatically a complete three-class comparator. If the 2D-TLK gate
  stays closed, use the predeclared DeepLabv3+/ResNet-18 comparator to test
  multiscale decoding with the baseline's pretrained encoder.
- Measure supported pixel/component metrics, unknown coverage, threshold
  trade-offs, original-coordinate error panels, seed sensitivity and resources.
- Produce a decision record for WI-08. Final test is scored only after the
  stakeholder freezes one model/settings record; unsupported measures stay null.

## Scope and effort boundary for review

Stakeholder decisions already received: include U-Net, SegFormer-B0 and gated
DINOv3; seek the best feasible model; allow separate Colab day sessions.
No fixed hours, number of days or GPU quota was imposed. Proposed bounded stages:

1. Reuse WI-06 rather than retrain its seed-42/30-epoch baseline. Admit each new
   candidate through an actual environment/weights/forward/backward/recovery
   check. Start with one seed-42, 30-epoch development run per admitted semantic
   challenger, using the common protocol in the design.
2. Report gates for 2D-TLK and MaskTerial. Admit at most the one additional
   semantic model (2D-TLK, or DeepLabv3+/ResNet-18 if that gate is closed) under
   this proposal. MaskTerial gets a compatibility
   assessment and, if executable, a clearly separate class-agnostic detection
   preview; complete detector/classifier adaptation requires further review.
3. Shortlist at most two candidates from measured validation trade-offs. Screen
   1024-letterbox and native 512-tile/384-stride inference on their retained
   checkpoints. For each finalist, allow one evidence-justified training change
   (geometry OR learning-rate correction), declared before running it. Preserve
   the initial protocol and report the change as an ablation.
4. Confirm each finalist's frozen configuration with seeds 42, 43 and 44, reusing
   compatible existing runs. Compare one common original-coordinate support and
   stop when feasible trade-offs are documented or data uncertainty prevents a
   defensible preference. Training checkpoints always persist across sessions.

These are proposed run/stage limits, not an agreed GPU-hour budget or guaranteed
resource availability. Colab quota exhaustion means save/recover on a later
available session. Do not bypass quotas, buy compute or drive Colab unattended.
If the stages cannot answer the question, report the limitation and ask for a
specific extension; do not silently add models, grids, seeds or external data.

Scope excludes new annotations/splits, Figshare or synthetic-data generation,
pseudo-labels, unreviewed color augmentation, production UI, ONNX export/parity
and app integration. Existing pretrained weights may be used with recorded
provenance; no external lab dataset is added. WI-08 retains export ownership.

## Dependencies and review decisions

WI-03 audit is accepted. WI-06 PR #20 is merged; local `main` already contains
`7d4954d`, checked 2026-10-11 via authorized `gh`. Dataset-v3 partial-v2 is reviewed
and supports all three classes in train/validation. Roles remain 31/4/5; test has
no background support and acquisition independence remains partly unknown.
Baseline epoch 23 SHA-256:
`c199f87a1d3f06f013dbef0db7982c6d4e3e2ba852146c1ca57f735ec25e267f`.
The identities in the [WI-06 evidence](../../../docs/review/14_WI_06_VERIFICATION.md)
and [confirmed handoff](../../../docs/review/wi06/03_LABEL_CONFIRMATION_AND_BACKGROUND_REVIEW.md)
must agree before evaluation.

Approval must cover the finite stages above, candidate gates, component proxy
definitions, partial-label limitations, and freeze/test workflow in the design.
Numeric minimum few-layer recall and acceptable full false-detection burden are
not agreed and cannot be validated with exhaustive coverage absent. They remain
release decisions after pilot error review. A provisional exploratory recommendation
may be accepted with limitations; no arbitrary weighted score selects a winner.
Colab/Drive access method was previously authorized for WI-06; verify its continuing
availability before execution. New Meta access/license acceptance requires the
stakeholder's action/authorization; absent access produces a gated-out DINO record.

## Acceptance criteria

| Criterion | Observable outcome | Evidence |
| --- | --- | --- |
| WI-07-AC-1 | All evaluation runs bind to verified dataset/split/supervision, class mapping, checkpoint/config/source identities and declared roles. Unknown pixels and padding never become background; test/excluded samples never enter fitting or development selection. | Consumer validation, digest checks, role-leakage/tamper/non-square fixtures and actual baseline reconciliation. |
| WI-07-AC-2 | The stakeholder receives actual baseline and SegFormer comparison plus an executed DINO probe or supported access/license/resource exclusion. 2D-TLK/MaskTerial each receive an evidence-based gate decision; admitted runs preserve comparable supervision and durable cross-session state. | Real run/checkpoint histories, initialization/config/env records, fresh-session recovery, gate diagnostics and matched comparison table. Synthetic tests alone do not establish measured candidates. |
| WI-07-AC-3 | Reports contain accumulated confusion counts, per-class precision/recall/IoU/Dice and foreground macros, annotated-component matching/misses, known-region false detections and unknown detections, plus explicit unavailable reasons for full flake recall/false burden/ranking when unsupported. | Hand-calculated fixtures and real per-image/aggregate reports with denominators, unknown support and deterministic panels/matching. No unsupported class receives a perfect score. |
| WI-07-AC-4 | Development setting/geometry decisions and finalist seed sensitivity are reproducible, with original-coordinate errors and measured GPU/training/CPU resources. Uncertainty accounts for image/group support and unknown acquisition identities. | Validation sweeps, geometry ablations, finalist seed records, per-image uncertainty/sensitivity and hardware-tagged timings/memory; unavailable hardware measurements have a reason. |
| WI-07-AC-5 | A reviewed decision records a feasible candidate/settings handoff or an inconclusive result, reasons/exclusions and next step. A final-test report uses only the frozen selection, or test deferral is explicit; test results never reopen selection. | Stakeholder decision/freeze identity, selected checksum/settings/support references, final exploratory test evidence or documented deferral, and WI-08 handoff limitations. |

All criteria are **unverified**. G-02 full proposal approval precedes coding;
G-03 includes measured evidence and stakeholder decision; G-04 sync/archive follows
verification and submission. G-05 deployment/release thresholds remain separate.
Do not call literature inspection, software regressions or a single Dice score
item completion.

## Impact and workflow

Add capability `model-selection-evaluation`; extend the separate training/evaluation
package and training-only dependencies with compatibility for WI-06 saved runs.
Expected artifacts include a comparison notebook, technical guide, private reports/
panels under `.workspace/wi07/`, and public aggregate evidence under
`docs/review/wi07/`. Preserve raw lab images and weight/checkpoint privacy.

After explicit approval, refine Issue #7 and link
`feat/wi-07-model-selection` using `gh issue develop 7`; implement in coherent
Conventional Commits, push and open a PR with `Closes #7` and criterion evidence.
Sync/archive only verified scope. No protected-branch update, WI-08 proposal or
new paid/account service is authorized by this draft.
