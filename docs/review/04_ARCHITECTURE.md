# Architecture proposal

Status: architecture recommended for approval; local-first scope confirmed.

## Deployment and options

Keep React/Vite and FastAPI. Run inference on the lab computer, with CPU as the
required execution path and GPU acceleration optional. Train separately in Colab.

Plan for Linux, 16 GB RAM, and an RTX 3090, as assumed by the stakeholder rather
than inspected hardware. Provide a GPU inference option after validating the
ONNX Runtime CUDA environment, with explicit CPU fallback. Benchmark both. Process
batches of 40 or more images through a bounded queue; avoid decoding the entire
batch into RAM. Thread/batch/tile limits can be configured for stronger hardware.
Colab remains the required portable training workflow even when local GPU
resources are available; no paid cloud resources are authorized by this assumption.

| Persistence option | Benefit | Cost / constraint |
| --- | --- | --- |
| Local filesystem + SQLite | Works without a cloud account; simple installation and backups on one computer. | New persistence adapter; shared lab-computer access needs a deliberate policy. |
| Existing Supabase/accounts | Retains existing users and shared metadata. | Cloud/internet dependency remains even with local inference; ownership and schema need repair. |

The stakeholder selected local-first persistence without mandatory accounts or
cloud services. Use SQLite for metadata and local files for artifacts/results;
remove mandatory Supabase/auth from the initial runtime. Bind to loopback by
default for the lab computer. Any future shared-network access needs an explicit
access policy. The Supabase option above is a considered alternative, not a
parallel first-release implementation. Existing remote data remains untouched.

Use storage/registry boundaries and relative artifact paths so later approved cloud
hosting can replace persistence without changing the model contract. Cloud service
selection, provisioning, account access, and deployment require a later decision.

## Proposed component responsibilities

- Shared Python package: class schema, image preprocessing, tiling, postprocessing,
  dataset validation, and metric definitions used by training and inference.
- Training modules/notebook: data loading, transfer learning, checkpoints,
  evaluation, operating-setting selection, ONNX export, parity checks.
- FastAPI: validate uploads/packages, manage model metadata, run selected-model
  inference, return masks/statistics/provenance, provide training handoff resources.
- ONNX Runtime: execute the supported exported semantic-segmentation graph.
  [Official Python documentation](https://onnxruntime.ai/docs/get-started/with-python.html).
- React: batch input, progress/results, ranking, interactive mask visualization,
  export, model import/details, guided training.

Keep training libraries out of the inference installation where feasible. Limit
supported model formats to a documented package contract; arbitrary Keras,
pickle/joblib, or undocumented state dictionaries are not a useful first-release promise.
Custom models are supported when exported to that contract; broader runtimes are separate work.

## Model package contract

Proposed archive contents: `model.onnx`, `manifest.json`, `evaluation.json`.

Required manifest fields: schema version, model name/version/ID, architecture,
artifact checksum, ordered class IDs/names/colors, RGB input layout/type,
normalization, input shape constraints, resize/tile/padding settings, output
name/layout/semantics, and validated few-layer operating setting.

Training provenance includes source/license, data fingerprint, split identity,
pretrained checkpoint, run configuration/environment, and best checkpoint rule.
Evaluation records dataset/split, class support, matching/metric definitions,
settings, measured results, and whether evidence is measured or user supplied.

Package validation checks supported schema, archive members/size, checksum,
class consistency, graph input/output shape/type, allowed runtime resources,
and a bounded smoke inference. Reject incompatible artifacts before selection.
Do not deserialize arbitrary Python objects during model import.

## Prediction contract and correctness

Each request names a model and operating settings. Return exact model identity,
source filename, decoded dimensions, class-ID mask, overlay/statistics, and timings.
Retain one immutable inference context for the whole request: model session,
preprocessing, class mapping, and settings must not change mid-prediction.

Selection changes cannot silently alter another user's in-flight prediction.
Record the same model identity in downloaded reports and saved results. All masks
are mapped back to original coordinates; overlapping tile logits are combined
before the final class decision. Derived coverage uses a documented denominator.

Apply bounded uploads, image decoding, archive expansion, batch sizes, concurrency,
and runtime thread limits appropriate to the lab computer. Return actionable
errors without secrets, tracebacks, or internal paths. Use a configured API origin
and one frontend client with coherent session-expiry behavior.

If accounts are retained, enforce owner/admin access server-side, prevent public
admin registration, and migrate schema using reviewed, repeatable changes. Existing
data is preserved; destructive migrations and live account actions are not implied
by approval to implement repository changes.
