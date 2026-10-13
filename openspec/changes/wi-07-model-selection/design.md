# WI-07 evaluation and experiment design

Status: explicitly approved with the proposal/specifications on 2026-10-11. This is one model-selection
spike. [Proposal](proposal.md) owns scope/effort and numbered acceptance criteria;
[literature review](../../../docs/review/wi07/01_LITERATURE_AND_CANDIDATES.md)
owns source claims. Detailed experiment settings below are proposed for review.

## Fixed data, baseline and isolation (AC-1)

Reuse `.workspace/wi06/dataset-v3/background-confirmed-v2-round-01/` or its verified
private ZIP. Consumer-validate the artifact, preserve approved roles/groups,
and require the dataset/split/supervision fingerprints recorded in WI-06.
Train only on 31 train images; select on four validation images. Five test images
stay isolated until an explicit freeze. Integrity validation may inspect complete
artifact bytes, but must not generate test predictions/panels or inspect its
outcomes during selection. No new split or inferred acquisition grouping.

Canonical classes remain 0 background / 1 few-layer / 2 bulk / 255 unknown-ignore.
Few-layer includes mono under visual lab judgment, not measured layer counts.
Conflict ignores and non-exhaustive coverage persist. Train/validation background
are eight reviewed interiors; test has none. Unknown predictions are not errors
or correct detections by default. Supervision identities cannot change mid-comparison.

Load the WI-06 epoch-23 checkpoint using restricted tensor/state loading, verify
the recorded digest and saved configuration/environment, and reproduce its
argmax validation counts/foreground Dice within declared numeric tolerance.
Before implementation, set that tolerance from the existing float32 geometry
contract; do not adjust it after seeing a disagreement. Record backend/version
differences. A digest, mapping or material count mismatch blocks comparison.

## Candidate admission and training (AC-2)

| Candidate | Initialization/head | Admission and comparison limits |
| --- | --- | --- |
| U-Net/ResNet-18 | Exact retained WI-06 checkpoint; ImageNet encoder origin retained. | Stable reference; do not retrain merely to produce another baseline score. |
| SegFormer-B0 | Pin `nvidia/mit-b0` revision and weight digest; initialize a new three-class semantic decoder, train encoder + decoder. | Verify exact pretrained encoder loading. Disable label reduction; reuse RGB normalization and geometry, with no implicit processor resize or second normalization. Record weight-license review before download/use. |
| DINOv3 ViT-S/16 | Exact approved author checkpoint/revision; frozen encoder in evaluation mode plus trainable 1x1 three-class head on spatial patch tokens. | Approved access/license and finite forward/backward/resource check required. Discard register/class tokens appropriately; reshape spatial tokens using declared patch geometry, interpolate logits to 512 tensor coordinates before common loss/restoration. Record coarse-patch limitation. No silent larger encoder, random weights or different foundation model. |
| 2D-TLK | Faithful author semantic architecture and an identified pretrained FastViT initialization if available. | Require license and reproducible architecture/weights, three logits, class-0/255 semantics, compatible preprocessing and resumable training. If those are unresolved, document exclusion; no guessed reimplementation marketed as the paper's model. |
| DeepLabv3+/ResNet-18 fallback | Same verified ImageNet ResNet-18 encoder as the baseline; new three-class decoder. | Only the fourth-candidate slot if 2D-TLK remains inadmissible. Tests a multiscale decoder while controlling encoder provenance; apply the same loss/geometry/recovery and resource gates. |
| MaskTerial assessment | Public domain-pretrained detector; no synthetic pretraining rerun. | Inspect class-agnostic masks, contrast-classifier assumptions, CPU/export/custom-op requirements and partial-label loss behavior. Executable detection-only validation preview is separate from the complete task. Never map physical 1–4-layer classifiers to visual few/bulk automatically. Full adaptation needs separately reviewed scope. |

The inspected 2D-TLK config currently uses two-class heads, label reduction,
random cropping and a local checkpoint path; GitHub license discovery returned
404. Admission remains closed until those issues are genuinely resolved. A
three-class/ignore-safe adaptation would be explicitly labeled adapted architecture,
not reproduction of its reported benchmark. Use the predeclared fallback if the
gate stays closed; no additional fifth semantic candidate under this proposal.

