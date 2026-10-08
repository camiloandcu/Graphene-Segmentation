## Context and Goal

The local app currently mounts only `/health` and static files. `Workspace` owns
a schema-v1 SQLite database, generated artifact filenames, a process lock,
file-before-metadata publication, integrity checking and startup orphan recovery.
`graphene_model_contract` validates the exact three-member v1 ZIP, returns manifest,
evaluation, model bytes, bundle digest and smoke evidence, and bounds native work
in a disposable CPU subprocess. Model extras are optional.

Extend these boundaries rather than connecting legacy cloud registry/training code.
One cohesive outcome: a lab member can import and explicitly choose an intact,
compatible model, with identity preserved across restart. All decisions below are
proposed for stakeholder approval, not implemented behavior.

## Registry and Schema Upgrade

Upgrade schema v1 to v2 transactionally under the existing exclusive workspace
lock. Fresh workspaces receive v2. Preserve every existing artifact and its metadata;
reject unsupported future schemas with the existing compatible-version message.
An interrupted migration leaves the prior complete schema or complete v2.

Add `models` keyed by canonical manifest UUID, referencing one opaque ZIP artifact,
with bundle/model SHA-256, name/version, validated manifest/evaluation, import time
and validation evidence/version. Add a singleton workspace selection referencing
`models.model_id`, nullable initially. Enforce unique identity/artifact references
and foreign keys. Model settings and identity are immutable once committed.

Keep the original ZIP as the authoritative artifact; do not persist an extracted
graph directory or trust a supplied filename/path. Selection/list responses expose
public metadata and availability, never internal file paths. Imported evaluation
is supplied evidence, not independent lab verification.

Publication extends the existing file-before-metadata protocol: stream to a
generated private staging file, validate, flush/fsync and rename to a generated
artifact filename, then insert artifact and model metadata in one SQLite transaction.
Do not call `Workspace.publish` unchanged and perform a separate registry commit:
that would leave durable unregistered artifacts at the crash boundary. Failure
before commit leaves no listed model; startup removes generated unreferenced files.
Failure after commit may lose the HTTP response, so repeating the same ZIP resolves
to the existing record. No model deletion or replacement is introduced.

Exact same model ID and bundle digest is an idempotent import. Same ID with any
different bundle digest, including changed evaluation/packaging, returns a conflict.
New versions with different bytes must use a new model ID. Duplicate graph weights
under different model IDs are permitted: graph digest alone is not package identity.

## Bounded Import and Concurrency

Use the WI-02 `ValidationLimits` defaults, including a 256 MiB packed archive,
258 MiB expanded total, 1 MiB per JSON and 30-second native-worker wall timeout.
Server limits are authoritative; do not permit clients to raise them. Stream raw
ZIP bytes with `application/zip` rather than buffering an unrestricted multipart
body. Check declared size when available and count actual streamed bytes, including
chunked input; stop at the packed bound. Client filename is display-only.

Allow one validation mutation at a time in this single-server workspace. Acquire
a nonblocking service slot before reading the body; excess work returns a retryable
busy response rather than an unbounded queue. Configure a bounded upload deadline
and release staging/slot on disconnect, timeout and failure. Run ZIP validation
away from the async event loop; retain WI-02 native subprocess resource limits.
Health/list operations remain available while validation runs. Cleanup waits for
worker completion/reaping; abandoned requests cannot leak background workers.

Do expensive checks outside the short SQLite transaction. Under the workspace
mutation lock, recheck identity/conflicts and file integrity before committing.
Selection also uses the validation slot, so import/selection cannot race to bypass
resource bounds. Completed selection responses describe the committed model;
responses may be lost after commit, so clients refetch authoritative state on retry.

## API and Selection Semantics

Register new local routes before the catch-all SPA mount:

| Route | Behavior |
| --- | --- |
| `GET /api/models` | Registered summaries, availability, validation capability and selected model ID; deterministic order. |
| `GET /api/models/{model_id}` | Exact identity, compatible-package metadata, evaluation/provenance and availability. |
| `POST /api/models/import` | Bounded raw ZIP; 201 for creation, 200 for exact repeated import. Never auto-select. |
| `PUT /api/models/selection` | JSON model ID; integrity plus current CPU validation, then atomic selection commit. |

Selection GET is included in the list response; no clearing endpoint is needed
for this slice. Revalidating selection through the same validator proves current
runtime compatibility without retaining a serving inference session. Selecting the
already selected intact model is safe and returns authoritative state.

