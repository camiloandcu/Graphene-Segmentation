# local-model-management Specification

## Purpose
Provide lab members with bounded local model import, immutable package identity,
readable evaluation and explicit persistent selection without manual ML settings.
Keep technical compatibility separate from production inference and lab quality.
## Requirements
### Requirement: Validate before registering a local model
The local app SHALL accept bounded v1 ZIP imports using the WI-02 validator before
registering an immutable model identity and package metadata. Import SHALL NOT
change the selected model. Implements WI-04-AC-1/3.

#### Scenario: Compatible model is imported
- **GIVEN** model-validation extras and a compatible v1 package
- **WHEN** the user imports it through Models
- **THEN** the registry durably stores its exact model ID, bundle/model digests and validated metadata
- **AND** the UI confirms the model is available to select without manual ML configuration
- **AND** the prior selection remains unchanged, including an initially empty selection

#### Scenario: Identical package is retried
- **WHEN** the same model ID and identical bundle digest are imported again
- **THEN** the existing model is returned without a duplicate entry or selection change

#### Scenario: Model identity conflicts
- **GIVEN** a registered model ID
- **WHEN** a package reuses that ID with different bundle bytes
- **THEN** the app reports an identity conflict and preserves the original artifact, metadata and selection

### Requirement: Explicit durable selection checks current compatibility
Selection SHALL verify stored artifact integrity and current CPU compatibility
before atomically persisting the exact registered model ID. Failed selection MUST
preserve the prior committed choice. Implements WI-04-AC-2/3.

#### Scenario: User selects and restarts
- **GIVEN** two compatible registered models
- **WHEN** the user selects one and restarts the backend and browser
- **THEN** that exact ID and package identity remain selected in API and UI
- **AND** selection is acknowledged only after successful validation and durable commit

#### Scenario: Selection target is unavailable
- **WHEN** selection names an unknown, corrupt, missing or currently incompatible model
- **THEN** the app reports the specific reason and an actionable recovery step
- **AND** the prior committed selection is unchanged

### Requirement: Bound mutation work and preserve state on failure
Import and selection SHALL bound uploads, validation and concurrent work, enforce
limits on actual streamed bytes, retain resource-limited native validation, and
clean temporary artifacts/workers. Health SHALL remain responsive during validation.
Failed operations MUST NOT expose partial models or replace selection. Implements AC-3.

#### Scenario: Invalid or resource-limited import
- **GIVEN** an existing selected model
- **WHEN** an upload is malformed, incompatible, oversized or exceeds validation resources
- **THEN** the app rejects it with a safe specific reason and recovery action
- **AND** existing models and selection remain unchanged

#### Scenario: Competing or abandoned mutations
- **WHEN** concurrent requests exceed the validation slot or an upload disconnects/times out before commit
- **THEN** excess work receives a retryable busy response and abandoned work is cleaned
- **AND** no duplicate or partial registry state is published and health remains responsive

#### Scenario: Response is lost after commit
- **WHEN** the client loses an import or selection response after its durable commit
- **THEN** refetch returns the committed state and retrying identical import does not duplicate it

### Requirement: Recover without silently choosing a replacement
The registry SHALL expose availability separately from selection identity. Missing
or corrupt selected artifacts SHALL remain identifiable and unavailable without an
automatic fallback. Model management SHALL not require cloud accounts. Implements AC-4.

#### Scenario: Selected package is corrupted between restarts
- **WHEN** recovery detects a missing or corrupt selected artifact
- **THEN** the selected ID remains recorded and the UI offers explicit recovery
- **AND** the user can select another intact compatible registered model

#### Scenario: Model extras are absent
- **WHEN** the app starts without optional model-validation dependencies
- **THEN** local health and persisted model metadata remain accessible
- **AND** import and selection report the documented installation action without changing selection

### Requirement: Models interaction communicates actionable trustworthy states
The existing local shell SHALL offer accessible English import, details and
selection interactions with explicit empty, loading, pending, error, stale and
unavailable states. Evaluation SHALL distinguish unmeasured and supplied reported
evidence, and selection MUST NOT imply implemented prediction or certified quality.
Implements WI-04-AC-5.

#### Scenario: User completes management with keyboard or narrow viewport
- **WHEN** the user imports, opens details and selects a model with keyboard navigation or a narrow screen
- **THEN** controls have readable names, visible usable focus and non-color-only state feedback
- **AND** long metadata wraps, pending actions cannot be repeated accidentally and each failure offers a next action

#### Scenario: Evaluation and prediction limitations are shown
- **GIVEN** packages containing either unmeasured or reported evaluation
- **WHEN** the user opens model details or selects a model
- **THEN** supplied evidence remains labeled without invented accuracy or independent lab verification
- **AND** the UI states prediction is pending later implementation

#### Scenario: Connection or other-tab state changes
- **WHEN** a mutation response is uncertain or the user returns after another tab changes selection
- **THEN** the client refetches authoritative registry state before confirming selection
- **AND** retained last-confirmed data is visibly stale while recovery is pending