For admitted semantic challengers, start with WI-06 matched settings: seed 42,
30 epochs, 512 letterbox, float32, batch 2, AdamW learning rate 0.001/weight decay
0.0001, existing cosine horizon, ignore-aware CE + foreground Dice, no additional
augmentation. Select checkpoint by original-coordinate masked foreground macro
Dice, earliest epoch on exact ties. Lower batch with gradient accumulation only
if the resource gate requires it; record effective batch and BatchNorm differences.
No claim that matching hyperparameters is model-optimal. Diagnose unstable or
unconverged candidates; a single justified finalist correction is permitted by
the proposed stage boundary, with original results retained.

Use explicit versioned architecture/config dispatch. Existing WI-06 v1
configuration/checkpoints remain readable and retain their original compatibility
checks. Any new training environment/config starts a new run, not a resume of
an old run. Training dependencies stay separate from the app. Gate runs verify
actual weight tensors, deterministic masked-loss behavior, finite gradients and
durable state before launching a complete candidate run.

## Sessions and finite search (AC-2/4)

Run candidates sequentially in interactive Colab. Persist complete epoch or
equivalent step generations with model/optimizer/scheduler/RNG/precision/data-order
state, history and best identity. Before a session ends, verify the durable copy;
fresh sessions reinstall the pinned candidate environment, restore the same data
and verify the state/config before resume. Prove recovery for the new candidate
runner in a replacement runtime; do not treat WI-06 recovery as evidence for a
different architecture. Never reset the schedule to gain extra epochs on resume.

Maintain a ledger of stage, candidate, config/hash, seed, completed work, runtime,
durable checkpoint and next step. A revoked GPU allocation pauses execution until
a later available day; no guaranteed daily quota and no bypass or paid escalation.
Admission failures and completed runs remain inspectable. Stop candidate expansion
at the reviewed list/stages; ask for a concrete extension if evidence warrants it.

## Original-coordinate metrics and matching (AC-3)

Restore finite float32 logits to original coordinates before all decisions. For
semantic candidates, use the existing lower-class-ID argmax ties. Accumulate
3x3 integer confusion counts on `target != 255`; derive per-class pixel precision,
recall, IoU and Dice, foreground macro IoU/Dice over supported reference classes,
and per-image support/unknown fractions. Undefined denominators are null with a
reason; a predicted class with no target support is not awarded perfect quality.
Report supervised background false-positive pixels separately from bulk-to-few
confusion, with their different denominators and non-exhaustive scope.

Proposed object proxy: deterministic 8-connected components of reference
few-layer masks, not assumed physical flake instances. Predicted few-layer
components are formed on the full original image before support clipping.
For each prediction/reference pair, IoU is computed on the image's supervised
support only. Match eligible pairs at IoU >= 0.5 using maximum-cardinality
one-to-one assignment, then maximum total IoU, then stable component IDs for ties.
No minimum-area cleanup in the initial comparison. Report support, matches,
missed annotated components and component-recall proxy; additionally show target
coverage per component so boundary failure and complete misses are distinguishable.
Unknown-area bridges, touching labels and conflict-induced splits are flagged;
the proxy is not complete flake recall or standard fully annotated instance AP.

Unmatched prediction components wholly within supervised pixels are known-support
unmatched detections under this matching rule. Split them into no reference
overlap and overlap/localization/fragmentation errors. Components intersecting
unknown pixels are indeterminate; count/area/unknown fraction remain visible,
even if a supported match exists. Do not clip into multiple components and then
claim a whole-image false count. Full false detections per image remain unavailable
on current partial coverage; known-support counts are reported with that qualifier.

For MaskTerial, class-agnostic detection support may be measured separately against
annotated foreground; it has no comparable few-layer precision/recall without a
reviewed compatible classifier. No ground-truth boxes/points at inference for
automatic candidate comparisons. No full-image ranking agreement against partial
foreground density: actual coverage ranking is unsupported. Include a null entry
and explain which independent reviewed coverage would be needed.

## Settings, geometry and finalist sensitivity (AC-4)

Cache checkpoint-bound development logits privately; evaluate argmax plus
few-layer thresholds {0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8}. This is a proposed
finite sweep, not calibrated probabilities or release thresholds. Reuse WI-02:
softmax on restored logits, few-layer when p1 >= threshold, otherwise choose
background/bulk with lower-ID ties. No tuning on test; no area/postprocessing
search. Preserve per-class errors while discussing improved few-layer sensitivity.

