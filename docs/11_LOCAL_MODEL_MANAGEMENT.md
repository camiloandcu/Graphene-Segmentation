# Local model management

Consumer: lab members importing a model and operators recovering their workspace.
WI-04 implements import, inspection and explicit selection. Production inference
belongs to WI-09; selected does not mean an inference session has loaded.

## Supported packages and setup

Install the optional CPU validation dependencies in the local backend:

```bash
cd backend
uv sync --locked --extra models --python 3.12
```

Restart the server, then refresh Models. The storage-only installation also works;
it can display saved metadata but cannot import or select without these extras.
Supported packages follow the [v1 contract](10_PORTABLE_MODEL_CONTRACT.md): exactly
`model.onnx`, `manifest.json`, `evaluation.json` with explicit three-class semantics.
Do not upload a bare graph, framework checkpoint, pickle or training folder.

## User workflow

1. Open Models and choose a ZIP no larger than 256 MiB.
2. Import it. CPU compatibility is checked before the model is saved locally.
3. Inspect identity, classes, operating setting, geometry and evaluation details.
4. Select it explicitly. The stored bytes and current CPU compatibility are
   checked again before selection is committed.
5. Restarting the backend/browser retains the exact model ID and package identity.

Import never auto-selects. An identical ZIP with the same model ID returns the
existing record. A different ZIP reusing that ID is rejected, even if only the
evaluation or ZIP packaging changed; exporters must give changed packages a new ID.
There is no deletion/replacement flow in this slice. Identical weights can belong
to different package identities if settings/provenance differ.

Unmeasured results remain unmeasured. Reported evaluation includes the exporter's
definitions/support and remains supplied evidence rather than independently
verified accuracy. Synthetic packages verify the workflow, never lab usefulness.

## API and resource boundaries

| Route | Contract |
| --- | --- |
| `GET /api/models` | Summaries, exact selected ID, file availability and runtime capability. |
| `GET /api/models/{model_id}` | Full validated metadata/evaluation and digests; no internal paths. |
| `POST /api/models/import` | Raw ZIP body, `Content-Type: application/zip`; 201 new or 200 exact repeat. |
| `PUT /api/models/selection` | JSON `{"model_id":"<registered UUID>"}`; commit after validation. |

The single-server validation slot covers receiving, checking and committing a
mutation. Concurrent imports/selections return retryable `409 busy` rather than
queueing unbounded work. Health/list remain responsive during native validation.
Uploads are streamed to generated staging files, with actual-byte bounds and a
60-second receive deadline. Native validation retains WI-02's 30-second wall,
20-second CPU and 4 GiB address-space limits. The ZIP limit is 256 MiB, expanded
total 258 MiB and each JSON 1 MiB. Clients cannot increase these limits.

Validation runs away from the async event loop. Cancellation retains the slot
until its thread/native worker finishes cleanup; cancellation observed before
commit prevents import/selection publication. A lost response after commit is
reconciled by refreshing Models and retrying an identical import if necessary.

Errors use safe `code`/`message` responses: 413 size, 422 incompatible package,
404 unknown model, 409 conflict/unavailable/busy, 503 runtime/storage, 408 upload
deadline, 400 disconnected upload and 415 unsupported body format. Selection
uses one atomic SQLite update and never changes the choice on validation failure.

## Recovery and durability

The original ZIP is stored as generated opaque artifact bytes. File publication
and its fsync happen before a single SQLite transaction commits both artifact and
model rows. Failure before commit leaves no listed model; generated orphan/staging
files are removed at exclusive startup recovery. No extracted graph folder is
persisted. Only generated unreferenced files are eligible for orphan cleanup.

Schema v1-to-v2 migration is transactional and preserves unrelated artifacts.
Startup checks stored integrity without importing ONNX or performing inference.
List/detail refresh file integrity while the app stays open; a missing/corrupt file
is marked unavailable. Its selected identity is retained without automatic fallback.

| Condition | Recovery |
| --- | --- |
| No runtime extras | Install the optional dependencies above, restart, refresh. |
| Invalid ZIP | Ask its exporter to correct the stated contract problem; prior selection remains. |
| ID conflict | Export the changed package with a new model ID. |
| Busy/timeout | Wait for validation to finish, check connection, refresh and retry. |
| Lost response | Refresh authoritative state; identical import retries cannot create duplicates. |
| Missing/corrupt selected file | Select another intact model, or restore a complete stopped-workspace backup. |
| Storage failure | Check local disk permissions/capacity; retry after correcting it. |

Restoring means copying a complete consistent workspace, not replacing individual
bytes or modifying SQLite. See [backup/recovery](09_LOCAL_WORKSPACE.md).

## Verification

Run the backend/shared-contract tests and frontend build from README. The browser
check uses an isolated temporary workspace and compatible synthetic fixtures:

```bash
backend/.venv/bin/python scripts/make-model-ui-fixtures.py /tmp/graphene-wi04-fixtures
uv run --no-project --python 3.12 --with playwright python scripts/check-model-ui.py --fixtures /tmp/graphene-wi04-fixtures
```

The fixture directory contains `unmeasured.zip` named `Synthetic identity fixture`,
a distinct compatible `reported.zip` with reported metrics, and `invalid.zip`.
This check starts/stops its own loopback backend on port 8014, with `--port` and
`--output` overrides. Install Playwright Chromium first if absent. For exact
acceptance evidence see [WI-04 verification](review/12_WI_04_VERIFICATION.md).
