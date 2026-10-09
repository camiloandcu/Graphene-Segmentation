# WI-06 baseline training design

Status: revised for v3 partial supervision; explicitly approved on 2026-10-09.
Unknown-pixel handling and the 31/4/5 grouped assignments are stakeholder approved.

## Architecture and consumer

Add `packages/graphene-training/` as a separate Python package/CLI. The Colab
notebook installs a recorded repository revision and the training environment,
then calls the same reusable validation, train, resume and inspect functions as
local verification. Do not invoke the legacy backend training service or import
Supabase/MLflow. The app, dataset contract and model-contract core retain their
lightweight dependencies. The consumer receives a training checkpoint and run
record; WI-08 later reconstructs this architecture without arbitrary Python
objects and exports the selected state.

Proposed commands: `graphene-train check DATASET --config CONFIG.json`,
`graphene-train run DATASET --config CONFIG.json --output NEW_RUN`,
`graphene-train resume DATASET --run RUN --checkpoint GENERATION` and
`graphene-train inspect RUN`. Notebook cells provide guidance and display
results; they do not contain a second trainer. Invalid inputs fail before model
initialization, weight downloads or output mutation, with actionable reasons.

## Dataset boundary and isolation (AC-1)

Call `graphene_dataset_contract.check` before processing samples and use its
`iter_samples` API for explicit train/validation roles, retaining its use-time
digest checks. No image/mask globbing, source-ID remapping, raw-COCO fallback or
automatic split repair. Whole-artifact validation can inspect test file integrity;
the training adapter never yields test/excluded images for gradients or scoring.

Support dense dataset-v1 and explicit partial dataset-v2 through the same validated
consumer boundary. The active source is the checked v3 ZIP; old v2 numeric sample
IDs cannot be reused. Its approved assignments are 31 train / 4 validation / 5 test.
Require canonical RGB uint8 images and original-size masks with 0/1/2/255.
Report effective sample IDs, source/evaluation limitations and aggregate support.
Both train and validation must have positive reviewed background, few-layer and bulk support;
this is a stricter baseline training prerequisite than WI-05 structural readiness.
Missing support requires reviewed data decisions, never automatic reassignment.
An exploratory manifest permits an explicitly exploratory pilot, without a claim
of physical independence or lab generalization. Synthetic fixtures are labeled
synthetic in run evidence and cannot be promoted to real-data acceptance.

## Explicit partial-dataset contract (AC-1/2/4)

Extend `graphene-dataset-contract` with separate review/manifest-v2 schemas and
explicit `supervision_mode: partial`. Preserve dense v1 validation and semantics;
the v1 parser must reject v2 rather than silently infer background or bypass
eligibility. A source/version-bound partial review records annotation origin,
eligibility, class meaning, unknown coverage, conflicts, original/effective roles,
groups and all candidate dispositions. Partial readiness does not require claiming
exhaustive annotation, but still requires genuine review of the labels actually used.

Retain eligible source polygons as classes 1/2. Start every unannotated pixel as
255. Cross-class intersections remain 255 under the approved policy. Class 0 is
supplied only by source-bound reviewed background regions or verified material-free
images, with evidence/reviewer/date and original-coordinate geometry. Selecting
conservative interior regions or controls does not require precise full-object
boundaries. Never generate negative anchors from absence of source polygons,
color heuristics, model confidence or an automatically eroded prediction.

Background anchors are bounded polygons in the existing supported geometry;
reject stale image hashes, malformed/out-of-bounds geometry and intersections
with foreground source labels. They cannot override overlap-ignored pixels or
silently replace source labels. Verified background-only source images need their
own genuine provenance, as in v1. Every other unannotated pixel remains 255.
Record anchor IDs/evidence/digests, source support versus supervised support and
counts by ignore reason. Anchors for validation are frozen before optimization;
test remains excluded from selection. No anchor is currently supplied for the
active v3 dataset; preserve that real-run blocker.

Versioned dataset identity includes mode, supervision masks, anchors/reviews and
their byte/pixel digests. Split identity retains the existing group/role invariant.
Also expose a supervision fingerprint over sample identities, class/unknown masks
and anchor provenance; store it in run/checkpoint/metric records. Source changes
invalidate review binding. Changed anchors/coverage change supervision and dataset
identity and prevent resume even if the original image/split is unchanged.

Consumer validation reconstructs/validates supervised masks against declared source
polygons, reviewed anchors and ignore policy, not merely legal byte values. It
checks complete inventory, bounds, review and fingerprints before iteration and
at use time. Publish complete v2 outputs atomically under the WI-05 no-overwrite
contract; diagnostics and `.workspace/wi06/dataset-v3/partial-mask-preview/` are
not ready artifacts. Test dense-v1 compatibility and partial-mode contamination,
missing/tampered anchors, false-background promotion and changed supervision.

## Baseline and transforms (AC-2)

