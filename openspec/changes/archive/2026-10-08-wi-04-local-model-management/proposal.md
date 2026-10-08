## Why

Lab users need to import a portable model and choose it for later screening
without editing ML configuration. WI-01 supplies durable local storage and WI-02
supplies compatibility validation, but the running app exposes neither import
nor selection. Legacy cloud/model routes are excluded from the local runtime.

## Work Item and Review State

- **WI-04 / US**, parent **INC-01 / F-03**; [Issue #4](https://github.com/camiloandcu/Graphene-Segmentation/issues/4).
- Consumer: a lab member or occasional trainer with a v1 model ZIP.
- Outcome: import, inspect and explicitly select a compatible local model;
  retain the exact selection across app restart.
- Dependencies: WI-01 and WI-02, both merged and present locally. A real trained
  model is not required to prove this workflow; quality and prediction remain
  separate later acceptance gates.
- Status: prepared for stakeholder review on 2026-10-08; **explicitly approved by the stakeholder on 2026-10-08**.
- Source: `docs/review/06_DECISIONS_AND_WORK_ITEMS.md`, requirements/UX and WI-02 contract.

## What Changes

- Add a local SQLite model registry and one durable selected-model reference,
  with a reviewed schema-v1 migration preserving existing opaque artifacts.
- Accept bounded ZIP uploads and invoke the existing WI-02 validator before
  publishing any registered model. Keep native validation in its resource-limited worker.
- Expose local list/detail/import/selection APIs without accounts or cloud calls.
- Extend the existing workspace shell with Models import, readable details,
  explicit selection and actionable empty/loading/failure/recovery states.
- Separate technical compatibility, supplied evaluation evidence and selection
  from prediction readiness. No model session is loaded for production inference.

## Capabilities

### New Capabilities

- `local-model-management`: bounded model import, immutable registered identity,
  persistent explicit selection and usable local Models interaction.

### Modified Capabilities

- `local-workspace`: transactional schema-v1 upgrade, model metadata/selection
  recovery, and startup/health availability with or without optional model extras.

## Scope and Non-Goals

Scope: WI-04-AC-1 through AC-5 below, local storage/API/UI and verification.
Proposed policies: importing never auto-selects; exact repeated packages return
the existing model; reuse of a model ID with different package bytes is rejected;
unavailable selected artifacts retain their identity until the user selects a
different compatible model. No implicit replacement or fallback.

Excluded: prediction endpoints/sessions (WI-09), image/batch upload and result
inspection (WI-10/11), model deletion/editing, dataset import, training/export,
cloud registries, arbitrary model formats, CUDA support and accuracy certification.
No new calibration or threshold editing; settings come from the approved package.

## Acceptance Criteria and Evidence

**WI-04-AC-1 — Import and inspect.** Given a v1 compatible ZIP and model-validation
extras, when a user imports it through Models, then one durable registry entry
contains its exact model ID, version, package/model digests and validated metadata;
the UI shows its name, compatibility and evaluation evidence without ML form fields.
Import does not change the current selection, including on first import.
Evidence: synthetic package through UI/API, SQLite/artifact assertions and details review.

**WI-04-AC-2 — Explicit persistent selection.** Given registered compatible models,
when a user selects one and restarts the backend and browser, then the same model
ID and immutable package identity remain selected. Selection is acknowledged only
after checking artifact integrity and current CPU compatibility and committing it.
Evidence: two distinguishable fixture packages, API/UI switching and fresh-process restart.

**WI-04-AC-3 — Failures preserve usable state.** Given an existing selected model,
when an import or selection is malformed, incompatible, oversized, resource-limited,
missing-runtime, unknown-ID or interrupted before commit, then the prior committed
selection and existing models remain unchanged and the user receives a specific
reason and recovery action. An exact repeated import is idempotent; a conflicting
model ID is rejected without replacing files/metadata. Competing mutations cannot
publish duplicates or expose partial selection; validation cannot block health.
Evidence: API integration cases, concurrent requests, injected storage/commit
failures, disconnect/retry, worker timeout and health responsiveness checks.

**WI-04-AC-4 — Upgrade and recovery.** Given a schema-v1 workspace with unrelated
artifacts, when the app upgrades or restarts after an interrupted publication,
then existing artifacts are preserved, only committed model records are listed,
and orphan/staging files are recovered. Given a missing or corrupt selected package,
then its selection identity remains recorded and visibly unavailable; an intact
alternative can be explicitly selected. Basic startup/health work without model
extras, with import/selection providing an installation action rather than a crash.
Evidence: populated-v1 migration fixture, failure/restart injection, corruption
fixtures, alternate selection, and base-install subprocess/startup checks.

**WI-04-AC-5 — Understandable accessible workflow.** Given first-run, loading,
importing, compatible/unmeasured, selected, connection-error or unavailable states,
when a user operates Models with keyboard or a narrow viewport, then each state
offers a readable next action, focus remains usable, pending actions cannot be
accidentally repeated, and names/evaluation text render safely. The UI distinguishes
reported results from independently verified lab quality and states that prediction
is pending WI-09. Evidence: browser workflow, keyboard/focus checks and desktop/narrow
captures using long names, unmeasured and reported fixtures.

AC-1 through AC-5 are **technically passed**; see `docs/review/12_WI_04_VERIFICATION.md`. Shared G-02 approval,
G-03 acceptance, G-04 engineering completion and G-05 broader release remain separate.

## Impact

Changes after approval: local workspace schema/storage service, a local model service
and routes registered before the SPA mount, optional runtime configuration, frontend
Models components/API client, focused tests, usage and verification documentation.
Legacy cloud routes and remote data remain outside this change.

After explicit approval, refine the existing Issue from this record, create its
linked branch with `gh issue develop`, implement/verify, sync specifications,
archive the verified change, push and open a PR with `Closes #4`. No protected-branch
operation or subsequent proposal is authorized by this work item.
