## ADDED Requirements

### Requirement: Canonical source validation
The system SHALL validate the supported local COCO polygon export without modifying
source bytes, account for all images and annotations, and resolve reviewed category
names to canonical background 0, few-layer 1 and bulk 2. It SHALL preserve original
geometry and reject unsupported or malformed records before publishing a ready
artifact. Ignore 255 SHALL remain annotation-only. Implements WI-05-AC-1.

#### Scenario: Reversed source category IDs
- **WHEN** the reviewed source declares category 1 bulk and category 2 few-layer
- **THEN** its valid raster masks use 2 bulk and 1 few-layer at original coordinates

#### Scenario: Invalid or unresolved source
- **WHEN** an image is missing, geometry is inconsistent, a polygon is malformed or an annotated category is unresolved
- **THEN** validation identifies the affected record and no ready artifact is published

### Requirement: Explicit label review and origin
The system SHALL require source-bound human annotation eligibility, category,
completeness/background and conflict decisions for every included sample. Prediction,
unknown or missing annotation origin SHALL be ineligible. Conflicts SHALL fail by
default; explicitly reviewed conflicts MAY become 255 deterministically. Implements
WI-05-AC-4.

#### Scenario: Saved predictions are supplied as labels
- **WHEN** a candidate sample has prediction or unknown origin despite legal PNG values
- **THEN** it cannot enter an active training or evaluation split

#### Scenario: Real audit decisions remain unresolved
- **WHEN** the audited export is prepared without required lab review decisions
- **THEN** an actionable blocked report is produced and no training-ready manifest exists

#### Scenario: Reviewed conflict ignore
- **WHEN** a source-bound review explicitly authorizes ignoring overlapping classes
- **THEN** every conflict pixel becomes 255 independent of polygon order and the policy/counts are retained

#### Scenario: Unannotated background candidate
- **WHEN** an image has no foreground annotations
- **THEN** inclusion requires explicit verified background-only review; absence of polygons alone does not establish a negative image

### Requirement: Reviewed split identity and limitations
The system SHALL preserve original roles separately from explicit reviewed roles,
require one role or reasoned exclusion per image, prevent cross-role exact duplicates
and known groups, and require review dispositions for supplied grouping candidates.
It SHALL retain evaluation limitations without inventing acquisition metadata or
random assignments. Implements WI-05-AC-3.

#### Scenario: Supplied roles are deferred
- **WHEN** source train/validation/test roles exist but effective assignments are unreviewed
- **THEN** source roles remain evidence and readiness is blocked

#### Scenario: Reviewed split isolation fails
- **WHEN** an exact decoded duplicate or known acquisition group spans active roles
- **THEN** publication is rejected with the affected sample identities

#### Scenario: Explicit exploratory evaluation
- **WHEN** reviewed roles meet isolation rules but acquisition independence is unknown and exploratory use is acknowledged
- **THEN** the artifact retains that limitation and does not claim an independent benchmark

### Requirement: Reproducible traceable handoff
The system SHALL publish a versioned handoff retaining source identity/license,
canonical mapping, review provenance, explicit unknowns, sample/artifact digests,
original/effective roles and grouping evidence. Identical inputs/settings SHALL
produce identical dataset and split fingerprints. Implements WI-05-AC-2.

#### Scenario: Repeated preparation
- **WHEN** the same source, review and conversion settings are prepared at different destinations
- **THEN** dataset and split fingerprints agree and source bytes remain unchanged

#### Scenario: Reviewed assignment changes
- **WHEN** a sample's reviewed role or group changes
- **THEN** split and dataset identity change while original source roles remain recorded

### Requirement: Bounded complete publication and consumption
The system SHALL enforce source/read/image resource limits and safe paths, stage
complete artifacts before publication, and preserve existing outputs on failure.
The consumer SHALL verify schema, readiness, file inventory, digests, fingerprints,
mask semantics and split invariants before yielding samples. Implements WI-05-AC-5.

#### Scenario: Interrupted publication
- **WHEN** preparation fails or stops before complete publication
- **THEN** incomplete staging is not accepted as a ready dataset and source/prior outputs remain intact

#### Scenario: Tampered or diagnostic directory
- **WHEN** the consumer receives changed bytes, missing files, unsafe paths or a blocked report directory
- **THEN** it rejects the directory with a specific reason before yielding training samples

#### Scenario: Offline ready handoff
- **WHEN** a valid source and complete genuine review pass preparation and consumer checks
- **THEN** the trainer can iterate the explicit active roles with original-resolution images and aligned canonical masks without accounts or cloud services
