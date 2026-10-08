# WI-05 validated dataset verification

Checked: 2026-10-08. Proposal/design/specs explicitly approved by stakeholder.
Status: software contract implemented and technically verified; stakeholder
acceptance/merge and genuine real-label/split readiness remain pending.
Issue: [#5](https://github.com/camiloandcu/Graphene-Segmentation/issues/5).
Branch: `feat/wi-05-validated-labeled-datasets`, linked with `gh issue develop 5`.
Approved-design commit: `8447823`. Implementation/PR references are recorded below.

## Observable result

The offline Python package/CLI validates the supplied polygon ZIP, requires an
explicit source-bound human review, and publishes a complete immutable directory
only when annotation eligibility and split invariants pass. The same consumer
validator rejects missing/tampered files, prediction contamination, invalid masks
and incomplete/diagnostic directories before yielding training samples.

Two real-source preparations reproduced **40 images, 759 annotations, 10 conflict
images and 10,578 conflict pixels**, with all source bytes, decoded RGB digests,
class support and all 40 decoded masks matching WI-03. The source was unchanged.
All 15 WI-03 grouping candidates are retained, including the two cross-split pairs.
The real source correctly produces a **blocked** report and no ready manifest:
physical-category, eligibility/completeness, conflict and split/group decisions
have not been supplied. Stakeholder acceptance of WI-03 was not substituted for
those decisions.

Two reviewed synthetic handoffs reproduced dataset and split fingerprints. The
consumer iterated one sample each in train, validation and test with original
6×10 geometry and canonical 0/1/2 masks. Fixture reviews explicitly describe
synthetic data and exploratory limitations; they are never applied to real labels.

## Acceptance evidence

| Criterion | Software status | Evidence / limit |
| --- | --- | --- |
| AC-1 — Canonical validation | Passed | Complete real-export accounting and exact WI-03 mask agreement; reversed source IDs, non-square geometry, malformed polygons/categories/references and bounded archives exercised. |
| AC-2 — Traceability/reproducibility | Passed | Source metadata/license/attribution and unknowns retained; real reports identical, synthetic dataset/split IDs identical; label/review/role changes alter relevant IDs; source unchanged. |
| AC-3 — Reviewed split isolation | Passed | Explicit assignments/original roles preserved; exact byte/decoded duplicates and known groups crossing roles block readiness; all known-source candidates cannot be omitted; real assignments remain deferred. |
| AC-4 — Human eligibility | Passed | Prediction/unknown/missing origins rejected for active inclusion; stale/missing reviews blocked; default conflict rejection, deterministic reviewed ignore, verified negatives and all-ignore rejection exercised. Genuine lab review remains pending. |
| AC-5 — Complete offline handoff | Passed for software; real ready handoff unverified | CLI and consumer ready/blocked/invalid paths, schema/inventory/fingerprints/geometry/tamper checks, write/interruption/rename failures and no-overwrite competition pass. Fresh installed wheels consume the handoff. A real ready artifact needs a genuine lab review. |

Software verification is not stakeholder acceptance or certification of label truth.
The conditional real-ready evidence remains unverified, as allowed by the approved
proposal when genuine review is unavailable. WI-06 real training and G-05 release
remain blocked by the separate real-data human gate; no training ran.

## Checks performed

- Editable package plus unchanged WI-03 audit regression suite: **84 passed**
  (64 dataset checks and 20 audit checks), Linux/Python 3.12.13.
- Built model/dataset source distributions and wheels. A fresh wheel-only environment
  passed all **64 dataset checks** and the installed CLI consumed the existing
  synthetic handoff with matching identities. No ONNX, cloud/backend or frontend
  runtime dependency was installed for this path.
- `scripts/check-dataset-handoff.py`: two complete real blocked runs, all 40 masks
  reconciled, two synthetic ready runs and all active roles consumed.
- Strict OpenSpec, whitespace and documentation-link checks are recorded at handoff.
  App runtime/UI and the WI-03 audit implementation are unchanged; app build/tests
  were not needed for this isolated package.

Actual versions: NumPy 2.5.3, Pillow 12.3.0, pycocotools 2.0.11, Pydantic 2.14.0.
`requirements-wi05.txt` pins the verification environment separately from the app
and WI-03. pycocotools differs from WI-03's 2.0.10; all 40 real decoded masks still
agree exactly. Its existing NumPy `__array__` deprecation warning is non-blocking;
a duplicate-ZIP warning comes from the intentionally malformed test fixture.
Python 3.10/3.11/3.13 and Windows publication are unverified.

## Reproduction and private evidence

Follow [dataset preparation and consumption](../13_VALIDATED_DATASETS.md).

```bash
.workspace/wi05/venv/bin/python -m pytest \
  packages/graphene-dataset-contract/tests scripts/tests/test_lab_dataset_audit.py -q
.workspace/wi05/venv/bin/python scripts/check-dataset-handoff.py \
  --source '.workspace/wi03/source/2D Materials segmentation.v2i.coco-segmentation.zip' \
  --audit .workspace/wi03/audit-02 --output .workspace/wi05/verification-new
.workspace/wi05/wheel-venv/bin/graphene-dataset check .workspace/wi05/verification-01/synthetic-1
```

Private outputs: `.workspace/wi05/verification-01/`, including `summary.json`,
`real-1/`, `real-2/` and `synthetic-1/`, `synthetic-2/`. Ready synthetic artifacts
and source/review fixtures are local; raw data, paths and reviewer records are
excluded from Git. The checked summary contains:

- Real report fingerprint: `0c7b71f58c9b339bdd354c56afce2768a1f3e6e0370f60d181e0c821b276d710`.
- Synthetic dataset fingerprint: `27f19ab8d33d098c3ba946880121ef5daa6dabba232afbb1b67c2695523f86cf`.
- Synthetic split fingerprint: `c93c87856267941592823579392088e20da22e943756b17f167b78a2a4fdda7f`.

## Remaining human decisions

Supply a real source-bound lab review confirming physical categories, annotation
origin/completeness, conflicting-label correction or justified ignore, acquisition/
candidate grouping, and explicit split assignments or exclusions. Unknown physical
facts cannot be resolved by successful PNG conversion. Then run real preparation/
consumer checks and record genuine readiness before WI-06 real training.
No new proposal, protected branch update, model training or cloud action is included.