Use stable `{code, message}` errors with readable, safe recovery copy: 413 oversized,
422 invalid/incompatible package, 404 unknown model, 409 identity conflict/unavailable
artifact/busy, 503 missing model runtime, and sanitized storage/timeout failures.
Do not return native traces, manifest contents as errors, or internal paths.

Startup verifies referenced artifacts through workspace recovery without ONNX
execution. Missing/corrupt artifacts become unavailable; the selected ID remains
visible, with no automatic fallback. Selection always verifies current bytes and
compatibility, including after an environment change. Without extras, users can
view persisted registry metadata but import/select are unavailable. Cached import
validation is labeled historical evidence; it is not a promise of current runtime
execution or lab performance. No startup dependency on ONNX or cloud modules.

Keep `model_loaded: false` in health until WI-09 implements inference loading;
report actual schema version and separate selection/capability information where
needed. Update the frontend's readiness check so healthy local storage does not
depend on whether a future inference model is loaded. Extend dev CORS to the
required GET/POST/PUT methods and headers while retaining exact loopback origins.

## Models UX Within the Existing Workspace

Consumer: lab members and occasional trainers; surface mode: Operate. Preserve
the current dark shell, system typography, restrained blue accent, visible focus
and responsive navigation from `frontend/src/App.tsx` and `frontend/src/index.css`.
No redesign, new product-context files or unrelated legacy-page activation.

Add Models navigation and a selected-model summary in Workspace. Models starts
with an inline, labeled native file picker, supported ZIP guidance and **Import
model** action. No architecture/encoder/threshold fields. On import success show
the imported entry and offer **Select model**; preserve the user's prior selection.

List names and versions with text labels for selected/available/unavailable and
evaluation status. Use explicit selection buttons. Inline expandable details show
class names, operating setting, geometry, CPU validation, identity and reported
evaluation/provenance. Few-layer metrics appear only with supplied definitions
and support; missing or unmeasured results stay labeled. Do not invent a ranking,
quality badge or guaranteed recall. Long names wrap; metadata is rendered as text.

| State | Observable feedback and next action |
| --- | --- |
| Empty | Explain compatible model ZIPs; offer import. No selected model. |
| Listing/loading | Preserve structure and announce loading; avoid an empty-state flash. |
| Importing/selecting | Announce the pending action; disable duplicate mutations. |
| Imported | Confirm saved locally, selection unchanged; offer explicit Select model. |
| Selected | Identify exact name/version; explain prediction arrives with later work. |
| Unmeasured/reported | Distinct text labels; supplied results are not independently verified. |
| Invalid/conflict/busy | Specific reason, preserved selection and corrected-file/retry action. |
| Offline or lost response | Preserve last confirmed data as stale; retry/refetch before claiming success. |
| Unavailable selection | Retain its name/ID; offer another intact model or compatible-app recovery. |
| Missing extras | Keep workspace usable; give the documented local installation action. |

Keyboard users can import, inspect and select with visible focus. Use semantic
buttons/headings, linked errors and polite status announcements; errors must not
depend on color. Preserve focus after updates; no mandatory modal. On narrow
screens stack controls and list details without horizontal page overflow. Pending
work in one tab is enforced again server-side; refetch on tab focus and after
mutations so other-tab changes reconcile without silently claiming stale selection.

## Verification and Handoff

AC-1/2: two distinguishable synthetic fixture ZIPs through API/UI; exact digests,
explicit selection, backend/browser restart and registry/detail consistency.
AC-3: malformed/unsupported/binary/oversized packages, digest conflict, repeated
upload, resource timeout, missing runtime, unknown selection, concurrent requests,
health during validation and lost-response retry. Reuse WI-02 contract fixtures;
test service integration rather than duplicating the validator's unit suite.
AC-4: populated v1 upgrade, migration/publication interruption boundaries, orphan
cleanup, corrupt/missing selected artifact, alternate selection and no-extras startup.
AC-5: reported/unmeasured/long-name fixtures, keyboard/focus, state recovery and
desktop/narrow screenshots. Backend focused regression checks and frontend
typecheck/build are required. Synthetic evidence proves management, not model quality.

Create `docs/review/12_WI_04_VERIFICATION.md` during implementation and record
AC evidence, branch/commits/PR and remaining human acceptance. Update user-facing
setup/import docs and technical migration/recovery docs. Sync specs and archive
only after verification; push the work branch and open the linked PR. Protected
branches, broader release and later proposals retain their approval boundaries.
