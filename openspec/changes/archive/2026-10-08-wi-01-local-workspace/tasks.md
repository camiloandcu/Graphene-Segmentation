## 1. Establish the runtime baseline

- [x] 1.1 After approval create a short-lived local branch, record Python/Node versions, and diagnose frontend build/type-check non-completion (AC-1; G-02/G-04).
- [x] 1.2 Reconcile local dependencies/install commands without cloud/training frameworks; apply only required setup/build fixes (AC-1, AC-3).

## 2. Implement durable storage

- [x] 2.1 Add workspace configuration, versioned SQLite metadata, relative paths and exclusive ownership (AC-2, AC-3).
- [x] 2.2 Implement staged durable publication, verified lookup, rollback and scoped recovery (AC-2).
- [x] 2.3 Verify write/restart/relocation, injected publication/transaction/interruption failures, missing/corrupt files, confinement, schema rejection and second-writer rejection (AC-2).

## 3. Connect the local workspace

- [x] 3.1 Replace eager initialization with local lifespan/health and eliminate secret printing (AC-1, AC-3).
- [x] 3.2 Serve built frontend/API through the loopback launcher and configure development origins and absent-assets errors (AC-1, AC-3).
- [x] 3.3 Add the minimal English readiness entry without login/cloud calls; review visual/keyboard/error states without implementing subsequent workflows (AC-1).

## 4. Verify and hand off

- [x] 4.1 Record clean setup/startup without credentials and outbound access after installation; inspect health/UI/listeners/logs and absent external imports/calls (AC-1, AC-3).
- [x] 4.2 Run affected backend checks and frontend build/type checks; record pass/fail/unverified AC evidence including an actual process restart (AC-1–AC-3; G-03/G-04).
- [x] 4.3 Update README and operational docs for installation/start/stop, limitations, data location, backup and restore (AC-1, AC-2; G-04).
- [x] 4.4 Make coherent Conventional Commits, publish the linked work branch and open its PR with `Closes #1`; after verified completion sync specs and archive, keeping pending stakeholder review explicit. No protected-branch merge/push or next proposal without approval (G-03/G-04).
