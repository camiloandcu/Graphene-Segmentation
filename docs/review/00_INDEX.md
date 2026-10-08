# Project repair review

Status: WI-01 through WI-03 merged; WI-03 lab acceptance pending. WI-04 proposal
prepared for review; implementation and broader release remain pending.
Checked: 2026-10-08.

Current item: the stakeholder requested continuation with WI-04 on 2026-10-08.
Review its single [change entry point](../../openspec/changes/wi-04-local-model-management/README.md),
[proposal](../../openspec/changes/wi-04-local-model-management/proposal.md),
[design](../../openspec/changes/wi-04-local-model-management/design.md),
[requirements](../../openspec/changes/wi-04-local-model-management/specs/local-model-management/spec.md)
and [tasks](../../openspec/changes/wi-04-local-model-management/tasks.md).
Explicit approval is pending; no implementation has started. WI-01/WI-02
dependencies are merged. All WI-04 acceptance criteria remain unverified.
Proposal checks on 2026-10-08: strict OpenSpec validation for
`wi-04-local-model-management` and `git diff --check` passed. Application checks
are pending implementation.

Previous item: the stakeholder approved WI-03 and supplied the export with a
90-minute investigation limit. Its
[proposal](../../openspec/changes/archive/2026-10-08-wi-03-lab-dataset-audit/proposal.md),
[design](../../openspec/changes/archive/2026-10-08-wi-03-lab-dataset-audit/design.md),
[audit requirements](../../openspec/changes/archive/2026-10-08-wi-03-lab-dataset-audit/specs/lab-dataset-audit/spec.md)
and [tasks](../../openspec/changes/archive/2026-10-08-wi-03-lab-dataset-audit/tasks.md) were explicitly
approved on 2026-10-08. See the [audit report](wi03/00_INDEX.md) and
[WI-03 verification](11_WI_03_VERIFICATION.md). The audit is technically verified;
lab review and stakeholder acceptance remain separate. Authorized read-only `gh`
inspection confirmed PR #17 merged on 2026-10-08; local `main` already contains it.

Previous item: WI-02 is implemented and merged following explicit stakeholder approval;
review its single [proposal](../../openspec/changes/archive/2026-10-08-wi-02-portable-model-contract/proposal.md),
[technical design](../../openspec/changes/archive/2026-10-08-wi-02-portable-model-contract/design.md),
[specification](../../openspec/changes/archive/2026-10-08-wi-02-portable-model-contract/specs/portable-model-contract/spec.md),
and [tasks](../../openspec/changes/archive/2026-10-08-wi-02-portable-model-contract/tasks.md).
See [WI-02 verification](10_WI_02_VERIFICATION.md) for acceptance evidence and
the boundary between compatibility and real model performance.

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
10. [WI-02 verification](10_WI_02_VERIFICATION.md): contract and geometry evidence.
11. [WI-03 verification](11_WI_03_VERIFICATION.md): lab data audit and readiness evidence.

Confirmed stakeholder decisions take precedence over recommendations. Open decisions
must be resolved or explicitly accepted as assumptions before their dependent work.
WI-01 local architecture, scope and acceptance criteria were approved. Unrelated
ML decisions and later work items remain subject to their own review.

Application startup is the WI-01 local foundation; WI-02 adds a shared contract
library and optional validation dependencies. Dataset inspections
used public metadata/byte ranges for initial planning and a stakeholder-supplied
local export for WI-03; no dataset account was accessed.
