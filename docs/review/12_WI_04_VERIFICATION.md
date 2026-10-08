# WI-04 model management verification

Checked: 2026-10-08. Proposal/design/specs explicitly approved by stakeholder.
Status: implemented, technically verified and stakeholder accepted on 2026-10-08.
PR #18 is merged (checked via `gh`); release readiness remains separate.
Issue: [#4](https://github.com/camiloandcu/Graphene-Segmentation/issues/4).
Branch: `feat/wi-04-local-model-management`, linked with `gh issue develop 4`.
Approved-design commit: `50ca4cb`. Implementation commit: `2758654`.
PR: [#18](https://github.com/camiloandcu/Graphene-Segmentation/pull/18), merged with `Closes #4`; GitHub confirms the closing Issue association.

## Acceptance evidence

| Criterion | Technical result | Evidence |
| --- | --- | --- |
| AC-1 — Import and inspect | Passed | Real synthetic three-class ONNX ZIPs pass native CPU validation through UI/API; exact bundle/model digests, manifest, evaluation and model UUID persisted. Import leaves selection unchanged. Reported/unmeasured details render safely. |
| AC-2 — Explicit persistent selection | Passed | Two distinguishable models switch explicitly; API lifespan reopen and actual backend/browser restart retain exact ID/package identity. Health continues to report no production inference session. |
| AC-3 — Failures preserve state | Passed | Malformed ZIP, binary graph, actual-byte/declared-size bounds, ID conflict, unknown selection, real native-worker timeout, disk/commit failure, changed bytes during selection, repeated imports and competing requests preserve committed state. Health/list work while validation waits. Disconnect/deadline cleanup and cancellation ownership/precommit checks pass. Lost-response retry uses idempotent import and committed crash recovery. |
| AC-4 — Upgrade/recovery/base installation | Passed | Populated schema-v1 fixture preserves opaque bytes/metadata; failed migration rolls back. Real subprocess exits at staging/publication/commit boundaries recover correctly. Missing/corrupt selected packages retain identity; browser/API can select an intact alternative. Base installation and fresh optional-import-blocked interpreter remain usable with installation guidance. |
| AC-5 — Accessible understandable workflow | Passed | Chromium desktop 1440×1000 and narrow 390×844: keyboard file import/select, focus feedback and skip link, long names, safe supplied HTML text, reported/unmeasured details, no horizontal overflow, stale connection/retry, other-tab reconciliation, missing runtime and unavailable selection. No page errors or unexpected dialogs. |

These results establish model management with synthetic packages. Stakeholder
acceptance is confirmed. Real trained-model usefulness, prediction and INC-01
release gates remain unverified; compatible/selectable does not certify accuracy.

## Executed checks

- Backend and shared contract: **113 passed**, Python 3.12; command below. The
  earlier 108/112-test runs exposed no regressions; additional boundary tests were
  added for binary output, selection commit/integrity and cancellation ownership.
- Isolated storage-only installation: **24 passed** without ONNX/model extras,
  using pinned FastAPI/httpx/pytest in a separate `uv run --isolated` environment.
  The final suite also includes a fresh interpreter blocking every optional model
  module while checking health/list/import/select behavior.
- Frontend: `npm run build` passed, including TypeScript. Existing Browserslist
  dataset-age notice is non-blocking; no dependency versions were changed.
- Impeccable mechanical detector: no deterministic findings on changed App/Models/CSS.
- Playwright workflow: all nine scenarios passed twice; second pass confirms the
  focus-link adjustment. Screenshot inspection confirms readable desktop/narrow
  layout and class/evaluation/selection labels.
- OpenSpec strict change validation passed; archive synced five model-management
  and three workspace requirements. `openspec validate --all --strict --no-interactive`
  passed all four specifications; `git diff --check` passed.

```bash
cd backend
.venv/bin/python -m pytest tests_local ../packages/graphene-model-contract/tests -q
cd ../frontend
npm run build
cd ..
backend/.venv/bin/python scripts/make-model-ui-fixtures.py /tmp/graphene-wi04-fixtures
uv run --no-project --python 3.12 --with playwright python scripts/check-model-ui.py --fixtures /tmp/graphene-wi04-fixtures
```

Browser check uses a disposable workspace, starts/stops its own loopback server,
and emits screenshots/JSON. Fixtures contain illustrative metrics explicitly
labeled as synthetic, never lab measurements. Evidence committed:

- [Desktop](evidence/wi04-desktop.png) and [narrow layout](evidence/wi04-mobile.png).
- [Invalid-package recovery](evidence/wi04-invalid-package.png).
- [Unavailable selected file](evidence/wi04-unavailable-selection.png).
- [Browser results](evidence/wi04-browser-results.json).

## Delivered boundaries and recovery

SQLite schema v2 migrates v1 in one transaction; old artifacts remain intact.
The model ZIP is the authoritative generated artifact. Artifact/model metadata
commit together after file publication/fsync; startup cleans generated orphans.
Selection is explicit and immutable model records reject conflicting package IDs.
Missing/corrupt selected files keep their identity without fallback. Restoring
requires a complete stopped-workspace backup, not manual byte/DB modification.

One nonblocking validation slot covers receiving/checking/committing; actual ZIP
bytes and receive time are bounded. Cancellation observed before commit prevents
publication, retains worker ownership and reaps native work before releasing the
slot. Lost responses after commit require authoritative refetch. Runtime extras
remain optional; no cloud/accounts/training module or production session is loaded.

No tracked dependency locks changed. `uv sync --locked --extra models` rebuilt the
existing editable contract package. Browser tools used an ephemeral cached uv
environment; isolated base checks installed their own test dependencies.

## Submission and remaining gates

No protected branch was pushed, merged or updated. The work branch is pushed and
PR #18 uses `Closes #4`. Approved design and implementation commits are pushed;
a final documentation commit records these submission references. Verified
specifications are synced and the change archived under
`openspec/changes/archive/2026-10-08-wi-04-local-model-management/`.
Lab/stakeholder acceptance, Issue closure, merge and release remain pending.
No next proposal has been prepared.
