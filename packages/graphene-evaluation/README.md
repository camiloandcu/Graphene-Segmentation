# Graphene model evaluation

Checkpoint-bound development evaluation and reviewed model comparisons for the
local Graphene Workspace. This package keeps WI-06 training source and checkpoint
formats intact. Reports preserve the distinction between reviewed supervision
and unknown image regions.

Install it alongside the dataset, model-contract and training packages. Use
`graphene-evaluate score` for validation, `benchmark` for warmed inference,
`compare` for common-support comparisons, and `freeze` only after an actual
stakeholder decision. `graphene-experiment` runs and resumes approved semantic
challengers. Synthetic tests demonstrate contracts, not model quality.

See [the evaluation guide](../../docs/15_MODEL_SELECTION_EVALUATION.md) for the
protocol, commands and limitations. No model is designated the winner until the
real comparisons and human review are recorded.
