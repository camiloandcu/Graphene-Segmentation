# Portable model contract v1

Consumers: Colab export code, the future app model importer, and authors exporting
custom segmentation models. This contract makes tensor/class/coordinate behavior
explicit; passing validation does not prove that a model finds graphene accurately.

## Install and check

The local workspace still starts with its default lightweight installation. For
contract development/CPU validation from the repository:

```bash
cd backend
uv sync --locked --extra models --python 3.12
.venv/bin/graphene-model-check /path/to/package.zip
```

For an exporter or separate environment, install the shared package alone:

```bash
python -m pip install './packages/graphene-model-contract[validation]'
graphene-model-check /path/to/package.zip
```

Omit `[validation]` for core schema/geometry only. The core requires NumPy, Pillow
and Pydantic, never PyTorch/TensorFlow/cloud clients. CPU checking is Linux-specific;
no CUDA initialization is performed. Core is Python 3.10–3.13 compatible; actual
Colab notebook execution remains a later Work Item.

## Required bundle

Exactly three root regular files in a ZIP (stored or deflated):

| Member | Meaning |
| --- | --- |
| `model.onnx` | One static float32 RGB input and one three-channel logit output. |
| `manifest.json` | Identity, hash/size, class mapping, tensors, normalization, geometry, decision and provenance. |
| `evaluation.json` | Same identity/settings and explicitly unmeasured or supplied reported evidence. |

No external tensor files, nested paths, directories, symlinks, duplicate members,
encryption, extra files or arbitrary Python checkpoints. SHA-256 checks integrity;
it does not authenticate the author. Models must come from the lab's approved
sources; resource-limited subprocess validation is not a hostile-code sandbox.

Structural JSON schemas ship inside the wheel:

- `graphene_model_contract/schemas/manifest-v1.schema.json`
- `graphene_model_contract/schemas/evaluation-v1.schema.json`

The parser additionally checks cross-field/document consistency. The validator
checks the actual graph and resource bounds. JSON Schema alone cannot certify
those invariants. Duplicate keys, non-finite numbers (including overflow exponents),
boolean substitutes for numeric literals and unknown structural fields are rejected.

## Tensor profile and classes

Version 1 uses standard ONNX opset 17, declared IR 8/9/10, no custom domains/local
functions/control-flow/subgraphs, no external or sparse tensors. Both input and
output have `[1,3,H,W]`, with fixed H/W from 32 through 1024, divisible by 32.
Tensor names match the manifest; output is float32 **logits**, not probabilities,
argmax masks or a single binary channel. Include full-resolution logit upsampling
in the exported graph if the architecture's segmentation head has lower resolution.
The architecture name describes the model and never selects an inferred adapter.

| ID | Name | Interpretation |
| --- | --- | --- |
| 0 | background | Not labeled as few-layer/bulk. |
| 1 | few-layer | Lab taxonomy includes mono-layer; physical label review remains pending. |
| 2 | bulk | Lab bulk class; external thick-graphene equivalence is not yet validated. |
| 255 | training ignore only | Never a model output channel or predicted ID. |

Colors are explicit RGB triples. Source datasets map their own categories through
reviewed names/aliases; COCO IDs must not be assumed to match these IDs.

## Preprocessing and coordinates

Callers supply correctly oriented **uint8 RGB HWC** arrays. The library checks
shape/depth, but cannot infer whether an array was incorrectly decoded as BGR.
Image decoding, EXIF and high-bit-depth handling belong to the later prediction
boundary. Do not silently rescale microscopy intensities or discard bit depth.

Core preparation converts after geometry to contiguous float32 NCHW:
`(RGB * float32(1/255) - mean) / std`. Mean, positive std, padding RGB and algorithm
version must be declared; ImageNet statistics are never guessed.

**Letterbox:** resize RGB bilinearly at uniform fit scale; round dimensions with
floor(value + 0.5); center-pad with floor(leftover/2) on top/left. Retain the exact
immutable geometry record. Restore float-logit planes by cropping that padding
and Pillow bilinear resize to original size, then select class IDs. Never interpolate
class-ID masks linearly. Downsampling can lose flakes; inverse geometry cannot
recover that information.

**Native tiles:** row-major fixed-size windows, declared vertical/horizontal stride,
final edge-anchored windows and bottom/right padding only when smaller than a tile.
Average overlapping original-coordinate logits using contribution counts; exclude
padding and decide once after merging. Duplicate/unexpected/missing tiles are
errors. Prepare sequentially; do not retain every tile tensor. Limits are applied
before accumulator/position allocations: 16 million original pixels and 4096 tiles
by default, adjustable through `GeometryLimits` for stronger hardware.

