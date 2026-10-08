## ADDED Requirements

### Requirement: Transactional model-registry upgrade preserves local artifacts
The workspace SHALL upgrade schema v1 to the model-registry schema transactionally,
preserving existing artifact records and files. Unsupported future versions MUST
fail with a compatible-version recovery message. Implements WI-04-AC-4.

#### Scenario: Existing workspace upgrades
- **GIVEN** a schema-v1 workspace with unrelated opaque artifacts
- **WHEN** the app opens it with the model-registry schema
- **THEN** original artifact identities, metadata and bytes remain intact
- **AND** model registry and initially empty selection are available

#### Scenario: Migration is interrupted
- **WHEN** failure interrupts the schema upgrade
- **THEN** reopening observes either the complete prior schema or complete upgraded schema
- **AND** no partial migration loses original artifact records

### Requirement: Model publication and recovery agree across files and metadata
Model import SHALL publish its file before a single artifact-and-model metadata
transaction. Startup recovery SHALL remove generated unreferenced/staging files
and flag missing/corrupt referenced files without erasing selected identity.
Implements WI-04-AC-3/4.

#### Scenario: Publication fails before metadata commit
- **WHEN** import is interrupted after file publication but before the metadata transaction commits
- **THEN** no registered model or selection change becomes visible
- **AND** startup cleans the generated orphan without removing unrelated artifacts

#### Scenario: Registry commit succeeds before response is lost
- **WHEN** the metadata transaction commits and the app stops before responding
- **THEN** startup recovers the committed model and its intact artifact together
- **AND** existing selected identity remains unchanged by import

### Requirement: Local health separates selection from inference loading
Startup and health SHALL remain independent of optional model runtimes. Health
SHALL report the actual schema version and MUST NOT claim a production inference
model is loaded merely because a registered model is selected. Implements AC-4/5.

#### Scenario: Selected model without inference implementation
- **WHEN** a registered model is selected in this management-only slice
- **THEN** workspace connection remains healthy and selection is separately visible
- **AND** `model_loaded` remains false until an implemented inference runtime loads a model
