## Context

The required segmentation classes are background, few-layer and bulk. Missing
few-layer flakes is the primary lab concern; image ranking uses predicted few-layer
coverage. The lab export and physical label boundary remain unaudited. WI-02 fixes
the machine contract without selecting architecture, resolution or operating
sensitivity for real lab images. WI-01 is merged; Issue #2 is reused.

## Goals / Non-Goals

**Goals:** AC-1 unambiguous producer/consumer semantics; AC-2 bounded rejection;
AC-3 no binary-to-three-class interpretation; AC-4 matching tensors and original
coordinates on square/non-square synthetic fixtures.

**Non-Goals:** app import/prediction workflows, actual Colab execution, training,
benchmark selection, dataset masks, CUDA or lab accuracy certification.

## Decisions

### 1. Single-file ONNX bundle and explicit schema

Version 1 is a ZIP with exactly three root regular files: `model.onnx`,
`manifest.json`, `evaluation.json`. No executable Python, pickles, extra files,
directory entries, symlinks, encryption or nested archives. ZIP_STORED and
ZIP_DEFLATED are supported. Strict JSON rejects duplicate keys, non-finite values,
unknown fields and unsupported schema versions; annotations have a defined
metadata field rather than unrestricted structural additions.

The manifest declares:

| Field group | Required meaning |
| --- | --- |
| Schema/identity | Contract version 1; generated model UUID, name, version and descriptive architecture. Architecture never selects a guessed adapter. |
| Artifact | `model.onnx`, lowercase SHA-256, byte size and supported ONNX IR/opset. Bundle digest is computed separately; the manifest does not hash itself. |
| Classes | Ordered IDs/names: 0 background, 1 few-layer, 2 bulk; explicit RGB colors. 255 is a training ignore value, never a predicted channel. |
| Input | Exact graph input name, RGB, float32 NCHW `[1,3,H,W]`, fixed dimensions. |
| Preprocessing | Algorithm version 1, scale 1/255, three-channel mean/std with finite positive std, padding RGB values. No implicit ImageNet normalization. |
| Geometry | `letterbox` or `tiles`; dimensions and mode-specific settings, interpolation and overlap merge version. |
| Output | Exact graph output name; float32 NCHW `[1,3,H,W]` full-input-resolution logits, not probabilities or masks. |
| Decision | `argmax` or explicit few-layer probability threshold; declared tie rule and evidence reference. |
| Provenance | Dataset/split fingerprints, source/license, checkpoint selection, preprocessing, run environment and seed; unknown values marked explicitly with reasons. |

Use JSON Schema as the external specification and one strict typed Python parser
for both consumers. Authoritative fixtures test agreement between schema and parser.
The initial graph profile uses standard ONNX opset 17 and IR versions 8–10, one
input/output, static batch 1, each spatial dimension 32–1024 and divisible by 32.
Fixture sizes are not recommended microscope settings. Unsupported dynamic shapes,
lower-resolution outputs or newer profiles receive an explicit incompatibility
error; exporters must include full-resolution logit upsampling in their graph.

Alternatives considered: accepting arbitrary Keras/PyTorch files retains adapter
guessing and Python deserialization; supporting every ONNX tensor profile now
increases undefined preprocessing/geometry. A narrow versioned profile is reviewable
and can grow after measured exporter evidence.

### 2. Evaluation evidence is distinct from compatibility

`evaluation.json` is required, even for unmeasured packages. It declares either
`unmeasured` with a reason or `reported` with source, dataset/split identity,
checkpoint/settings, metric definitions/support and finite reported results.
Missing class support is explicit; absent results are not converted to perfect scores.
Reported metrics remain supplied claims, not independently verified by import.

Argmax is valid for synthetic fixtures without claiming lab calibration. A
few-layer threshold in `(0,1)` must be explicit and paired with the evaluation
settings/evidence state. The schema never invents or certifies a validated
operating threshold. Later UI separates compatibility from lab validation.
Measured producer/model parity belongs to WI-08; WI-02 uses known synthetic logits.

