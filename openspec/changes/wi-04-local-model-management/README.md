# WI-04 review entry point

Status: explicitly approved on 2026-10-08; implementation in progress.
Request: continue with WI-04. This authorizes preparing this single proposal;
the stakeholder subsequently approved proposal/design/specs and policies.

Read in order:

1. [Proposal](proposal.md): outcome, scope and numbered acceptance criteria.
2. [Design](design.md): storage/API decisions, recovery and Models interaction.
3. [Requirements](specs/local-model-management/spec.md): observable scenarios.
4. [Tasks](tasks.md): implementation and verification after approval.

Reuses [Issue #4](https://github.com/camiloandcu/Graphene-Segmentation/issues/4).
WI-01 and WI-02 are merged and present on local `main`. WI-03 is also merged;
its unresolved lab acceptance is not a dependency of model import/selection.

Branch: `feat/wi-04-local-model-management`, linked with `gh issue develop 4`.
Implementation and acceptance evidence are in progress; no PR yet. All WI-04 acceptance criteria remain unverified.
Validation: `openspec validate wi-04-local-model-management --strict --no-interactive`
and `git diff --check` passed on 2026-10-08. These verify proposal format and patch
whitespace, not application behavior.
Review the proposed policies: explicit selection after import, identical-package
deduplication, rejection of conflicting model IDs, and preservation of an
unavailable selection with a clear recovery action. Approval covers these policies.
