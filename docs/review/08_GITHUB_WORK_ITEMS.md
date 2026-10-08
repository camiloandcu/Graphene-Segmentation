# GitHub work item tracking

Access: `gh`, authorized by the stakeholder. WI-01, WI-02 and WI-03 proposals are approved;
WI-03 and WI-04 are stakeholder accepted and merged; WI-05 software is approved, implemented and technically verified. Later items retain their provisional readiness. Creating Issues does not
approve their implementation or create additional OpenSpec proposals.

| Work item | Issue | Parent | State |
| --- | --- | --- | --- |
| WI-01 | [#1](https://github.com/camiloandcu/Graphene-Segmentation/issues/1) | INC-01 / F-03 | Merged via PR #15 |
| WI-02 | [#2](https://github.com/camiloandcu/Graphene-Segmentation/issues/2) | INC-01 / F-03 | Merged via PR #16 |
| WI-03 | [#3](https://github.com/camiloandcu/Graphene-Segmentation/issues/3) | INC-01 / F-01 | Merged via PR #17; stakeholder accepted 2026-10-08 |
| WI-04 | [#4](https://github.com/camiloandcu/Graphene-Segmentation/issues/4) | INC-01 / F-03 | Merged via PR #18; stakeholder accepted 2026-10-08 |
| WI-05 | [#5](https://github.com/camiloandcu/Graphene-Segmentation/issues/5) | INC-01 / F-01 | Software verified; real ready handoff/lab review pending; PR #19 open |
| WI-06 | [#6](https://github.com/camiloandcu/Graphene-Segmentation/issues/6) | INC-01 / F-02 | Provisional; refinement required |
| WI-07 | [#7](https://github.com/camiloandcu/Graphene-Segmentation/issues/7) | INC-01 / F-02 | Provisional; refinement required |
| WI-08 | [#8](https://github.com/camiloandcu/Graphene-Segmentation/issues/8) | INC-01 / F-02 | Provisional; refinement required |
| WI-09 | [#9](https://github.com/camiloandcu/Graphene-Segmentation/issues/9) | INC-01 / F-03 | Provisional; refinement required |
| WI-10 | [#10](https://github.com/camiloandcu/Graphene-Segmentation/issues/10) | INC-01 / F-04 | Provisional; refinement required |
| WI-11 | [#11](https://github.com/camiloandcu/Graphene-Segmentation/issues/11) | INC-01 / F-04 | Provisional; refinement required |
| WI-12 | [#12](https://github.com/camiloandcu/Graphene-Segmentation/issues/12) | INC-01 / F-04 | Provisional; refinement required |
| WI-13 | [#13](https://github.com/camiloandcu/Graphene-Segmentation/issues/13) | INC-01 / F-05 | Provisional; refinement required |
| WI-14 | [#14](https://github.com/camiloandcu/Graphene-Segmentation/issues/14) | INC-02 / F-06 | Provisional; refinement required |

WI-01 branch: `feat/wi-01-local-workspace`, linked using `gh issue develop 1`.
PR [#15](https://github.com/camiloandcu/Graphene-Segmentation/pull/15)
uses `Closes #1`; GitHub confirms the closing Issue association. Main merge is not authorized.

Checked 2026-10-08: PR #15 is merged. WI-02 reuses Issue #2. Branch
`feat/wi-02-portable-model-contract` was linked using `gh issue develop 2`
after explicit proposal approval. See [verification evidence](10_WI_02_VERIFICATION.md).
The prior restriction on protected-branch operations still applies to agent actions.

WI-02 PR [#16](https://github.com/camiloandcu/Graphene-Segmentation/pull/16)
uses `Closes #2`. Its verified specification is synced and change archived under
`2026-10-08-wi-02-portable-model-contract`. Stakeholder acceptance, Issue closure,
merge and release remain separate. GitHub confirms PR #16 merged on 2026-10-08;
no protected branch was updated by this WI-03 work.

WI-03: Issue #3 is open, checked 2026-10-08 using authorized `gh` access. The
[audit proposal](../../openspec/changes/archive/2026-10-08-wi-03-lab-dataset-audit/proposal.md) is
approved by the stakeholder on 2026-10-08. The stakeholder supplied the ZIP and
authorized a 90-minute limit. `feat/wi-03-lab-dataset-audit` was linked with
`gh issue develop 3`. Two local audit runs and 20 focused tests passed. See
[verification](11_WI_03_VERIFICATION.md). Lab review and stakeholder acceptance
remain pending; no later proposal is prepared.

WI-03 PR [#17](https://github.com/camiloandcu/Graphene-Segmentation/pull/17) uses
`Closes #3`; GitHub confirms the closing Issue association. Commits `27f4c9a`
(approved context map) and `d2223bb` (audit/evidence) were pushed on the linked
branch. The verified audit specification is synced and the change archived under
`2026-10-08-wi-03-lab-dataset-audit`. Issue closure, lab/stakeholder acceptance,
merge and release remain separate. No protected branch was updated.

Checked 2026-10-08 with authorized `gh`: PR #17 is now merged; local `main`
already contains merge commit `985d40b`. Historical handoff statements above
describe the prior submission state; stakeholder acceptance was confirmed on
2026-10-08. Label/group questions remain downstream decisions.

WI-04: Issue #4 was refined from the explicitly approved 2026-10-08 proposal.
Branch `feat/wi-04-local-model-management` is linked with `gh issue develop 4`.
All AC-1–5 are technically passed; see [verification](12_WI_04_VERIFICATION.md).
PR [#18](https://github.com/camiloandcu/Graphene-Segmentation/pull/18) uses `Closes #4`; GitHub confirms the closing Issue association.
Commits `50ca4cb` (approved design) and `2758654` (implementation/evidence) are pushed.
Specification sync/archive and final documentation references are recorded there; human acceptance,
Issue closure, merge and release remain separate. No later proposal is prepared.

Current check, 2026-10-08: PR #18 is merged and local `main` contains `36119c5`.
Stakeholder explicitly accepted WI-03 and WI-04 and authorized continuation to WI-05.
No agent protected-branch operation was performed. Earlier open/pending statements
are historical submission records.

WI-05: Issue #5 is refined from the explicitly approved proposal/design/specs
(2026-10-08). Branch `feat/wi-05-validated-labeled-datasets` is linked with
`gh issue develop 5`; approved-design commit `8447823`. See
[verification](13_WI_05_VERIFICATION.md) for 84 checks, complete real audit
reconciliation and fresh wheel consumption. AC-1–5 software behavior is verified;
genuine real ready handoff requires lab label/group/split decisions and remains
unverified. The specification is synced and verified software change archived.
[PR #19](https://github.com/camiloandcu/Graphene-Segmentation/pull/19) is open with `Closes #5`; GitHub confirms the closing Issue
association. Implementation `b17453f` and design `8447823` are pushed; final handoff
references are committed separately. Stakeholder item acceptance/merge remain separate.
