# Baseline training and recovery

WI-06 delivers a separate training package and a thin
[Colab notebook](../notebooks/01_COLAB_BASELINE_TRAINING.ipynb). Local CPU verification
and synthetic pretrained optimization are recorded in
[the verification report](review/14_WI_06_VERIFICATION.md). Real reviewed-data Colab
training and fresh-runtime resume remain unverified; no lab performance is claimed.

## Dataset readiness

Use a consumer-validated handoff from `graphene-dataset check`. Dense schema 1
continues to require exhaustive annotation. Partial schema 2 explicitly keeps
unannotated pixels unknown (`255`). Magenta cross-class conflicts also remain
`255`; existing nonconflicting foreground labels remain supervised.

Partial background comes only from reviewed polygons wholly inside known
substrate, bound to the source image SHA-256, or from a positively reviewed genuinely
blank image. An anchor records `id`, `class_id: 0`, `image_sha256`, original-coordinate
`polygons`, `evidence`, `reviewer` and ISO `date`. It cannot intersect any source
foreground or conflict. Its geometry is validated with the same COCO rasterizer.
A reviewer can choose a conservative interior substrate patch without claiming
reliable pixel-by-pixel annotation of the entire image. Record the actual evidence;
do not fill approval fields merely to pass validation.

```bash
graphene-dataset prepare SOURCE.zip --partial --output NEW_REVIEW_DIRECTORY
# Review the generated v2 template, including eligibility/semantics/groups/anchors.
graphene-dataset prepare SOURCE.zip --review REVIEW.json --groups GROUPS.json --output NEW_DATASET
graphene-dataset check NEW_DATASET
```

The current private v3 source is under `.workspace/wi06/source/`; its review and
candidate evidence are under `.workspace/wi06/dataset-v3/`. The user-approved
31/4/5 assignment is retained. Lab-human origin/eligibility and visual label semantics are now confirmed by the
stakeholder, with subjective reliability 7/10. The partial-v2 handoff is consumer-valid
with zero review blockers. Eight exact background interiors are stakeholder-confirmed,
four train and four validation; real Colab training/recovery remains pending.
See [the candidate review](review/wi06/03_LABEL_CONFIRMATION_AND_BACKGROUND_REVIEW.md). No completeness attestation was
invented. Regional lab feedback is planned under provisional WI-15; that workflow
will supply traceable Correct/Incorrect/Unsure judgments for later curation,
not automatically create pixel truth. No HITL interface is delivered by WI-06.

Both train and validation must have nonzero supervised support for classes 0, 1
and 2, before any model download or run creation. Resizing must leave usable
supervision in every active sample and all three classes in both roles. The
preflight reports per-image erased classes and original/transformed support.
Test/excluded samples never enter training, selection or evaluation. The entire
artifact is still integrity-checked, including test members.

## Separate installation

Python 3.11–3.13 on Linux. The verified environment is Python 3.12.13 and CPU
PyTorch 2.7.1; current Colab GPU/runtime compatibility must be checked when used.
Pin and retain the exact code revision; do not resume from a floating branch.

```bash
UV_CACHE_DIR=.workspace/wi06/uv-cache uv venv .workspace/wi06/venv --python 3.12
UV_CACHE_DIR=.workspace/wi06/uv-cache uv pip install --python .workspace/wi06/venv/bin/python \
  torch==2.7.1 torchvision==0.22.1 --index-url https://download.pytorch.org/whl/cpu
UV_CACHE_DIR=.workspace/wi06/uv-cache uv pip install --python .workspace/wi06/venv/bin/python \
  -r packages/graphene-training/requirements-common.txt \
  ./packages/graphene-model-contract ./packages/graphene-dataset-contract ./packages/graphene-training
```

