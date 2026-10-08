## Context

WI-01 establishes the runtime consumed by model management and later dataset/
results work. The lab selected Linux, local persistence, no accounts, and English.
This change does not select a model architecture or prove inference. See the
[architecture proposal](../../../docs/review/04_ARCHITECTURE.md).

`backend/app/main.py` imports all routes and tries cloud-backed model loading.
Health imports the legacy model service. Configuration prints secrets. React
requires a role/token. Backend dependency definitions disagree and combine cloud,
training, and inference. Previous frontend build/type checks were interrupted
without a result, rather than verified compiler failures.

## Goals / Non-Goals

**Goals:** AC-1 clean local startup, AC-2 durable/recoverable writes, AC-3 loopback
defaults without secret logging or cloud initialization.

**Non-Goals:** remote migration, supporting legacy cloud routes locally, public
generic artifact upload, model interpretation/execution, prediction UX, datasets,
training, GPU tuning, or multi-user/network access.

## Decisions

### Isolated local startup and dependencies

The default backend entry/app factory constructs only local health, workspace
lifecycle, and frontend serving. FastAPI lifespan opens storage and completes
recovery before readiness. Local configuration does not import Supabase/auth/
model/training modules, require their variables, or load remote `.env` credentials.
Remove the secret print in existing configuration as well.

Use explicit local dependencies (FastAPI/Uvicorn and only necessary configuration
support), with standard-library SQLite/files. Cloud/training packages are outside
the required installation. Reconcile supported install commands and requirements/
lock definitions. Support Python 3.12 and document a Node version verified against
the installed frontend dependencies, recording tested versions.

Keeping all routes and making credentials optional was considered: transitive
imports would retain cloud/ML coupling and expose unsupported workflows.

### One local server and an honest entry view

`./scripts/start-local.sh` starts one Uvicorn worker on `127.0.0.1:8000` serving
`frontend/dist` and the API. Installation builds assets first; absent assets
produce an actionable launcher error. Vite development also defaults to loopback
and an explicit API origin. Built browser requests use the same origin; development
CORS permits documented loopback origins without credentials.

`GET /health` reports runtime/storage readiness and no loaded model without
instantiating inference. Storage initialization failure prevents healthy startup.
Browser responses do not expose secrets or absolute internal paths.

The frontend opens without login and shows connection/storage state and no ready
model in English. It does not mount pages that call cloud APIs or present working
upload/predict controls. WI-04/WI-10 add those workflows. Review this minimal entry
view with Impeccable during implementation, including keyboard and failure states.

A single built server was chosen over mandatory separate development servers to
simplify the operator command and avoid CORS in the normal lab workflow.

### Workspace persistence boundary

Default directory: `${XDG_DATA_HOME:-$HOME/.local/share}/graphene-segmentation`;
`GRAPHENE_WORKSPACE_DIR` explicitly overrides it. Store `workspace.sqlite3`,
`artifacts/`, and staging files beneath the root. Persist relative paths and
generated identities; original filenames are display metadata. The local OS user
owns the workspace. Do not import/overwrite existing backend models/MLflow data.

Use versioned SQLite schema (`PRAGMA user_version`), foreign keys, explicit
transactions and durable commit settings. Artifact metadata includes identity,
relative path, size, checksum, timestamp, and opaque consumer metadata. Later
items define model/dataset semantics. Reject unsupported newer schema versions
without resetting data. Expose publish/verified lookup as an internal service,
not an unvalidated public upload route. Usable lookups require intact files;
caller names cannot escape the workspace.

Extending the current registry directly was considered: its framework guessing,
user scoping and activation would pull separate model-management work into WI-01.

### File/database recovery and ownership

SQLite and files cannot commit together. Write under a fresh generated identity
to staging, flush/fsync, atomically move to the final path on the same filesystem,
fsync the directory, then commit metadata. Success follows both publication and
commit. Failed commit rolls back metadata and cleans unreferenced files.

Acquire an OS workspace lock before recovery and retain it for the server lifetime.
Reject a second writer. Startup removes only unreferenced files in the store's
generated staging/artifact namespace. Preserve unrelated and legacy files.
Missing/corrupt committed artifacts become unavailable to consumers; never create
empty replacements. Diagnostics report recovery without secrets/file contents.
Multiple workers and shared/network filesystems are outside the supported setup.

### Evidence and operational handoff

Verify an isolated install without cloud/training packages or Supabase/JWT
variables. After dependencies/assets are installed, run the launcher with outbound
access unavailable; observe health, listener, UI and absence of external imports/
calls. Existing cloud credentials must also not affect local startup.

Use opaque fixture bytes to verify restart and relocation. Inject staging,
publication, transaction and interruption failures; verify corruption, path
confinement, schema rejection and second-writer behavior. Include an actual process
restart alongside fault-injection checks. Run affected backend tests and frontend
build/type checks. If baseline diagnosis exposes unrelated broad work, surface a
scope decision rather than expand this item silently.

Update the product-facing README and deeper `/docs/` operations guide. Document
install/start/stop, offline use, current limits, storage location and backup/restore:
stop the server and copy the entire workspace, then restore with relative references.

## Risks / Trade-offs

- Filesystem/database interruption -> ordered durable publication, exclusive
  recovery, generated namespace, and boundary tests.
- Local access has no multi-user policy -> loopback defaults; sharing needs a
  later approved design.
- Legacy workflows disappear from local navigation -> clearly state the current
  foundation's limits; preserve remote data and add features in subsequent items.
- Build baseline unknown -> diagnose first and record tested versions/results.
- Disk permissions/capacity -> fail explicitly; do not return a successful broken record.

## Migration Plan

After approval, create a short-lived local branch. Initialize a fresh workspace
without remote access, implement/verify, and make Conventional Commits. Push the linked work branch and open its PR with
`Closes #1`, as subsequently authorized by the stakeholder.
Rollback restores prior code through the branch while preserving all local,
legacy and remote data. After verified completion sync specs and archive WI-01.
Main merge/push and another proposal require separate approval.

## Open Questions

The stakeholder approved this local architecture/scope before implementation. No additional kickoff
decision is needed for the foundation. Real hardware performance, model-package
semantics and dataset readiness remain in their subsequent items.
