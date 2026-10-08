# Project repair review

Status: WI-01 implementation approved and technically verified; broader release
and later proposals remain pending.
Checked: 2026-10-07.

Current step: WI-01 was approved and implemented. Its single
[OpenSpec proposal](../../openspec/changes/archive/2026-10-08-wi-01-local-workspace/proposal.md),
[technical design](../../openspec/changes/archive/2026-10-08-wi-01-local-workspace/design.md),
[behavior specification](../../openspec/changes/archive/2026-10-08-wi-01-local-workspace/specs/local-workspace/spec.md),
and [tasks](../../openspec/changes/archive/2026-10-08-wi-01-local-workspace/tasks.md) record the approved work.

Read in this order:

1. [Product brief](01_PRODUCT_BRIEF.md): lab task, users, value, success.
2. [Requirements and UX](02_REQUIREMENTS_AND_UX.md): release scope and user flows.
3. [Data and ML plan](03_DATA_AND_ML_PLAN.md): evidence, training, evaluation, export.
4. [Architecture](04_ARCHITECTURE.md): local deployment and integration contract.
5. [Audit](05_CURRENT_PROJECT_AUDIT.md): findings and baseline verification.
6. [Decisions and work items](06_DECISIONS_AND_WORK_ITEMS.md): increments, features,
   executable items, dependencies, acceptance evidence, and implementation tasks.
7. [Dataset source evidence](07_DATA_SOURCE_EVIDENCE.json): checked source metadata and annotation counts.
8. [GitHub tracking](08_GITHUB_WORK_ITEMS.md): Issues and implementation branches.
9. [WI-01 verification](09_WI_01_VERIFICATION.md): acceptance and browser evidence.

Confirmed stakeholder decisions take precedence over recommendations. Open decisions
must be resolved or explicitly accepted as assumptions before their dependent work.
WI-01 local architecture, scope and acceptance criteria were approved. Unrelated
ML decisions and later work items remain subject to their own review.

Application code changed only for the approved WI-01 local foundation. Dataset inspections
used public metadata and byte ranges; no external account was accessed.