Shortlist up to two candidates on the validation Pareto trade-off: annotated
few-layer detection/pixel recall, known-support precision/quality and resource
use. Stakeholder reviews pilot errors and picks preferences; no hidden scalar
score or Dice-only final winner. A statistically unclear frontier is a valid result.

Screen 1024 letterbox and native 512 tiles with stride 384/mean-logit merge for
the shortlist using common contract geometry. These inference-only ablations can
change scale relative to training and may worsen predictions; label that shift.
Compare original-coordinate small-component misses, boundary quality and latency.
One declared training adjustment per finalist may address demonstrated resolution
loss or unstable optimization. Freeze each finalist configuration, then run seeds
42/43/44 with per-seed best-development checkpoints. A changed config needs all
three seed runs; do not mix seed results across configurations.

Report min/median/max and dispersion across seeds, and per-image results. Resample
whole reviewed acquisition groups where identities exist, never pixels/flakes
as independent observations. For unknown identities, image-level resampling is
explicitly exploratory; include support counts, method/seed and limitations.
Four development images cannot establish precise generalization or reliable
architectural superiority. Do not present training-seed variation as an independent
test confidence interval. Omit an interval with a reason if support is inadequate.

Panels show original RGB, source supervision/unknown regions, prediction and
original-coordinate misses/confusions with shared sample/component IDs across
candidates. Include every validation image and deterministic error crops; archive
unknown-region detections separately as review candidates, not confirmed errors.

## Feasibility, freeze and handoff (AC-4/5)

Measure training/GPU allocated and reserved peaks, optimization time and total
wall time including validation/checkpoint I/O separately. Measure batch-one CPU
PyTorch end-to-end inference at original input sizes, recording hardware, threads,
backend, environment, geometry, warm-up/repeat counts, median/p95 and peak process
RSS. Include decode/preprocess/restoration/decision time and initialization
separately. Benchmark on the same machine with the same protocol; timings from
papers or Colab GPUs are not local CPU evidence. User lab-hardware equivalence
and acceptable latency/RAM limits are not yet established; record that unknown
and have the stakeholder accept measured feasibility before selection.

For the WI-08 shortlist inspect three-logit/static-input interface, dependency/
custom-op risk, preprocessing/decision reproducibility and expected export path.
This inspection does not claim ONNX parity; WI-08 must verify actual export.
An incompatible detector or unmeasured CPU candidate cannot silently become
the selected local-app model. A feasible slower/higher-quality alternative may
be retained alongside the selected compromise with explicit rationale.

The stakeholder freezes checkpoint SHA-256, architecture, seed, geometry,
preprocessing, decision rule, data/support fingerprints and development report
before any final-test prediction. Choose the actual seed/checkpoint from development
only; do not choose retrospectively by test. Score only that selection on the five
test images once, retaining all limitations. Background recall has zero support;
full false burden and ranking remain unknown. A supported explicit test deferral
is allowed if the stakeholder cannot freeze a meaningful candidate.

Report test outcomes without reopening tuning. A failed exploratory test can
produce an inconclusive recommendation; any subsequent redesign needs a new
reviewed evaluation protocol, with this test no longer treated as untouched.
Provide WI-08 the selected checkpoint/settings/provenance and references to
metrics/support/limitations. Repeated-seed runs are sensitivity evidence, not
an ensemble to export. Full release thresholds and independent physical thickness
validation remain separate.

Use a checkpoint-oriented WI-07 report schema with matrices, per-sample records,
matching/settings/resource definitions, null reasons, gates and freeze provenance.
Do not fake an ONNX model hash/ID to fill the WI-02 package evaluation-v1 schema.
WI-08 later derives its package report from verified checkpoint evidence.

## Finalist transport implementation note (2026-10-12)

The approved U-Net seed stage may use the WI-07 schema-2 experiment runner with
the exact WI-06 U-Net/ImageNet initializer and common loss/data/optimizer/selection
functions. This uses the already verified incremental persistence to avoid full
checkpoint-chain hashing on every save. WI-06 schema-1 source remains unchanged.
New transport trials have new run IDs and an explicit source pin; do not resume
a schema-1 run under the new runner. Fixture full-state parity and a real CUDA
first-epoch parity gate precede using the new transport for U-Net evidence.
Training geometry is the single declared adjustment; transport/schema changes
are recorded separately and never represented as a new architecture or extra
hyperparameter search. Frozen seed cohorts use their declared configuration and
source. Preserve superseded partial trials without ranking incomplete histories.
