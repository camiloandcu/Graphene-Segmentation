# WI-06 verification

Checked: 2026-10-10. Approved change:
[proposal](../../openspec/changes/archive/2026-10-10-wi-06-colab-baseline-training/proposal.md),
[design](../../openspec/changes/archive/2026-10-10-wi-06-colab-baseline-training/design.md),
[tasks](../../openspec/changes/archive/2026-10-10-wi-06-colab-baseline-training/tasks.md).
Issue: [#6](https://github.com/camiloandcu/Graphene-Segmentation/issues/6).
Branch: `feat/wi-06-colab-baseline-training`. PR: [#20](https://github.com/camiloandcu/Graphene-Segmentation/pull/20)
with `Closes #6`; no merge or protected-branch update. The software is implemented and
CPU-verified and real reviewed-data Colab acceptance criteria pass.
Specifications are synced and the verified change is archived; merge and stakeholder
acceptance are separate.

## Delivered software

- Dataset package 2.0 adds explicit partial schema 2 and keeps dense schema 1
  behavior. Source polygons, reviewed background anchors and supervision identity
  are retained; the consumer reconstructs supervision and rejects invented
  background even when an altered mask's digests are resealed.
- Separate training package 1.0 provides check/run/resume/inspect/persist,
  U-Net/ResNet-18 ImageNet initialization, shared WI-02 letterbox geometry,
  paired flips, ignore-aware CE + foreground Dice and original-coordinate masked
  development metrics. All three classes in train/validation are required before
  download/model/output creation. Test/excluded samples are never scored.
- Completed epoch generations hold safe tensor/state checkpoints, immutable
  history/metadata and completion-last checksums. Full optimizer/scheduler/AMP/
  RNG/data-order restoration, writer exclusion, verified retained copies and
  separate winning/last identity are implemented.
- A thin notebook, common package pins and the
  [setup/recovery guide](../14_COLAB_BASELINE_TRAINING.md) use that same engine.
  Notebook setup is pinned to code revision
  `b0480172dd80181efbd7241b7c8e2853818407f4` (deterministic CUDA loss fix).

Implementation commits: `fc2d9e3` (partial dataset/shared geometry), `845b3ba`
(training engine and regressions), `c885bc6` (persistence isolation), and `12be26b` (native CPU replay/frozen data identity). `85b0cd8` records approved scope/source decisions.

## Acceptance evidence

| Criterion | Status | Verified evidence |
| --- | --- | --- |
| AC-1: validated isolated data | Passed on current reviewed v3 handoff; exploratory limitations retained | Dense compatibility, partial masks/anchors/reconstruction/tamper rejection, public-role loading, no test-role requests and all-class support gates pass. Current v3 has confirmed visual labels and eight reviewed background regions; roles retain 31/4/5. See current preparation/preflight evidence below. |
| AC-2: pretrained optimization/provenance | Passed | Actual ImageNet U-Net optimization completed 30 Tesla T4 epochs with finite loss, CUDA memory/time history, frozen environment/configuration/data identity and encoder checksum. |
| AC-3: durable complete state | Passed | CPU replay/tamper checks pass. After a replacement compute environment lost staged files/packages and the Drive mount, pinned setup and data were restored. Retained epoch 2 was inspected/copied with its unchanged checksum; public resume completed epochs 3–30 in the same run/configuration. Final local and Drive winning identities match. |
| AC-4: original-coordinate best selection | Passed | All 30 original-coordinate confusion matrices preserve validation support; scores recomputed from counts. Earliest maximum is epoch 23 (0.913150140599); selected generation and verified checkpoint checksum match. Test and unknown pixels were excluded. |
| AC-5: real Colab workflow | Passed | Authorized MCP, Tesla T4, Drive, ready reviewed partial dataset, pretrained optimization and replacement-runtime recovery were executed. Full final retained-state inspection and independently reconciled history are recorded below. |


## Checks executed

In the separate `.workspace/wi06/venv` (Python 3.12.13, Torch 2.7.1+cpu,
torchvision 0.22.1+cpu, SMP 0.5.0, NumPy 2.2.6, Pillow 11.3.0,
Pydantic 2.12.3, pycocotools 2.0.10):

```bash
.workspace/wi06/venv/bin/python -m pytest packages/graphene-dataset-contract/tests -q
.workspace/wi06/venv/bin/python -m pytest packages/graphene-model-contract/tests -q
.workspace/wi06/venv/bin/python -m pytest packages/graphene-training/tests -q
OPENSPEC_TELEMETRY=0 openspec validate wi-06-colab-baseline-training --strict
git diff --check
```

Results: **70 dataset tests, 68 model-contract tests, 20 training tests passed**.
The dependency emits NumPy/pycocotools deprecation warnings; source-archive
adversarial tests intentionally emit a duplicate-member warning. Final regression checks pass. A follow-up actual-architecture comparison exposed
small first-epoch numeric variation with multithread optimized CPU kernels; it was
not attributable to missing checkpoint state. CPU replay now explicitly uses native
single-thread kernels, with an actual U-Net state/optimizer regression. Final
pretrained new-process replay evidence is recorded below. An initial model-test collection lacked test-only ONNX/jsonschema
dependencies; after installation all 68 tests passed. Test dependencies remain
separate from the training package and application.

All three wheels were built. A fresh `.workspace/wi06/wheel-venv` installed the
CPU pair, common pins and noneditable wheels. The public dataset CLI checked the
synthetic partial handoff, and the public training CLI safely inspected/resumed a
retained run. The tracked template has 10 cells, empty outputs and valid Python syntax;
Google-dependent execution was initially pending; the later real Colab trial below supplies that evidence. Local Markdown
links and whitespace are checked before submission. Application code/dependencies
were not changed; unrelated frontend/backend suites are not claimed.

## Actual pretrained CPU smoke

Synthetic examples only, authored by the regression fixture; no lab labels or
accuracy claims. Two epochs, input 64, batch 2, seed 42, AdamW/cosine as declared,
float32 CPU, explicit verified local retention. After epoch 1 the retained run was
copied to a new local directory and resumed in a **new Python process through the
public CLI**. It completed epoch 2 and verified the retained winning identity. Under the
native single-thread CPU policy, its actual pretrained model and optimizer tensors
match an uninterrupted two-epoch run exactly. The selected masked synthetic score
is 0.2960342469825792; this is not a lab performance estimate.

The [retained summary](wi06/02_CPU_SMOKE_RECORD.json) records actual losses,
masked scores, support, environment and selected-checkpoint identity.

Official encoder bytes:
`f37072fd47e89c5e827621c5baffa7500819f7896bbacec160b1a16c560e07ec`.
Private reproducible records are in `.workspace/wi06/pretrained-native-smoke/`:
`summary.json`, `cli-resume.json`, `run/`, `recovered/` and `durable/`.
The smoke script is `.workspace/wi06/pretrained-native-smoke.py`; it uses the
tracked synthetic fixture and the committed training package. No weights,
checkpoints or dataset images are committed. The CPU check demonstrates software
behavior; it cannot establish real Colab compatibility, lab accuracy, complete
annotation coverage or generalization.

## Real dataset and Colab execution

Actual source SHA-256:
`344b2ff3bfcf0d18ac206894b92f0b89892f706bc8ef8dbb540a3a7a40da6a34`.
The user authorized the v3 replacement and removal of the previous ZIP; all 40
image bytes are unchanged. The initial v2 review was migrated to explicit partial schema 2
without inventing eligibility/semantic approval, reviewer evidence or background.
Preparation returned **blocked**, 41 review blockers, 621 source polygons and
1,792 source conflict pixels. Unknown supervision totals 157,745,361 pixels.
Background support is zero in both training and validation. See
[the role/support record](wi06/01_DATASET_V3_REVIEW.md#partial-v2-implementation-verification-2026-10-09).
That historical diagnostic had no ready manifest. No model/run was initialized from it.

Subsequently the stakeholder confirmed laboratory human origin and visual semantics,
then approved all eight displayed background candidates. See
[current confirmation, preparation and preflight evidence](wi06/03_LABEL_CONFIRMATION_AND_BACKGROUND_REVIEW.md).
Coverage uncertainty and test isolation remain unchanged; that preparation stage preceded training.
Actual Colab execution now verifies a Tesla T4, Python 3.13.15 and Torch
2.7.1+cu126 with CUDA. Browser reconnection preserved installed packages but
reset notebook cells; restoration and checksum-verified dataset transfer subsequently
passed. A Python-kernel restart resolved stale NumPy without losing staged files.
Drive authorization, mounting and real Colab preflight passed; the dataset archive
is checksum-verified in Drive. The first GPU trial failed before epoch completion
because Torch 2.7 spatial CE reduction rejects strict determinism. Fix `b048017`
uses per-pixel CE with a separate tensor sum; 21 training tests passed and one
CUDA regression was skipped locally. The production loss then passed the actual Tesla T4 strict-determinism regression
with exact repeated values/gradients and zero ignored gradients. The saved Drive
notebook's separate runtime recovered the dataset archive from Drive. Two actual GPU epochs completed and both retained generations were inspected before the runtime interruption.
The replacement environment had no staged repository, dataset, training package or
Drive mount. Pinned installation, Drive authorization and checksum-verified dataset
recovery passed. The retained epoch-2 checkpoint kept SHA-256
`7a3f415ef84dd2e92e4faffd00118d594867d23fe35b1b4e0481013836c1c7a4`;
the public resume completed epochs 3–30 without changing the saved schedule horizon.
The original VM identifier was not captured; replacement evidence comes from the
executable filesystem/package/mount probe, not stale notebook output.

Final local and Drive inspections verified 30 complete generations and the same
winning identity. Independently recomputed all validation Dice scores from their
confusion matrices: each contains exactly 5,642,841 supervised pixels, with class
supports `[262144, 549443, 4831254]`. Earliest maximum is **epoch 23**, foreground
macro Dice **0.913150**. Selected checkpoint SHA-256:
`c199f87a1d3f06f013dbef0db7982c6d4e3e2ba852146c1ca57f735ec25e267f`.
Peak allocated CUDA memory was 0.973 GiB. Per-epoch
training plus validation time ranged from 4.33
to 6.23 seconds; these measurements exclude
checkpoint retention and its Drive I/O overhead.

[Full aggregate provenance/history](wi06/04_COLAB_REAL_TRIAL_RECORD.json) and
[training curves](wi06/05_COLAB_TRAINING_CURVES.png) are committed; images, model
weights, checkpoints and account details remain private. The retained run is under
`MyDrive/Graphene/runs/graphene-baseline-wi06-20261010-002/`; the selected checkpoint
is `epochs/epoch-000023/checkpoint.pt`. The trial JSON and plot are also in
`MyDrive/Graphene/trials/`.

These are exploratory metrics on annotated validation pixels, not independent test
accuracy, exhaustive background recovery or measured layer counts. Unannotated
regions remain unknown, final test was not scored, and other acquisition identities
remain unconfirmed beyond the two approved shared-sample pairs. Regional human
feedback remains future WI-15 scope. WI-07 evaluation/challengers and WI-08 export
are later work items, with no new proposal prepared here. No protected branch was
updated.

WI-06 specification sync, 2026-10-10: main training/dataset specifications updated;
verified change archived as `2026-10-10-wi-06-colab-baseline-training`.
PR #20 awaits review; Issue #6 stays open until merge. No protected branch update.

Final handoff checks: all six current OpenSpec specifications pass strict validation;
19 relevant Markdown files have valid local link targets; tracked notebook Python
syntax and whitespace pass. Production training/dataset/model source checksum
`bb7cfa684aa4d3e9072a2dbf8c9a5b55736422a7b81dffb7ffb41a543e703409`
matches the final run. The affected loss regression remains 21 CPU tests passed,
one local CUDA skip, plus the actual Tesla T4 deterministic-loss regression.
