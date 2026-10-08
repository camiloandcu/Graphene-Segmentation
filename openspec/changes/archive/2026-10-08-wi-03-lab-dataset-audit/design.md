## Context and Goals

WI-03 answers a data-readiness question for the trainer and stakeholder. Existing
records describe a small lab segmentation dataset; actual files are not verified.
Acquisition metadata is reported absent. The audit must preserve that uncertainty.

Goal: trace each conclusion to actual files, reproducible checks or documented
human review. Non-goals match the proposal: no training, production importer,
external dataset inspection, cloud mutation or new annotation campaign.

## Decisions

### 1. Resolve input and effort before execution

Record the supplied export location, source/version, available license and
annotation provenance; mark unavailable metadata unknown. Obtain stakeholder
agreement on the investigation effort limit before running the spike. Report
unexamined evidence and remaining questions when that limit is reached; do not
interpret missing checks as passes or expand scope automatically.

Support the actual supplied format after inspection. Pixel-ID masks, documented
palette masks or segmentation polygons can provide pixel labels; bounding boxes
alone cannot. Retain original files and export splits. Reject unsafe file paths
and avoid unrestricted archive extraction; prefer an already extracted local
directory. Never run the cloud-writing legacy converter.

### 2. Inventory and mapping

Build a stable manifest with original IDs/relative paths, file checksums, decoded
dimensions, label associations, existing split, source, annotation provenance and
known group/augmentation lineage. Include dataset fingerprint, audit procedure,
environment and configuration. Separate actual file counts from metadata counts.

Map documented source classes explicitly to the existing canonical IDs:
0 background, 1 few-layer, 2 bulk; 255 ignored. Never infer mapping from source
numeric IDs or visual color. Unknown classes or ambiguous thickness definitions
remain unresolved until reviewed. Retain source values as evidence. Do not treat
an unlabeled image as a verified background example or model output as ground truth.

Check decodability, image/mask dimensions, legal class values, missing labels,
invalid geometry and incompatible polygon overlaps where applicable. Count
class pixels and image support; connected components, if reported, are proxies
and do not establish physical flake-instance counts. Report ignored pixels and
unsupported label cases separately rather than silently normalizing them.

### 3. Visual evidence and duplicate review

Choose deterministic examples covering observed classes, dimensions, anomalies
and background/ignore cases where present; record the selection and actual review
coverage. Overlays use explicit colors at original image geometry. Visual review
can reveal label problems but cannot verify physical thickness without lab evidence.

Compare byte checksums and decoded-pixel identity. Use a documented image-similarity
method only to propose near-duplicate/overlapping-field candidates; record its
settings and review candidate pairs. Distinguish confirmed duplicates, suspected
overlap and unresolved cases. Do not claim that a negative similarity check proves
independent acquisition. Record conflicting annotations for duplicate images.

### 4. Proposed split, not an invented independent test

Preserve supplied split roles as evidence. Group confirmed duplicates and known
augmentation families before proposing assignment. Any correction of existing
roles remains a stakeholder-reviewed proposal, with original and proposed roles
recorded. Unresolved overlap pairs must be excluded or conservatively co-grouped
in the proposal, with the reason stated.

Record deterministic assignment settings and per-split image/class support when
a defensible candidate split is possible. Do not invent acquisition groups, split
percentages or an independent test claim. If groups or class support cannot
support evaluation, provide a manifest of exclusions/unassigned entries and the
specific blocking evidence rather than forcing a training/validation/test split.

### 5. Evidence and recommendation

Place the tracked procedure, sanitized summary, decision record and acceptance
status in `docs/review/wi03/`, using ordered document names. Local evidence output
contains inventory, checks, duplicate review, candidate split and overlays;
private data/evidence paths are supplied at execution time and kept outside Git.
Record evidence fingerprints so the trainer can match the report to the export.

For each WI-03 criterion, report passed, failed or unverified and its evidence.
Recommend readiness, readiness conditional on explicit corrections, or an
inconclusive/unsuitable finding. List limits and the next stakeholder/trainer
action. Stakeholder review, technical verification and Issue closure are distinct.

## Risks and Alternatives

- Small support or unknown acquisition grouping limits generalization claims.
- Similarity methods can miss overlaps or flag unrelated images; inspect candidates
  and preserve uncertainty.
- Missing source mapping or incomplete labels can prevent valid class counts;
  document the block instead of guessing.
- Reusing the legacy cloud converter would introduce writes and implicit mapping;
  use a standalone local procedure tailored to this export instead.
- A generic importer would expand WI-03 into WI-05; keep reusable work proportional
  to the evidence needed for this spike.

## Execution and Handoff

After proposal approval and input/effort resolution, reuse Issue #3 and create an
Issue-linked short-lived branch with `gh issue develop`. Implement the audit,
verify meaningful failure boundaries and inspect real output. Update planning and
review records, commit/push and open a PR with `Closes #3` and acceptance evidence.
Sync/archive only after required technical evidence is verified. Required human
review remains explicit. No protected branch update is authorized.

## Open Questions

1. Where is the lab export, and what format/version does it contain?
2. What effort limit bounds this investigation?
3. If source definitions are ambiguous, who can confirm few-layer/bulk mapping?

Proposal approval was received on 2026-10-08. The stakeholder then supplied the
version-2 COCO polygon ZIP and authorized a 90-minute investigation and local
relocation. Both execution-input questions are resolved. Name-to-canonical mapping
is explicit; physical thickness and group definitions remain lab-review questions.
The audit delivers a supported conditional/inconclusive answer rather than
silently assuming those definitions or independent evaluation readiness.
