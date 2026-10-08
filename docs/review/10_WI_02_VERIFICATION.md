# WI-02 verification evidence

Checked: 2026-10-08. Status: approved, implemented and technically verified;
stakeholder acceptance, merge and release remain separate.
Issue: [#2](https://github.com/camiloandcu/Graphene-Segmentation/issues/2).
Branch: `feat/wi-02-portable-model-contract`, linked using `gh issue develop 2`.

## Acceptance

| Criterion | State | Evidence |
| --- | --- | --- |
| AC-1: explicit producer/consumer agreement | Passed | Installable core, generated JSON Schemas, strict parser and cross-document identity checks. Producer builds an Identity ONNX package; a distinct CLI consumer checks it in a CPU worker and matches independently calculated RGB tensors/logits. Explicit background/few-layer/bulk IDs, normalization, geometry, decision, hash and provenance are preserved. |
| AC-2: bounded incompatibility rejection | Passed | Archive metadata preflight and streamed byte limits; paths, duplicate/extra/encrypted/symlink members, CRC/digest mismatch, malformed/duplicate/non-finite JSON and unsupported versions rejected. Worker tests reject unsupported graphs, external tensors, huge declarations, invalid output, and verify timeout/reaping/temp cleanup and address-limit failure. |
| AC-3: binary output never interpreted as three classes | Passed | Wrong channel count, class IDs/order/name, dtype, shape and graph interface rejected. Binary graph regression fails before mask interpretation. Class decisions use explicit logits and fixed IDs. |
| AC-4: shared geometry preserves original coordinates | Passed | Independent RGB/normalization/padding values; portrait, landscape, square and odd padding; pixel-center inverse interpolation; edge-anchored native tiles and overlap means; inclusive threshold/tie fixtures. Actual CPU Identity execution produces expected original-coordinate masks for square/portrait/landscape/tiled cases. |

Synthetic checks establish a software contract. They do not establish microscopy
label validity, trained-model recall, resize/tiling suitability or threshold
calibration. Reported evaluation remains producer-supplied and unverified;
unmeasured packages retain an explicit reason. Compatibility is not accuracy.

## Executed checks

- Shared contract suite: **68 passed**, including actual ONNX CPU execution,
  independently expected tensors/masks and final cleanup/reaping assertions.
- Default app suite: **24 passed** from `backend`, after `uv sync --locked --python
  3.12` removed the shared library, NumPy, Pillow, ONNX and ONNX Runtime. Real
  offline loopback launch/restart and persistence checks passed.
- Locked production-only install and independent real launcher smoke passed;
  fresh interpreter blocks optional model/training/cloud imports and outbound
  connections. Health reports local storage ready and no loaded model.
- Built a standalone wheel. Installed its **core only** in an isolated Python
  **3.10.12** environment; parsed documents, performed geometry/mask smoke and
  accessed bundled schemas. No ONNX/runtime/training/cloud dependencies loaded;
  package validation without the optional runtime returns `missing_runtime`.
- Producer example plus consumer CLI passed with an unmeasured synthetic package,
  CPU provider, shape `[1, 3, 32, 32]`, matching deterministic input/output hashes.
- Ruff formatting and lint passed for shared source/tests/example. Frontend code
  is unchanged; its existing built assets were used by real launcher checks.

Runtime measured for native validation: Python **3.12.13**, NumPy **2.5.3**,
Pillow **12.3.0**, Pydantic **2.13.3**, ONNX **1.23.2**, ONNX Runtime **1.30.0**,
pytest **8.3.5**. The core-only Python 3.10 wheel check used NumPy **2.2.6** and
Pydantic **2.13.5**. Dependency ranges are recorded in the library metadata;
backend native/development versions are locked in `backend/uv.lock`.

Two verification invocation problems were corrected: a sandboxed launcher timed
out with an empty log, and running the app suite from repository root caused four
subprocess `app` import failures. Running the documented command from `backend`
outside the sandbox passed all 24 checks without changing app code or timeouts.

## Reproduction and boundaries

```bash
cd backend
uv sync --locked --extra models --python 3.12
.venv/bin/python -m pytest tests_local ../packages/graphene-model-contract/tests
.venv/bin/python ../packages/graphene-model-contract/examples/make_synthetic_package.py /tmp/synthetic-graphene.zip
.venv/bin/graphene-model-check /tmp/synthetic-graphene.zip
```

See [contract documentation](../10_PORTABLE_MODEL_CONTRACT.md) for standalone
installation, immutable interface rules, error codes and the explicit resource
policy. The synthetic package is an Identity graph, not a trained graphene model.

Default bounds are archive/model 256 MiB, each JSON 1 MiB, total expanded 258 MiB;
worker wall 30 s, CPU 20 s, address space 4 GiB, one CPU thread; geometry 16 million
pixels and 4096 tiles. Archive parsing occurs before native execution. Linux
process limits reduce resource risk; this is not a hostile-code security sandbox.
Use lab-approved packages. GPU and non-Linux native validation are outside scope.

Colab execution, real dataset/model training and validation, PyTorch/ONNX parity,
app import/selection/prediction, lab acceptance and 40+ image batch performance
remain **unverified**, assigned to later Work Items. No app endpoint or UI was
added for model import. The default app still opens in its no-model state.

The verified OpenSpec change is synced and archived before handoff. The PR closes
Issue #2 on merge; no protected branch is updated by this implementation.