Use `segmentation_models_pytorch.Unet`, `encoder_name="resnet18"`,
`encoder_weights="imagenet"`, three RGB input channels and three output logits,
without an output activation. SMP documents pretrained encoders and associated
[preprocessing](https://smp.readthedocs.io/en/latest/quickstart.html), including
[ResNet-18 support](https://smp.readthedocs.io/en/latest/encoders.html).
Record weight identifier, actual source, file digest and encoder initialization
status. Resume reconstructs with weights disabled before loading saved state;
it does not redownload/reinitialize pretrained parameters. Network/download
failure stops a new pretrained run; offline cached weights must match identity.

Proposed resolved defaults: 512 x 512 input, batch size 2, seed 42, 30 planned
epochs, AdamW LR 0.001/weight decay 0.0001, cosine schedule over the fixed epoch
horizon, equal CE and foreground soft-Dice coefficients, no class weighting.
These are configurable pilot settings, not an agreed compute budget or measured
optimum. Persist the fully resolved settings before optimization. Batch-size or
horizon changes create a new run rather than silently adapting an OOM/resume.
Allow a positive batch size and retain the smaller final batch; do not drop
training images to force equal-size batches. Verify the supported spatial input
and batch shapes against the encoder during the setup check.

Reuse WI-02 normalization and letterbox geometry through a shared adapter, without
fabricating an inference manifest/model identity. If a small geometry refactor is
needed, keep existing public behavior and regression coverage unchanged. Explicit
ImageNet mean `[0.485, 0.456, 0.406]`, std `[0.229, 0.224, 0.225]`, scale `1/255`
and RGB padding `[0, 0, 0]` are recorded and checked against encoder metadata.
Use shared uniform fit/floor(value + 0.5)/center-padding behavior for RGB;
resize masks with nearest neighbor to the exact recorded resized dimensions and
fill all padding with 255. Do not treat padding as background supervision.

Default augmentation is disabled. Optional horizontal and vertical flips have
explicit probabilities, apply to paired train images/masks only, and are seeded.
No crops, rotations, color/illumination changes or validation augmentation in
this baseline. Count target support before/after resize and disclose erased
foreground; reject an all-ignore transformed sample or lost aggregate foreground
support. Per-image small-flake loss remains a reported limitation.

CE is the mean over valid pixels. Foreground soft Dice computes probabilities
from logits with ignored targets/probabilities masked out, over the batch, and
averages classes with positive batch target support. Unsupported batch classes
are omitted from that term and still receive CE supervision; a background-only
batch has zero Dice term. Record the smoothing constant and formula. No gradient
or denominator includes 255; entirely ignored batches fail clearly.

Use single-process loading (`num_workers=0`) for reproducible epoch recovery.
Enable mixed precision only on compatible CUDA execution, otherwise float32,
recording the actual mode. Seed Python/NumPy/Torch/data order; record deterministic
settings. Nonfinite loss/logits or OOM stop with the last completed checkpoint
intact. CPU tests establish deterministic recovery on their recorded environment;
different CUDA runtimes need state continuity, not a bitwise equality claim.

## Development scoring and best selection (AC-4)

Validation is deterministic, in evaluation mode without gradients. Restore float32
logits to each original image using WI-02 inverse letterbox, then apply canonical
argmax (lower ID wins ties). Score against original masks; transformed training
masks and padded pixels cannot become validation ground truth. Partial v2 scores
only its frozen supervised pixels; original unannotated/ignored regions are not
counted as false positives, true positives or true negatives. Report original
pixel count, supervised per-class support, unknown count/fraction and the
supervision fingerprint. Metrics are explicitly masked development measurements,
not whole-image precision/recall, complete flake recall or verified coverage.

Accumulate a 3 x 3 confusion matrix on non-ignored original pixels over all
validation samples. For class c, TP = diagonal, FP = column minus TP and FN = row
minus TP. Dice = 2TP/(2TP+FP+FN), IoU = TP/(TP+FP+FN), precision = TP/(TP+FP)
and recall = TP/(TP+FN). Zero denominators yield unavailable with a reason, never
one; unsupported target classes are reported and excluded from selection averages.
Log support, all per-class fractions, few-layer precision/recall, foreground macro
Dice/IoU and validation loss with its transformed-resolution definition.

The selection score is mean Dice for target-supported foreground classes 1 and 2;
the baseline support prerequisite ensures both participate. Choose the highest
finite score; exact ties retain the earlier epoch. Keep separate last and best
identities. Restore/inspect the winning state after training and reconcile its
epoch/score/digest against history. This surrogate is not flake recall, a lab
operating threshold, an independent test result or WI-07 acceptance.

## Run records and checkpoint contract (AC-2/3/4)

Versioned JSON configuration/run records contain dataset/split fingerprints,
effective-role IDs, source revision, actual dependency/Python/Torch/CUDA/cuDNN/GPU
versions, pretrained weight identity, supervision mode/fingerprint and frozen
anchor evidence, normalization/geometry, loss and selection
definitions, RNG policy, optimizer/scheduler horizon and evaluation limitations.
Capture measured per-epoch elapsed time and peak CUDA allocation; CPU or unavailable
resources carry explicit reasons. A resolved-config digest excludes paths/run
timestamps but includes every setting that affects continuation.

Checkpoints contain state dictionaries and tensors/primitives only: model,
optimizer, scheduler, AMP scaler if active, Python/NumPy/Torch/CUDA RNG states in
restricted-load-compatible form, data-order generator, next epoch, best score and
best-checkpoint reference. JSON metadata/history carry the identities and digests.
Use `torch.load(..., weights_only=True, map_location="cpu")`; no unrestricted
pickle fallback or serialized module instances. PyTorch describes restricted
[loading](https://docs.pytorch.org/docs/2.14/notes/serialization.html) and the
optimizer/epoch state needed for
[resume](https://docs.pytorch.org/tutorials/beginner/saving_loading_models.html).
Restricted loading and hashes verify format/integrity, not trusted authorship.

Each completed epoch publishes an immutable generation containing checkpoint,
history and metadata checksums with a completion marker written last. Write to
owned staging and validate before publication. Keep prior generations intact;
last/best references point only to complete verified generations. Restore by
loading a specifically selected complete generation, not the newest filename.
Partial checkpoint/history/marker writes never qualify. Reject missing/wrong
digests, unsupported schema/state, changed config/data/split/supervision/source/dependency
versions or device/precision policy before restoring/mutating output.

The immutable generation is authoritative; references are derived and recoverable
if interrupted. Resume rolls back incomplete work to the saved history boundary,
restores all state before creating the next data iterator, and records a resume
event. A partially completed epoch is repeated from the last complete boundary.
Prevent concurrent writers to the same run. Loading a different GPU with the same
validated environment/policy is recorded; unsupported state changes fail clearly.

## Notebook, persistence and real execution (AC-5)

Notebook order: explain data/compute requirements; install the recorded revision
and pinned training profile; report environment/GPU; choose local dataset/run paths
and explicit persistence; check the dataset/configuration; start training; inspect
curves/best identity; verify durable copy; recreate runtime and resume; inspect
the selected-checkpoint handoff and remaining evaluation/export steps.

Colab documents transient VMs, variable resources and manual Drive permissions in
its [FAQ](https://research.google.com/colaboratory/faq.html). Do not require paid
compute, guarantee a GPU, or operate the runtime as an app server. No automatic
account connection or background remote controller. Choose MCP versus manual
before account actions; provide manual instructions until waived for that service.
The notebook offers user-initiated Drive persistence or explicit downloadable
generations. New Drive mounting is an explicit cell, not a setup side effect.

Read images from runtime-local validated data. For external persistence, copy each
complete generation, verify destination checksums and mark completion last. Do not
assume local atomic rename/fsync provides Google Drive transactional durability.
An interrupted copy preserves the previous verified generation. Training reports
a persistence failure and stops at that boundary rather than claiming recoverability.
Downloaded artifacts require the user's explicit retained-copy verification;
files under `/content` alone never establish durable recovery.

Actual acceptance requires reviewed real lab data, multiple completed epochs,
independent checkpoint retention, runtime replacement, resumed optimization and
reconciled selection history. Record executed notebook/run evidence privately and
publish only non-sensitive verification summaries. Do not upload raw microscopy
data or reviewer identities through automated tooling without account authorization.
Keep AC-5 pending when these inputs are absent, even if all CPU tests pass.

## Verification, handoff and limits

Use synthetic reviewed dense and partial datasets for loader isolation/tampering/support checks,
non-square geometry and ignore/loss/metric cases. Compare uninterrupted and
epoch-resumed CPU optimization, model/optimizer/scheduler/RNG/history, and best
identity on the same environment. Exercise earlier best/ties, failed writes,
partial/mismatched/corrupt generations, unsupported environment and persistence
failure. CPU random-weight fixtures are labeled fixtures, never pretrained evidence.

Install/test the training wheel separately and validate notebook syntax/cell order.
Pin a coherent training dependency profile during implementation and record actual
Colab compatibility; docs alone do not verify it. Run affected dataset/model
contract regressions, strict OpenSpec and whitespace/link checks. No frontend/backend
build is needed unless those paths change.

Update `docs/review/14_WI_06_VERIFICATION.md` with AC-1–5 passed/failed/unverified,
branch/Issue/PR, actual checks and remaining inputs. Do not sync/archive this change
as completed with required real execution pending. Handoff to WI-07/08 consists
of the selected training-state digest, architecture/configuration, preprocessing,
dataset/split/supervision identity and explicitly masked exploratory development
evidence. The regional human-review UI remains a separate provisional candidate;
no predicted mask or vote is automatically admitted to training.

## Verified CPU replay implementation detail

CPU replay uses native single-thread kernels with oneDNN/MKLDNN disabled and
records that policy. Multithread optimized CPU kernels produced small first-epoch
numerical differences on the actual U-Net despite equal seeds and restored RNG.
The native policy supports the approved deterministic CPU comparison; CUDA keeps
its explicitly recorded precision/determinism policy without a bitwise cross-GPU
promise. Role loading also rejects a dataset fingerprint changed after preflight
and freezes matching source sample identities before optimization.
