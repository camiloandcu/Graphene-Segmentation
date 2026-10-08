# lab-dataset-audit Specification

## Purpose
Define the evidence required to audit the supplied lab segmentation export and
support a truthful training/evaluation-readiness decision for the trainer and
stakeholder. This is an audit-deliverable contract, not an application importer.

## Requirements
### Requirement: Traceable actual dataset inventory
The audit deliverable SHALL inventory the supplied export with reproducible file
identity, image/label counts, dimensions, explicit source-to-canonical mapping,
class support and annotation provenance. Missing version/license or metadata
SHALL be identified as unknown. Source files SHALL remain unchanged.

#### Scenario: Export contains valid and invalid label associations
- **WHEN** the supplied export includes missing labels, invalid geometry or unsupported class values
- **THEN** the inventory records affected entries and specific findings separately from valid class support, with source checksums and documented audit settings

#### Scenario: Source class meaning is unresolved
- **WHEN** source IDs or colors lack a documented, reviewed class meaning
- **THEN** the report marks mapping unresolved and does not invent canonical labels or treat missing annotations as verified background

### Requirement: Reviewable label and overlap evidence
The audit deliverable SHALL include representative label overlays and exact and
near-duplicate/overlap evidence, with actual human review coverage stated.
Confirmed findings, candidates and unknown acquisition grouping SHALL be distinct.

#### Scenario: Similar images occur across supplied splits
- **WHEN** duplicate or overlap candidates are found across existing split roles
- **THEN** evidence identifies the affected original entries, review outcome and proposed grouping/exclusion without silently rewriting source split roles

### Requirement: Honest split recommendation
The audit deliverable SHALL provide a proposed split or exclusion/unassigned
manifest with class support, documented assignment settings and remaining leakage
uncertainty. It SHALL NOT assert independent acquisition from missing metadata.

#### Scenario: Independent evaluation cannot be supported
- **WHEN** acquisition grouping or class support is insufficient for a defensible evaluation split
- **THEN** the report explains the limitation and blocking next step instead of forcing an independent test claim

### Requirement: Bounded investigation and actionable conclusion
Execution SHALL require an authorized dataset route, explicit proposal approval
and a stakeholder-agreed effort limit. The report SHALL state evidence coverage,
limits, next actions and passed/failed/unverified status for WI-03-AC-1 through
WI-03-AC-3. An evidenced inconclusive finding SHALL be a valid recommendation.

#### Scenario: Agreed effort limit is reached
- **WHEN** the investigation reaches its agreed limit with unresolved evidence
- **THEN** the report distinguishes completed checks from unexamined questions and presents a bounded next step without marking unperformed checks as passed
