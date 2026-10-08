## Why

The lab's exported model and the local app must interpret pixels identically.
The legacy runtime guesses framework/classes and converts one binary channel
into three classes. A portable explicit contract prevents those errors before
model import, and gives the Colab exporter one supported target.

## Work Item and Review State

- **WI-02 / Enabler**, parent **INC-01 / F-03**; [Issue #2](https://github.com/camiloandcu/Graphene-Segmentation/issues/2).
- Consumers: Colab exporter, inference runtime and custom-model authors.
- Outcome: one versioned package contract with executable compatibility checks
  and shared preprocessing/geometry, proved with synthetic producer/consumer fixtures.
- Status: explicitly approved by the stakeholder and implemented on 2026-10-08.
  WI-01 is merged. This change does not establish a trained-model claim.
- Source: [WI-02 criteria](../../../docs/review/06_DECISIONS_AND_WORK_ITEMS.md).

## What Changes

- Define a v1 ZIP containing exactly `model.onnx`, `manifest.json`, and
  `evaluation.json`, with explicit identity, checksum, RGB tensor semantics,
  canonical classes, geometry, decision rule and reported evaluation provenance.
- Add an installable shared Python library for the exporter and app. Support
  fixed-shape float32 RGB input and three-channel logits, preserving aspect ratio
  through letterboxing or native-resolution tiles with overlap-logit averaging.
- Validate bounded archives, schema, graph/runtime compatibility and a bounded
  CPU smoke execution. Reject binary outputs, implicit class mapping, unsupported
  graphs, external tensor files and unsafe archive members with specific errors.
- Keep technical compatibility distinct from measured lab usefulness. Synthetic
  or custom packages can explicitly carry unmeasured evaluation; validation does
  not certify their accuracy or invent a sensitivity threshold.
- Document custom export requirements and test producer/consumer agreement,
  known tensor values, original coordinates, and invalid-package boundaries.

## Capabilities

### New Capabilities

- `portable-model-contract`: versioned bundle/schema, bounded compatibility,
  shared preprocessing/inverse geometry and explicit class/decision interpretation.

### Modified Capabilities

None. WI-01 local startup remains usable without model-runtime extras.

## Scope and Non-Goals

Scope: WI-02-AC-1 through AC-4. Library, schema/documentation, bounded validator,
synthetic graph/package fixtures and producer/consumer contract checks.

Excluded: model import/selection UI/API/registry (WI-04), dataset ingestion,
real training/evaluation (WI-03/WI-05 onward), trained-model export parity (WI-08),
production prediction (WI-09), CUDA benchmarking and architecture selection.
Lab resize/tile settings and sensitivity are chosen later using real data.

## Impact

New shared package under `packages/graphene-model-contract`, backend optional model
dependencies/lock entries, contract tests and technical export documentation.
No frontend change, public upload endpoint or mandatory cloud/training dependency.
After approval, create an Issue-linked branch, implement/verify, push, open a PR
with `Closes #2`, then sync/archive the verified change. Protected-branch operations
and the next proposal still require separate approval.