### 3. Shared preprocessing and inverse geometry

Create an installable library under `packages/graphene-model-contract` supporting
the Colab producer and local consumer. Core dependencies are NumPy/Pillow; ONNX
checker/runtime are validation extras. No PyTorch/TensorFlow/cloud dependency.
Python support is declared/tested explicitly; actual Colab execution remains
unverified until WI-06. Backend adds an optional models extra and lock/source
entry; default account-free health/startup does not import that extra.

Both consumers supply already decoded, correctly oriented uint8 RGB HWC pixels.
File decoding/EXIF/high-bit-depth policy is WI-09. Reject unsupported arrays rather
than silently divide 16-bit images by 255 or swap color channels. Convert to
contiguous float32 NCHW only after geometry: `(RGB / 255 - mean) / std`.

**Letterbox:** scale uniformly to fit the declared tensor dimensions. Round resized
dimensions with floor(value + 0.5), clamp to positive input bounds, resize RGB with
Pillow bilinear, and center-pad using declared RGB values. Top/left receive floor
of half the leftover pixels. Carry exact original/resized sizes and padding in an
immutable geometry record; do not rederive rounding during inverse mapping.
Crop padding from each float32 logit plane, bilinearly restore it to the original
width/height, then make the class decision. Version the float-plane resize routine
and test independent expected coordinate/ramp values. Never resize class-ID masks
with linear interpolation.

**Tiles:** use native-resolution windows equal to tensor size; row-major positions
advance by a declared positive stride no greater than tile size, with a final
edge-anchored position when needed. Pad only images smaller than a tile or partial
dimensions, using the same RGB padding. Accumulate finite logits in original-image
coordinates, average overlapping logits with pixel contribution counts, discard
padding and decide classes once. Every original pixel must receive a contribution.
Process tiles sequentially, never retain an unbounded batch of tile tensors.
The library enforces a configurable original-pixel/accumulator budget before
allocation; initial deployment policy is 16 million decoded pixels.

Geometry limitations are explicit: downsampling can lose flakes, and inverse
mapping cannot restore missing detail. Tests prove coordinate/tensor consistency,
not lossless recovery of arbitrary segmentation boundaries. Resolution/tile stride
for the lab is selected after WI-03; support for both modes is not a recommendation
to train or deploy both.

**Decision:** argmax uses canonical channel order and lower ID for exact ties.
For the few-layer policy, compute stable three-channel softmax after original-size
logit restoration/merging. If `p(few-layer) >= threshold`, emit 1; otherwise choose
the larger background/bulk probability, with background winning a tie. No automatic
threshold optimization or connected-component filtering. Output uint8 mask IDs
0/1/2; coverage denominator is original image width × height in later consumers.

### 4. Bounded archive and graph validation

Proposed initial deployment limits, adjustable by the operator within documented
policy: archive/model 256 MiB, each JSON 1 MiB, expanded total 258 MiB, exactly
three members. These are engineering limits for the assumed 16 GB host, not model
quality or spike-effort requirements. Check metadata and actual streamed bytes;
never trust only ZIP headers or call unrestricted `extractall`.

Reject wrong filenames, duplicate members, absolute/traversing/backslash paths,
symlinks, unsupported compression, malformed JSON, oversize members, CRC mismatch,
wrong digest and schema/class/tensor inconsistencies before returning compatibility.
Validation uses private temporary storage and cleans it on success/failure;
existing workspace records/selection are never changed by this library.

Run model parsing/checking and CPU smoke inference in a disposable child process,
not the FastAPI process. Initial worker policy: 30-second wall timeout, 20-second
CPU limit, 4 GiB address-space limit and one runtime thread. Enforce limits before
native ONNX parsing/session construction. Terminate/reap on timeout and report a
specific bounded failure; never accept an artifact because a check timed out.
Use only CPUExecutionProvider in validation, with no custom-op registration,
profiling/output writes or CUDA initialization.

