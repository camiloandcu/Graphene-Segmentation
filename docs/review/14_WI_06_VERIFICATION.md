# WI-06 verification

Checked: 2026-10-10. Approved change:
[proposal](../../openspec/changes/wi-06-colab-baseline-training/proposal.md),
[design](../../openspec/changes/wi-06-colab-baseline-training/design.md),
[tasks](../../openspec/changes/wi-06-colab-baseline-training/tasks.md).
Issue: [#6](https://github.com/camiloandcu/Graphene-Segmentation/issues/6).
Branch: `feat/wi-06-colab-baseline-training`. Draft PR: [#20](https://github.com/camiloandcu/Graphene-Segmentation/pull/20)
with `Closes #6`; no merge or protected-branch update. The software is implemented and
CPU-verified; required real reviewed-data Colab evidence remains unverified.
The change stays active, with no completed spec sync/archive or item acceptance.

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

| Criterion | Status | Verified evidence / missing evidence |
| --- | --- | --- |
| AC-1: validated isolated data | Passed on current reviewed v3 handoff; exploratory limitations retained | Dense compatibility, partial masks/anchors/reconstruction/tamper rejection, public-role loading, no test-role requests and all-class support gates pass. Current v3 has confirmed visual labels and eight reviewed background regions; roles retain 31/4/5. See current preparation/preflight evidence below. |
| AC-2: pretrained optimization/provenance | Local synthetic pretrained evidence passed; real Colab unverified | Actual ImageNet encoder and U-Net optimization, finite losses, three logits, full provenance and new-process CLI resume pass on CPU. Actual lab/GPU memory and runtime are not measured. |
| AC-3: durable complete state | Local CPU state/recovery checks passed; real VM trial unverified | Uninterrupted/resumed tensors and metric history match; scheduler/RNG/data order match. Failed epoch repeats; corruption/mismatch/unsafe pickle fail; prior durable epoch survives copy failure; a retained pretrained run resumes in a new Python process. Drive mounting and dataset retention pass; no completed lab checkpoint or Colab VM recovery yet. |
| AC-4: original-coordinate best selection | Synthetic software checks passed; real handoff unverified | Hand-calculated original-coordinate counts exclude padding/unknown, absent denominators yield null, non-final winner and earlier exact ties pass; best checksum is reconciled with generations/history. No real-lab winning checkpoint exists. |
| AC-5: real Colab workflow | Unverified | MCP, GPU setup, authorized Drive mounting, dataset retention and real preflight pass. First GPU optimization failed before epoch completion; successful lab epochs and fresh-VM resume remain pending. Synthetic/local evidence is insufficient. |

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
retained run. The notebook has 10 cells, empty outputs and valid Python syntax;
no Google-dependent cell or full Colab notebook was executed. Local Markdown
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

## Real dataset and remaining work

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
Coverage uncertainty and test isolation remain unchanged; no real training was run.
Actual Colab execution now verifies a Tesla T4, Python 3.13.15 and Torch
2.7.1+cu126 with CUDA. Browser reconnection preserved installed packages but
reset notebook cells; restoration and checksum-verified dataset transfer subsequently
passed. A Python-kernel restart resolved stale NumPy without losing staged files.
Drive authorization, mounting and real Colab preflight passed; the dataset archive
is checksum-verified in Drive. The first GPU trial failed before epoch completion
because Torch 2.7 spatial CE reduction rejects strict determinism. Fix `b048017`
uses per-pixel CE with a separate tensor sum; 21 training tests passed and one
CUDA regression was skipped locally. Real CUDA regression, successful lab
training, retained checkpoints and recovery acceptance remain unverified. See the linked live setup record.

Remaining authorized work once real inputs exist: choose Google account/access/persistence method, execute multiple
pretrained Colab epochs, retain verified generations, recreate runtime and resume,
and record/reconcile actual winning checkpoint evidence. Coverage uncertainty stays
non-exhaustive; regional human feedback remains future WI-15 scope. Then finish
required acceptance, sync specifications/archive the change, and update the PR.
No later OpenSpec proposal has been prepared and no protected branch is updated.