The lab's actual input resolution, tile stride and preservation of tiny flakes are
unmeasured; WI-03 and model evaluation determine these. Synthetic contract fixtures
prove consistency and coordinate alignment, not microscope segmentation accuracy.

## Decision and evidence

`argmax` selects the largest original-coordinate logit, with lower class ID winning
an exact tie. `few_layer_threshold` computes stable three-channel softmax after
reconstruction and emits few-layer when its probability is **at least** the
explicit threshold in `(0,1)`. Otherwise it selects background/bulk, with background
winning a tie. Masks are uint8 IDs 0/1/2.

Thresholds are not automatically optimized or certified. Evaluation copies the
manifest's preprocessing/geometry/decision/checkpoint and model ID/hash. A mismatch
is rejected. Provenance values are `known` with a value or `unknown` with a reason;
no dataset fingerprint or checkpoint selection rule is fabricated.

Evaluation is either:

- `unmeasured`, with a reason; allowed for synthetic or compatible custom packages.
- `reported`, with supplied source, known matching dataset/split fingerprints and
  metrics carrying definition, support, unit and value or an unavailable reason.

Absent class support cannot receive a perfect fraction metric. Supplied metrics
remain reported claims; the CLI always outputs `evaluation_verified: false`.
Lab acceptance of recall/false detections still requires measured independent
review. No numeric release guarantee is implied by a compatible package.

## Developer API

```python
from pathlib import Path
from graphene_model_contract.package import validate_file
from graphene_model_contract.geometry import prepare_letterbox, restore_letterbox, decide

checked = validate_file(Path("model-package.zip"))
prepared = prepare_letterbox(decoded_rgb, checked.manifest)
# Later inference uses the declared model/session and prepared.tensor.
original_logits = restore_letterbox(model_logits, prepared.geometry)
class_mask = decide(original_logits, checked.manifest)
```

Native tile consumers use `prepare_tiles`, `TileAccumulator.add` and `.finish`.
An eventual app prediction request still needs immutable model selection and
provenance; this library does not implement that endpoint or registry.
Producer code uses `build_package(model_bytes, manifest, evaluation)` after exporting
ONNX, declaring actual checksum/size and parsing its two documents with `parse_contract`.
The producer and consumer both run compatibility validation. Keep training/resume
checkpoints separate from the inference ZIP.

## Bounds and errors

Default `ValidationLimits`: archive/model 256 MiB, each JSON 1 MiB, total expansion
258 MiB, central directory 1 MiB, exactly three members, 10,000 graph nodes and
512 MiB total declared constant tensor storage. Known intermediate tensor shapes
are also bounded. These are configurable engineering policies, not model-quality
requirements; unsupported limits cause explicit rejection.

Before native ONNX/NumPy session loading, the child receives 4 GiB address-space,
20-second CPU and 30-second wall-time bounds, one runtime thread, bounded result
writes and no core dumps. The parent kills/reaps timed-out workers and cleans
private temporary files. Native stderr/traces/paths are not exposed. Validation
never changes current workspace records/selection.

`ContractError.code` examples: `invalid_json`, `invalid_schema`, `evaluation_mismatch`,
`archive_members`, `archive_integrity`, `archive_limit`, `expanded_limit`,
`checksum_mismatch`, `graph_interface`, `external_data`, `unsupported_graph`,
`tensor_limit`, `invalid_logits`, `validation_timeout`, `worker_failed`,
`missing_runtime`. Geometry adds `invalid_pixels`, `image_limit`, `tile_limit`,
`geometry_mismatch`, `invalid_tile` and `missing_tile`.

## Reproduce contract checks

```bash
cd backend
uv sync --locked --extra models --python 3.12
.venv/bin/python -m pytest tests_local ../packages/graphene-model-contract/tests
cd ..
backend/.venv/bin/python packages/graphene-model-contract/examples/make_synthetic_package.py /tmp/synthetic.zip
backend/.venv/bin/graphene-model-check /tmp/synthetic.zip
```

The Identity graph example is **not a trained model** and must never be used for
lab screening. Actual Colab training, real-model ONNX parity, app upload/selection
and prediction are separate Work Items. [WI-02 evidence](review/10_WI_02_VERIFICATION.md)
records measured checks and remaining limitations.