Require one supported graph input/output matching the manifest. Reject external
tensor data references, nonstandard operator domains, local functions, graph
attributes/control-flow and unsupported sparse representations rather than
resolving files or allowing hidden subgraphs. Bound graph node/tensor declarations
and initializer byte products before runtime initialization. Run the ONNX checker
and verify actual smoke output shape/type and finite logits. Use a deterministic
bounded RGB fixture preprocessed by the shared implementation.

This is resource isolation/compatibility checking, not a claim that a subprocess
is a security sandbox for hostile native-code exploits. Integrity checks do not
authenticate a model publisher. Deployment accepts models from the lab's approved
sources; stronger adversarial isolation is outside this item.

### 5. Acceptance evidence and dependency integration

Use a minimal standard-operator synthetic graph that propagates known spatial
signals into three logit channels. Build a package through a producer helper,
validate/load through a distinct consumer entry, and compare against independent
golden tensor/class/coordinate expectations. Include portrait/landscape, odd
dimensions/asymmetric padding, channels, overlap seams, ties and threshold bounds.
Do not prove agreement solely by calling the same function twice.

Rejection fixtures cover each contract/resource failure, including binary output,
an apparently plausible three-class manifest over a one-channel graph, non-finite
output and worker termination. Small injected limits prove oversize behavior
without allocating huge files. Check failures leave no temporary workers/files
and do not affect WI-01 health/persistence. Record CPU runtime versions and outcomes;
do not claim real lab accuracy, PyTorch export parity or GPU support.

## Risks / Trade-offs

- Narrow profile may reject an eventual exporter -> explicit compatibility reason;
  revisit using WI-08 evidence before adding a schema/runtime profile.
- Preprocessing mismatch can change optical contrast -> one versioned implementation
  and independent golden fixtures; lab suitability still needs real-image review.
- Downsampling misses tiny flakes -> native tiles supported; lab geometry selected later.
- Threshold favors recall at a false-detection cost -> explicit rule/evidence, no
  invented numeric release guarantee.
- Native runtime resource behavior varies -> bounded worker, recorded versions and
  limit-failure evidence. GPU performance is not inferred from CPU smoke success.

## Migration Plan

After explicit approval, create `feat/wi-02-portable-model-contract` linked to
Issue #2, based on the checked-out merged WI-01. Add the shared library/extras
without enabling unfinished app import. No existing models are reinterpreted or
auto-migrated. Preserve default local setup, verify acceptance, commit/push and
open a PR with `Closes #2`. Sync specifications and archive after verification.
Rollback removes the new optional integration through the branch; existing local
metadata/artifacts remain untouched. Main operations remain separately controlled.

## Open Questions for Review

Approval is requested for ONNX-only v1, its fixed tensor/profile semantics, both
geometry modes, explicit decision/evidence states and the proposed resource policy.
These technical choices are explained here so the stakeholder can approve the
concrete design without choosing architecture or training hyperparameters.
Lab geometry, physical labels and calibrated sensitivity are intentionally pending
their data/evaluation work, not blockers for synthetic contract validation.

## Primary References Checked 2026-10-08

- [ONNX checker](https://onnx.ai/onnx/api/checker.html): graph conformance API.
- [ONNX external data](https://onnx.ai/onnx/repo-docs/ExternalData.html): tensors can
  reference separate files; v1 rejects this packaging feature.
- [ONNX Runtime Python API](https://onnxruntime.ai/docs/api/python/api_summary.html):
  explicit execution providers, session options and inference output inspection.
- [ONNX Runtime compatibility](https://onnxruntime.ai/docs/reference/compatibility.html):
  IR/opset and runtime compatibility are separate from architecture/accuracy.

The resource limits and v1 profile above are project proposals, not limits asserted
by these sources. Runtime versions/wheel support will be pinned and tested during
implementation; no dependency installation or model execution occurred in this review.
