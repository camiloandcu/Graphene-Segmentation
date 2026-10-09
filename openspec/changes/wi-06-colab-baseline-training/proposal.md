# WI-06 — resumable pretrained baseline training in Colab

Status: revised on 2026-10-09 for dataset v3 and partial supervision. The stakeholder
explicitly approved this revised proposal/design/specifications on 2026-10-09,
including unknown-pixel handling and the grouped 31/4/5 reorganization. Real-data
eligibility/background anchors and actual Colab execution remain separate gates.
Parent: INC-01 / F-02. Type: Enabler. Reuses [Issue #6](https://github.com/camiloandcu/Graphene-Segmentation/issues/6).
Consumer: occasional lab trainer, then WI-07 evaluation and WI-08 export.

## Why

WI-05 now supplies a validated dataset contract, but the repository has no
supported Colab trainer. The consumer needs to start a reproducible pretrained
baseline, recover after a runtime interruption, and identify the checkpoint that
actually won on the development split. Legacy cloud training is outside the
local architecture. A runnable notebook alone does not prove this capability.

Outcome: an interactive Colab run consumes the reviewed WI-05 artifact, trains
the three-class baseline, resumes from a durable completed epoch and produces
an inspectable best-development checkpoint with dataset/configuration identity.
This checkpoint is a candidate for evaluation/export, not an accepted lab model.

## What changes

- Add an independently installable training package and a thin, documented Colab
  notebook; keep training dependencies out of the app and contract core.
- Validate the complete WI-05 handoff before loading train/validation samples.
  Preserve effective roles, provenance, fingerprints and evaluation limitations.
- Extend the dataset contract with an explicit partial-supervision v2 profile,
  preserving v1 behavior. Unannotated pixels remain unknown 255; only reviewed
  background anchors can supervise class 0. Reject missing three-class support.
- Train an ImageNet-pretrained U-Net/ResNet-18 with RGB input, three logit channels,
  explicit preprocessing, ignore-aware loss, AdamW and a recorded schedule.
- Record environment, pretrained-weight identity, seeds, resolved configuration,
  per-epoch metrics, elapsed time and measured GPU memory when available.
- Persist resumable epoch checkpoints and select the best original-coordinate
  validation foreground macro Dice over supervised pixels, with an explicit
  earlier-epoch tie rule and recorded supervised support/unknown coverage.
- Prove real Colab training and recovery in a new runtime, alongside local
  software regressions. Keep missing real-data/Colab evidence unverified.

## Scope and exclusions

Scope: one baseline trainer, its dataset adapter, development metric/loss contract,
checkpoint recovery/selection, notebook, run artifacts, tests and trainer guide.
Partial-dataset validation is part of enabling this trainer; region-feedback UI
is a separate requested candidate in the existing product/UX review, not a second
OpenSpec proposal or a hidden app implementation in WI-06.
Initial geometry is 512 x 512 letterbox, using WI-02 rounding/normalization and
inverse-logit behavior; masks use nearest-neighbor interpolation and ignored
padding. This is a pilot configuration with explicit small-flake loss limitations.

Exclude SegFormer/DINOv3, architecture search, Figshare, pseudo-labeling, split
changes, native-tile/crop experiments, color augmentation, final-test evaluation,
flake matching/uncertainty/ranking reports, operating-threshold tuning, ONNX
export/model import, app training endpoints and automated remote Colab control.
WI-07 owns model/setting evaluation; WI-08 owns portable export and parity.

## Dependencies and proposed review decisions

WI-02 and WI-05 are merged; local `main` already contains WI-05 merge `aed35d2`.
GitHub PR #19 merge was checked via authorized `gh` on 2026-10-08. This confirms
software availability, not real-label review or stakeholder item acceptance.

The [v3 review](../../../docs/review/wi06/01_DATASET_V3_REVIEW.md) supersedes v2
for current training. The old ZIP was removed with explicit authorization. The
new source is structurally valid but coverage remains uncertain; 40 partial masks
are analysis previews with no supervised background, not ready training data.
The stakeholder accepted retaining both confirmed shared-sample groups in test,
yielding 31 train / 4 validation / 5 test; remapped v3 identities are authoritative.

1. Approve U-Net/ResNet-18 ImageNet initialization as the sole baseline. Record
   the actual weight source and SHA-256; never silently substitute random weights.
2. Approve letterbox at 512 pixels as the initial geometry, with no claim that
   it preserves tiny flakes. Record foreground support lost by training resize.
3. Approve train-only optional horizontal/vertical flips and CE + foreground
   soft Dice; exclude ignore pixels from both losses and all metrics.
4. Approve maximum original-coordinate masked validation foreground macro Dice as the
   development selection surrogate, exact ties keeping the earlier epoch.
   Require all three supervised classes in train and validation for this baseline;
   absent support blocks the run with a remedy, without changing assignments.
5. Approve recovery at completed-epoch boundaries. Reuse the fixed configuration,
   schedule horizon, dataset/split and environment; incompatible changes start
   a separate run. Exact CUDA replay is not promised across hardware/runtimes.
6. Allow software implementation after proposal approval while genuine dataset
   review is pending; keep WI-06 acceptance open until real Colab evidence passes.
   Synthetic/local execution cannot satisfy the real-run criterion.
7. Implement explicit partial-dataset v2 support under the confirmed unknown-pixel
   policy: source-bound eligible foreground labels, documented background anchors,
   every other unannotated pixel 255, and a fixed supervision identity for metrics.
   Missing background evidence remains a real-run blocker. Complete pixel-precise
   manual refinement is not required; model feedback never becomes ground truth
   or a background anchor merely because a user accepts a predicted region.

Blocking inputs for real execution: a genuinely reviewed WI-05 ready artifact,
interactive Colab access and an explicit user choice of persistence/access method.
No new Google/Drive account access or paid compute is authorized here. The guide
will explain manual execution; ask MCP versus manual before account actions.

## Acceptance criteria

| Criterion | Observable contract | Verification evidence |
| --- | --- | --- |
| WI-06-AC-1 | Training starts only from a fully consumer-validated dense v1 or explicitly partial v2 handoff with nonempty train/validation and all three supervised classes supported in each role. Partial artifacts use 255 for unannotated pixels except reviewed background anchors; source, effective roles, supervision identity and dataset/split fingerprints are retained. Test/excluded samples never enter optimization, scoring or selection. | Dense-v1 compatibility and partial-v2 fixtures, unknown/background/anchor identity checks, invalid support/tamper/group regressions and the v3 31/4/5 record. Whole-artifact integrity checks may read test files without evaluating them. |
| WI-06-AC-2 | The pretrained baseline performs finite optimization with three-channel logits, paired geometric transforms, ignored padding and an explicit normalization/loss/schedule. The run records actual weights, resolved config, source revision, environment, seeds, per-epoch losses, development counts/metrics, time and measured GPU resources or a reason unavailable. | Small CPU optimization and non-square/ignore fixtures; notebook setup checks; actual Colab run records. No random-initialization run is labeled pretrained. |
| WI-06-AC-3 | A completed epoch produces a verified durable checkpoint restoring model, optimizer, scheduler, AMP state when applicable, RNG/data-order state, epoch/history and best-checkpoint identity. Interrupted writes preserve the last complete generation; mismatch, corruption or partial generations fail without modifying prior results. | Deterministic CPU uninterrupted-versus-resumed comparison; write-failure/corrupt/mismatch cases; real Colab disconnect/new-runtime recovery from an independently retained checkpoint. |
| WI-06-AC-4 | Best selection uses aggregate original-coordinate supervised validation counts, excludes ignored/unknown pixels and padding, never awards perfect metrics for unsupported classes, and applies the declared foreground Dice/tie rule. Partial metrics record their fixed support and unknown fraction without claiming full-image quality. The handoff identifies the winning epoch, score, checkpoint checksum, config and dataset/split/supervision identities rather than substituting the final epoch. | Hand-calculated partial/non-square/absent-support metrics, predictions in unknown regions excluded from success/failure, non-final-winner/tie regression and inspection of real history/handoff. |
| WI-06-AC-5 | A trainer follows the documented interactive Colab workflow on genuinely reviewed lab data, completes multiple epochs, retains a checkpoint outside transient VM storage, resumes in a fresh runtime and receives a valid selected-checkpoint handoff. Actual environment/resources and limitations are recorded. | Executed notebook/run evidence, durable checkpoint digest before/after runtime replacement, resumed epoch/history, and selection reconciliation. Local/synthetic smoke runs alone are insufficient; missing real data or Colab execution remains unverified and the item stays open. |

All criteria currently **unverified**. G-01 affected ML choices and G-02 proposal
approval precede implementation. G-03 includes real execution and stakeholder
acceptance. G-04 includes checks/docs/commits and sync/archive after required
verification; do not archive WI-06 as completed with AC-5 pending. G-05 release
and numeric lab performance approval remain separate.

## Impact and workflow

Add capability `colab-baseline-training`. Expected files:
`packages/graphene-training/`, `notebooks/01_COLAB_BASELINE_TRAINING.ipynb`,
training-only dependency pins, `docs/14_COLAB_BASELINE_TRAINING.md` and
`docs/review/14_WI_06_VERIFICATION.md`. Reuse dataset/model contracts; no app API,
storage or frontend change. Private data/checkpoints remain under ignored
`.workspace/wi06/` locally or the user's chosen private durable storage.

After explicit approval, refine Issue #6, link
`feat/wi-06-colab-baseline-training` with `gh issue develop 6`, commit approved
planning and implement. Push coherent Conventional Commits and open a PR with
`Closes #6`, criterion evidence and any pending real execution. A PR is not item
acceptance; do not mark complete or merge before the required gates pass.
No protected branch update or subsequent proposal is authorized.
