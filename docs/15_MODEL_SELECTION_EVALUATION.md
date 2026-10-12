# Model selection and evaluation

WI-07 compares the retained WI-06 U-Net/ResNet18 with approved, feasible semantic
challengers. A report binds exact checkpoint bytes, run configuration, dataset,
split, supervision, preprocessing and inference settings. Training runs in
interactive Colab; evaluation can use CPU. Public development aggregates belong
in the review records; source images, weight bytes and detailed panels remain in
private workspace/Drive storage.

## Setup and checkpoint evaluation

Install the four local packages in an isolated environment, in dependency order:

```bash
uv pip install --python .workspace/wi06/venv/bin/python \
  -e packages/graphene-model-contract -e packages/graphene-dataset-contract \
  -e packages/graphene-training -e packages/graphene-evaluation
```

The evaluator accepts retained WI-06 runs without changing their schema or
training source. Use a new output directory for each report:

```bash
graphene-evaluate score READY_DATASET --run RUN_DIRECTORY \
  --checkpoint epoch-000023 --output DEVELOPMENT_DIRECTORY
```

The default role is validation. The finite decision sweep evaluates argmax and
few-layer thresholds 0.2 through 0.8 on the same restored logits. Unknown pixels
(255) never enter the confusion matrix. Panels show original RGB, reviewed
labels, predictions and known-region errors in original image coordinates.
Optional `--cache-logits` stores private original-coordinate arrays.

Use `--size 1024 --geometry letterbox` or `--size 512 --geometry tiles --stride
384` only for the approved finalist geometry screens. These are inference
settings, not extra training runs. Decisions and identity include geometry and
threshold; test execution cannot silently switch them.

## Challenger training and recovery

`graphene-experiment check READY_DATASET --config CONFIG.json` validates support
and the environment before a run. `run` also requires reviewed pretrained
initialization. The configuration uses schema version 2 and one architecture:
`segformer-b0`, `dinov3-vits16-linear`, or the approved fourth-slot fallback
`deeplabv3plus-resnet18`. Keep the common 512 input, batch 2, float32, seed 42,
30 epochs, AdamW and masked CE plus foreground Dice for initial comparisons.

Hugging Face weights require the exact repository commit revision. Weight-byte
hashes are recorded; an optional expected digest enforces a prior admission
record. DINO's encoder stays frozen and in evaluation mode; only its 1x1 semantic
head trains. The DeepLabv3+ fallback replaces only its global-pooling
BatchNorm with 32-group GroupNorm in the randomly initialized decoder, permitting
the final singleton batch of the 31-image role without dropping an image.
No implicit category remapping, background reduction, processor
rescaling or random pretrained substitution is allowed. SegFormer's author
checkpoint is read with restricted `weights_only=True` deserialization under
Torch >=2.6; DINO uses safetensors. Record applicable license/access evidence
before setting `license_approved`. Evaluation approval does not establish
commercial deployment rights.

```bash
graphene-experiment run READY_DATASET --config CONFIG.json --output NEW_RUN
graphene-experiment resume READY_DATASET --run NEW_RUN --checkpoint epoch-000012
```

Each completed epoch carries model, optimizer, scheduler, scaler and RNG states;
completion markers are written last. Configure a separate Drive persistence
path. Resume only the latest completed epoch, with matching data, source and
runtime. An interrupted/incomplete epoch has no authority. Retain the recorded
package bundle across replacement sessions; source edits invalidate recovery.

The challenger runner fully verifies source and retained generations when opening
a persistence session, then checks and copies only newly completed epochs.
It writes each completion marker after all member checksums match. Recovery still
fully verifies every retained generation. This avoids repeatedly rereading the
entire history during each epoch. A successful readback through the current Drive
mount does not establish survival of a runtime disconnect: retain selected/latest
state archives and verify them after remounting or in a replacement runtime.

## Error analysis and resource evidence

Pixel metrics include per-class support, IoU, Dice, precision and recall. Zero
denominators yield null with a reason. Foreground averages use supported reference
classes. Component recall is explicitly a proxy for annotated semantic regions,
not exhaustive physical-flake recall.

Few-layer predictions are 8-connected over the full original image before
masking. Match annotated components one-to-one at supervised IoU >=0.5, maximizing
match count then IoU. Canonical component IDs determine assignment tie order.
Unmatched predictions entirely on known support are counted separately from
unmatched predictions touching unknown pixels. Unknown bridges and touching
flakes can merge semantic components. Full false-detection burden, exhaustive
flake recall and coverage-ranking accuracy remain unavailable.

```bash
graphene-evaluate benchmark READY_DATASET --run RUN_DIRECTORY \
  --checkpoint epoch-000023 --output BENCHMARK.json
graphene-evaluate compare DEVELOPMENT_A/report.json DEVELOPMENT_B/report.json \
  --output COMPARISON.json
```

Benchmarks use two warmups and five repetitions per validation image, one CPU
thread, and record image read/checksum/decode, normalization/inference/restoration
and decision latency, with per-phase timings. Checkpoint/data verification,
model construction/loading and device transfer are measured separately as
initialization. Repeated image reads use the operating system cache; these are
not cold-disk timings. Plotting is excluded. `benchmark --threshold 0.2` binds
timing to the corresponding decision rule. RSS is cumulative process high-water memory, not
model-exclusive RAM. CUDA measurements require actual GPU execution. Comparisons
reject test reports or changed supervision and use shared group bootstrap draws.
Few groups make these exploratory sensitivity estimates. Seed summaries only
combine configurations identical except seed and persistence path.

## Reviewed selection and final test

The stakeholder chooses a Pareto shortlist of at most two from few-layer recall,
component misses, known-region errors and resource evidence. Approved frozen
finalist configurations use seeds 42/43/44. Do not turn a single seed or a hidden
weighted score into a claim of superiority.

After actual stakeholder review, create a freeze naming the selected measured
setting and genuine review evidence:

```bash
graphene-evaluate freeze DEVELOPMENT_DIRECTORY/report.json --output FREEZE.json \
  --reviewer REVIEWER --date YYYY-MM-DD --evidence REVIEW_REFERENCE --setting argmax
graphene-evaluate score READY_DATASET --run RUN_DIRECTORY \
  --checkpoint epoch-000023 --role test --no-sweep --freeze FREEZE.json \
  --output FINAL_TEST_DIRECTORY
```

A freeze is bound to the exact development report, checkpoint and settings. It
is a record of review, not an automatic authorization generated by the software.
Final test contains no reviewed background: foreground and unknown-coverage
limitations remain explicit. Never sweep, rank candidates or retune on test.
An inconclusive development outcome may lead to an explicitly reviewed test
deferral; this must be documented rather than fabricated as a completed result.
