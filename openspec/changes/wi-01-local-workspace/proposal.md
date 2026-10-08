## Why

The lab needs a workspace that starts without cloud accounts and keeps its data
after restart. Today startup mounts cloud/auth routes and imports ML frameworks,
health depends on the legacy model service, and the interface requires login.

## Work Item and Review State

- **WI-01 / Enabler**, parent **INC-01 / F-03**.
- Consumers: lab operator and downstream model-management/inference services.
- Outcome: documented local startup with persistent SQLite metadata and files.
- The stakeholder explicitly approved implementation before coding.
  Approval covers the local foundation, not all future ML decisions.
  GitHub Issue #1 and linked branch feat/wi-01-local-workspace track this change;
  publishing this branch and its linked PR is authorized.
- Source: [WI-01 acceptance criteria](../../../docs/review/06_DECISIONS_AND_WORK_ITEMS.md).

## What Changes

- **BREAKING**: make the default app a local workspace without login or
  Supabase/JWT configuration. Exclude cloud/account/admin/training routes from
  its startup graph and stop offering their screens as working local features.
- Introduce versioned SQLite metadata and local artifact storage with relative
  paths, durable publication, rollback, and startup recovery.
- Separate health from model/training frameworks. An empty workspace is healthy
  and explicitly reports that no model is ready.
- Provide a loopback launcher serving the built frontend and API, opening
  directly to a minimal English workspace readiness view.
- Align local runtime dependencies and document installation, restart, and
  backup/restore. Diagnose unfinished frontend checks and apply only setup/build
  corrections necessary for this outcome.

## Capabilities

### New Capabilities

- `local-workspace`: account-free startup, health, persistent metadata/artifacts,
  recovery, loopback serving, and a minimal local entry screen.

### Modified Capabilities

None. No existing OpenSpec capability specifications exist in the repository.

## Scope and Non-Goals

Scope: WI-01-AC-1 through AC-3, Linux setup, local storage, isolated startup,
loopback defaults, and secret-free logging. Excluded: live Supabase migration or
deletion, network sharing, model-package import/selection, prediction, GPU
benchmarking, dataset ingestion, Colab training, and the full prediction UX.
Persistence fixtures are opaque bytes, not compatible imported models.

## Impact

Affected areas: backend entry/configuration/health, new workspace storage
services, frontend entry/API configuration and serving, runtime dependencies,
launcher, setup documentation, and integration checks. Existing cloud/ML modules
remain outside the supported local startup path. Future items consume the new
storage boundary. No external account access, remote data changes, deployment,
or main-branch operations are included.
