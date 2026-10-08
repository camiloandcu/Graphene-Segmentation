# Project context

Graphene Workspace is a local microscopy application for reviewing segmentation
masks and prioritizing image batches by few-layer graphene coverage. The app uses
React/Vite/TypeScript and FastAPI with local SQLite metadata and files. Training
runs separately in Colab. Intended capabilities and delivered behavior are
distinguished in the README and work-item records.

## Context navigation

- Product overview, delivered capabilities, setup and verification commands:
  `README.md`.
- Planning entry point: `docs/review/00_INDEX.md`.
- Product purpose and requirements: `docs/review/01_PRODUCT_BRIEF.md` and
  `docs/review/02_REQUIREMENTS_AND_UX.md`.
- Architecture: `docs/review/04_ARCHITECTURE.md`.
- Data and ML decisions: `docs/review/03_DATA_AND_ML_PLAN.md`.
- Work-item scope, decisions, dependencies and acceptance criteria:
  `docs/review/06_DECISIONS_AND_WORK_ITEMS.md`.
- GitHub Issue mapping and implementation references:
  `docs/review/08_GITHUB_WORK_ITEMS.md`.
- Current specifications: `openspec/specs/`.
- Active change proposals, designs and tasks: `openspec/changes/`.
- Completed change history: `openspec/changes/archive/`.
- Runtime and model-contract details: `docs/09_LOCAL_WORKSPACE.md` and
  `docs/10_PORTABLE_MODEL_CONTRACT.md`.

For a work-item request, locate its definition and approved OpenSpec change, then
read only the context relevant to its scope. Treat zero-padded identifiers such
as `WI-003` and `WI-03` as equivalent. Check recorded approval, dependencies and
blockers; an Issue alone does not establish implementation readiness.

## Session continuity

Keep changing status and decisions in the relevant work-item or OpenSpec change
documents. Record verification evidence in the review documents linked from
`docs/review/00_INDEX.md`. Before handing off unfinished work, update those records
with completed work, remaining tasks, branch/Issue/PR references, checks and
unresolved blockers. Inspect the actual branch and working tree when resuming.

## Project workflow

Follow the personal work guide and the approved OpenSpec design.

- Create or reuse the executable Work Item's GitHub Issue before coding.
- GitHub access for this project is authorized through `gh`.
- Create a short-lived branch linked with `gh issue develop`.
- Implement and verify the approved item, push coherent Conventional Commits,
  and open a Pull Request containing `Closes #<issue>` and acceptance evidence.
- Push and PR creation are part of completion, not optional follow-up offers.
- Never push, merge, or pull/update protected branches without explicit approval.
- Keep provisional Issues distinct from approved executable work.
- Sync specifications and archive verified OpenSpec work before handoff.
- Do not prepare another proposal without stakeholder approval.

This preference applies here. Do not modify global agent settings.
