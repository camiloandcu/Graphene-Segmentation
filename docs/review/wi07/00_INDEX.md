# WI-07 model-selection review

Checked: 2026-10-11. Consumer: stakeholder selecting a feasible exploratory model
and WI-08 exporter. Status: full proposal/design/specifications explicitly approved;
implementation started. Real-run/selection acceptance remains separate.

1. [Implementation/session evidence](02_IMPLEMENTATION_AND_SESSION_RECORD.md):
   checks, actual access, acceptance status and remaining work.
2. [Literature and candidate evidence](01_LITERATURE_AND_CANDIDATES.md): primary
   sources, relevance, reproducibility limits and proposed experiment order.
3. [Proposal](../../../openspec/changes/wi-07-model-selection/proposal.md): outcome,
   acceptance criteria, staged effort boundary and approval decisions.
4. [Design](../../../openspec/changes/wi-07-model-selection/design.md): partial-label
   metrics, candidate gates, session recovery, resource measurements and test freeze.
5. [Specification](../../../openspec/changes/wi-07-model-selection/specs/model-selection-evaluation/spec.md)
   and [tasks](../../../openspec/changes/wi-07-model-selection/tasks.md).

The stakeholder selected U-Net + SegFormer-B0 + gated DINOv3 on 2026-10-11,
requested current 2D-material/related-microscopy evidence, and accepts Colab work
across multiple day sessions. No fixed elapsed-time/GPU-hour cap was requested;
the finite experiment stages and stopping rule were included in the subsequent approval.
The stakeholder subsequently explicitly approved the complete review package on
2026-10-11. Do not reopen its settled scope; actual candidate gates remain required.

WI-06 PR #20 is merged, checked using authorized `gh` on 2026-10-11; local
`main` already contains `7d4954d`. Its epoch-23 checkpoint and approved partial-v2
dataset are the baseline, with grouped 31/4/5 roles retained. See
[training evidence](../14_WI_06_VERIFICATION.md) and
[label/background support](../wi06/03_LABEL_CONFIRMATION_AND_BACKGROUND_REVIEW.md).
Validation has four images; test has five images and no reviewed background.
The final test has not been scored. Unknown pixels remain unknown.

Issue [#7](https://github.com/camiloandcu/Graphene-Segmentation/issues/7) is refined
from the approved proposal. Branch `feat/wi-07-model-selection` is linked using
`gh issue develop 7`. The evaluator, challenger adapters, CLI and notebook are implemented and verified
with synthetic contracts. [Implementation/session evidence](02_IMPLEMENTATION_AND_SESSION_RECORD.md)
records actual Drive checkpoint verification and the connected T4 setup. Real
validation reproduction, challenger training and stakeholder selection remain pending.

Planning verification: `openspec validate --all --strict` passed all six current
specifications and the single WI-07 change (7 passed, 0 failed). Local-link,
newline and whitespace checks passed for all 11 affected Markdown files and
103 link targets; `git diff --check` passed. Planning verification is distinct from the subsequent implementation checks;
see the linked session record for current checks and acceptance limitations.