For a manually selected Colab GPU runtime, the notebook explicitly installs the
PyTorch 2.7.1/torchvision 0.22.1 CUDA 12.6 wheel pair from the
[official installation matrix](https://pytorch.org/get-started/previous-versions/),
then the common pinned
requirements and local packages. It checks CUDA availability instead of silently
falling back to CPU. Restart after installation if imported packages changed.
No Google account or Drive has been connected by the implementation agent.

## Fixed baseline

Copy [default configuration](../packages/graphene-training/examples/default-config.json)
and choose device, precision and persistence destination deliberately. Defaults:
U-Net/ResNet-18, torchvision ImageNet-v1 encoder weights, RGB, 512-square letterbox,
batch 2, seed 42, 30 epochs, AdamW at 0.001 with weight decay 0.0001, cosine decay
with the fixed 30-epoch horizon, no augmentation, float32 CPU. Optional paired
horizontal/vertical flips apply only to training. AMP float16 requires CUDA.

ImageNet normalization is scale 1/255, mean `(0.485, 0.456, 0.406)`, std
`(0.229, 0.224, 0.225)`, black RGB padding. Shared WI-02 letterbox geometry uses
Pillow bilinear RGB/logits and nearest-neighbor targets. Target padding is `255`.
The actual downloaded encoder bytes and SHA-256 are recorded; unavailable/corrupt
weights fail without substituting random initialization. Internal synthetic test
factories are explicitly marked and are not CLI configuration options.

The loss is valid-pixel mean cross entropy plus equally weighted foreground soft
Dice. Dice includes only foreground classes with positive batch target support;
a background-only batch still contributes cross entropy. Unknown pixels contribute
neither component. An entirely ignored batch fails. The last smaller batch is kept.

Validation uses eval/no-gradient float32 logits, restores logits to the original
image coordinates, then chooses argmax (lowest ID on exact ties). The confusion
matrix excludes unknown pixels. Reported Dice, IoU, precision and recall use
`null` for zero denominators. Foreground macro Dice averages target-supported
classes 1/2. Exact selection ties keep the earlier epoch. These are **masked
supervision metrics**, not evidence of complete-image recall or absence of missed
unannotated flakes. `run.json` includes dataset/split/supervision fingerprints,
unknown fractions, support, configuration, seeds, package/runtime/device versions,
training source digest, checkout revision and weight identity. Epoch history adds
loss, learning rate, elapsed time and peak allocated CUDA memory where applicable.

## Generations and recovery

Each `epochs/epoch-NNNNNN/` contains `checkpoint.pt`, `history.json`,
`metadata.json`, and a completion marker with checksums. Completed generations
are immutable. A writer lock prevents concurrent modifications. Temporary staging
folders are not authoritative and may be removed after verifying no writer owns
the run. There are no mutable `best.pt`/`last.pt` files to disagree with history.

```bash
graphene-train check READY_DATASET --config CONFIG.json
graphene-train run READY_DATASET --config CONFIG.json --output NEW_RUN
graphene-train inspect NEW_RUN
graphene-train resume READY_DATASET --run NEW_RUN --checkpoint epoch-000001
```

Resume requires the latest completed generation, unchanged dataset/splits/
supervision, training source and compatible package/Python/device/precision
versions. A different GPU model is recorded and allowed under the same policy;
bitwise CUDA equivalence is not promised. CPU replay explicitly uses native
single-thread kernels (oneDNN/MKLDNN disabled) to avoid multithread kernel
variation observed during the actual U-Net replay check. Configuration and scheduler horizon
are immutable. Checkpoints load tensors/primitives with `weights_only=True`;
there is no unsafe pickle fallback. Model, optimizer, scheduler, AMP scaler,
Python/NumPy/Torch/CUDA RNG and data-loader generator are restored before the
next iterator. Incomplete-epoch work repeats from the last completed boundary.
CPU regression tests compare uninterrupted and resumed model tensors, metrics,
optimizer progression, scheduler and RNG state.

Choose persistent storage before real Colab training. With `persistence_directory`,
each generation is copied member by member, verified at the destination, and
marked complete last. A failed copy stops training; earlier complete generations
remain recoverable. Drive is not assumed to provide local atomic rename/fsync.
A partial/corrupt destination collision fails: retain its prior complete epochs,
use a new destination for a verified copy, and never overwrite completed evidence.

For manual Drive use: choose your account/access method, mount Drive yourself in
the notebook, set the persistent folder, and confirm `inspect` at that destination.
For download use: create a ZIP of the verified run, download it, retain it outside
Colab, and in a new runtime upload/extract it into a new folder and re-run `inspect`
before resume. `/content` and a second folder in it are both transient. A download
request alone does not prove retention. The notebook requires explicit confirmation
for that evidence and keeps the real trial checklist visible.

A fresh runtime must install the same pins/revision and recover both the reviewed
dataset and completed run. Set `--checkpoint` from recovered `inspect`, never from
a guessed filename. If the environment is incompatible, restore the previous
environment; do not edit fingerprints to bypass the check. If persistence failed
after a completed local epoch, retry `persist` to a valid destination or resume
that latest local epoch; even a fully trained run retries pending persistence.

## Required real trial

After lab eligibility, semantic meaning and background evidence are confirmed,
run multiple pretrained epochs in interactive Colab, record the actual hardware,
retain verified generations outside transient storage, recreate the runtime,
and resume. Reconcile winning epoch/score/checksum with retained history. Keep
AC-5 and the OpenSpec change open until this evidence exists. CPU smoke tests,
synthetic scores and an unexecuted notebook cannot replace it.

WI-06 label/background update, 2026-10-09: laboratory human origin and visual
class semantics are stakeholder-confirmed (subjective reliability 7/10, not measured
accuracy). All eight proposed background interiors are approved, four train and
four validation. Coverage remains non-exhaustive and roles stay 31/4/5. See
[current confirmation and handoff evidence](review/wi06/03_LABEL_CONFIRMATION_AND_BACKGROUND_REVIEW.md).
Earlier pending-label/zero-background statements describe historical snapshots.
Real Colab training and fresh-runtime recovery remain unverified; draft PR #20,
Issue #6 and the OpenSpec change remain open.

For this machine, an official Colab MCP installation is registered in the ignored,
project-local `.codex/config.toml`; reload Codex to load it and authorize its browser
connection. Google Drive is selected for retained checkpoints. See the current
confirmation record for installation/handshake evidence. Registration does not
mean Google authentication or remote training has occurred.
