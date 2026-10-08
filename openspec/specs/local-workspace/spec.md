# local-workspace Specification

## Purpose

Provide an account-free local runtime with durable SQLite metadata and opaque
artifacts for the laboratory operator and downstream model-management services.
This specification implements WI-01 acceptance criteria AC-1 through AC-3;
model import, prediction and training are separate capabilities.

## Requirements

### Requirement: Account-free local startup
The documented Linux setup SHALL start without cloud credentials, login, external
service initialization, or training/inference dependencies. After installation,
normal startup SHALL work without outbound connectivity. Implements AC-1/AC-3.

#### Scenario: Start an installed workspace offline
- **GIVEN** documented dependencies/assets are installed without Supabase/JWT credentials
- **WHEN** the operator runs the local launcher with outbound access unavailable
- **THEN** the API/frontend start without accounts or cloud requests
- **AND** health reports initialized storage and no loaded model

#### Scenario: Existing credentials do not initialize cloud services
- **GIVEN** cloud credentials exist in the environment or legacy configuration files
- **WHEN** the default local app starts
- **THEN** no cloud/auth/training clients are imported or initialized
- **AND** credentials do not appear in logs

### Requirement: Honest local readiness
The frontend SHALL open without login and show runtime/storage readiness and no
ready model in English. It SHALL NOT present cloud workflows or unfinished
prediction as working. Health SHALL depend on local initialization, not legacy
model loading. Implements AC-1.

#### Scenario: Open an empty workspace
- **WHEN** the operator opens the running app with an empty workspace
- **THEN** the entry view is accessible without login and shows local readiness
- **AND** it states that no model is ready without offering functioning inference

#### Scenario: Storage initialization fails
- **WHEN** the workspace cannot be opened or has an unsupported schema version
- **THEN** initialization fails explicitly without reporting healthy storage
- **AND** existing data is not reset or overwritten

### Requirement: Durable workspace persistence
The store SHALL retain committed metadata and artifact bytes across process
restarts, using generated identities and relative paths. A usable lookup MUST
refer to an intact existing artifact. Implements AC-2.

#### Scenario: Restart after a successful write
- **GIVEN** metadata and fixture artifact bytes were committed through the workspace service
- **WHEN** a new process opens the same workspace after shutdown
- **THEN** the same identity, metadata, checksum and bytes remain available

#### Scenario: Restore in a different directory
- **GIVEN** a complete stopped workspace is copied to a new configured location
- **WHEN** the server opens the copy
- **THEN** its committed artifacts resolve without the old absolute path

### Requirement: Recoverable failed writes
Publication/recovery SHALL prevent failed writes from becoming usable records
with missing files. Recovery SHALL modify only the store's generated namespace.
Missing/corrupt committed artifacts MUST be unavailable. Implements AC-2.

#### Scenario: Metadata commit fails after publication
- **WHEN** failure occurs after file publication before successful metadata commit
- **THEN** no usable record is returned or persisted
- **AND** its unreferenced file is cleaned immediately or at exclusive startup recovery

#### Scenario: Process stops during publication
- **WHEN** the process stops at a staging/publication boundary and restarts
- **THEN** only intact committed records remain usable after recovery
- **AND** unreferenced generated files are removed without altering unrelated/legacy files

#### Scenario: A committed artifact is lost or altered
- **WHEN** an artifact is missing or fails integrity verification
- **THEN** the record is unavailable and the condition is reported
- **AND** no empty replacement is created

### Requirement: Workspace ownership and path confinement
The server SHALL confine artifact paths to the configured workspace and acquire
exclusive ownership before recovery/writes. Supports AC-2 under the documented
single-server operating conditions.

#### Scenario: Caller-controlled path escapes the workspace
- **WHEN** a request includes an absolute or traversing storage path
- **THEN** it is rejected or replaced by a generated confined path
- **AND** no external file is read or modified

#### Scenario: Second writer starts
- **GIVEN** a running server owns the workspace
- **WHEN** another server attempts to initialize it
- **THEN** it fails with an actionable ownership error before recovery/writes

### Requirement: Loopback defaults and secret-free diagnostics
The launcher SHALL bind API/built frontend to loopback by default. Development
serving SHALL also default to loopback with explicit local CORS origins and no
credentials. Logs/browser diagnostics MUST NOT expose secrets; browser errors
MUST NOT expose absolute internal paths. Implements AC-3.

#### Scenario: Inspect default listeners and logs
- **WHEN** the documented launcher runs with default settings
- **THEN** it listens on loopback rather than all interfaces
- **AND** startup/health diagnostics contain no cloud/JWT secrets

#### Scenario: Frontend assets are absent
- **WHEN** the operator runs the launcher before building assets
- **THEN** it explains the required build step without claiming the workspace is ready

