## 1. Confirm approval and package boundaries

- [x] 1.1 After explicit proposal approval create the Issue #2 linked branch; finalize the documented v1 schema/profile and resource policy (AC-1/AC-2; G-01/G-02).
- [x] 1.2 Add the installable shared library, strict JSON Schema/parser and independent schema examples; preserve optional model dependencies and default WI-01 startup (AC-1).

## 2. Implement shared tensor and geometry semantics

- [x] 2.1 Implement RGB/layout/normalization checks, immutable geometry records and exact versioned letterbox/inverse-logit transforms (AC-1/AC-4).
- [x] 2.2 Implement bounded native tile planning/overlap-logit reconstruction and declared class/threshold/tie decisions (AC-1/AC-3/AC-4).
- [x] 2.3 Verify independent golden RGB/channel/coordinate values, portrait/landscape and odd padding, tile edges/seams, ties and invalid arrays (AC-4).

## 3. Implement bounded package compatibility

- [x] 3.1 Implement stream-bounded ZIP/JSON/checksum/provenance checks, strict canonical classes and specific rejection errors (AC-1/AC-2/AC-3).
- [x] 3.2 Implement disposable resource-limited CPU graph checking/smoke execution and graph-interface validation with deterministic fixtures (AC-2/AC-3).
- [x] 3.3 Verify binary-output rejection, mismatched interfaces, unsafe/oversized archives, external tensors, malformed/inconsistent reports, non-finite output and worker timeout/failure cleanup (AC-2/AC-3).

## 4. Prove producer/consumer readiness and hand off

- [x] 4.1 Build synthetic packages through the producer helper and validate/reconstruct through a distinct consumer entry; compare to independent expected tensors/logits/masks and record runtime versions (AC-1–AC-4).
- [x] 4.2 Verify the core library's standalone install/import and WI-01 startup/tests without optional model runtime; run relevant shared/backend checks (AC-1/AC-4; G-04).
- [x] 4.3 Document export/import contract, unknown/unmeasured evidence, compatibility failures, geometry limitations and pass/fail/unverified acceptance evidence (AC-1–AC-4; G-03/G-04).
- [x] 4.4 Commit/push the approved Issue-linked branch, open a PR with `Closes #2`, and after technical verification sync specs/archive. Keep real Colab/model/lab validation unverified and stakeholder/merge/release status distinct (G-03/G-04).
