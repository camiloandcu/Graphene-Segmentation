## MODIFIED Requirements

### Requirement: Explicit label review and origin
The system SHALL require source-bound human annotation eligibility, category,
coverage mode, background and conflict decisions for every included sample.
Prediction, unknown or missing annotation origin SHALL remain ineligible. Dense
v1 SHALL retain its exhaustive/verified-background requirements. Explicit partial
v2 MAY admit reviewed incomplete human labels without claiming exhaustive coverage;
unannotated pixels SHALL be unknown 255 except source-bound reviewed background
anchors. Conflicts SHALL fail by default; explicitly reviewed conflicts MAY become
255 deterministically. Implements WI-05-AC-4 and WI-06-AC-1.

#### Scenario: Saved predictions are supplied as labels
- **WHEN** a candidate sample has prediction or unknown origin despite legal PNG values
- **THEN** it cannot enter an active training or evaluation split

#### Scenario: Real audit decisions remain unresolved
- **WHEN** the audited export is prepared without required lab review decisions for its declared coverage mode
- **THEN** an actionable blocked report is produced and no training-ready manifest exists

#### Scenario: Reviewed conflict ignore
- **WHEN** a source-bound review explicitly authorizes ignoring overlapping classes
- **THEN** every conflict pixel becomes 255 independent of polygon order and the policy/counts are retained

#### Scenario: Unannotated background candidate
- **WHEN** an image has no foreground annotations
- **THEN** inclusion as a negative image requires explicit verified background-only review; absence of polygons alone does not establish background

#### Scenario: Explicit partial supervision
- **WHEN** a v2 partial review approves eligible foreground labels and documented background anchors
- **THEN** original labels and reviewed anchors supply supervised class IDs while every other unannotated pixel remains 255
- **AND** source support, supervised support, ignored counts/reasons and anchor provenance are preserved

## ADDED Requirements

### Requirement: Partial supervision identity and compatibility
The dataset consumer SHALL distinguish dense-v1 semantics from explicit partial-v2
semantics, validate supervised masks against source labels/anchors and bind mode,
mask digests and anchor provenance to dataset and supervision fingerprints.
Partial-mode conversion SHALL NOT silently relabel an existing v1 handoff. Unknown
pixels SHALL NOT become background through absence of labels or prediction votes.
Implements WI-06-AC-1/4.

#### Scenario: Dense compatibility is preserved
- **WHEN** an existing valid dense-v1 artifact is checked with the updated consumer
- **THEN** its validation, mask meaning and fingerprints remain unchanged
- **AND** a v1-only consumer rejects unsupported v2 rather than interpreting unknown coverage as background

#### Scenario: Background anchor is stale or contradictory
- **WHEN** an anchor references changed source/image identity, invalid geometry or a region intersecting source foreground or ignored conflicts
- **THEN** the artifact is rejected before supervised samples are yielded

#### Scenario: Supervision changes while image and role remain fixed
- **WHEN** reviewed anchor geometry/evidence or supervised pixels change
- **THEN** dataset and supervision fingerprints change and downstream resume/metric identity detects the mismatch
- **AND** original source and split identities remain separately traceable
