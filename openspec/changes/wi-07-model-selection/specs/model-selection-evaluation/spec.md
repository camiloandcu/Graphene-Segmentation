## ADDED Requirements

### Requirement: Traceable isolated evaluation
The evaluation workflow SHALL validate dataset/split/supervision and checkpoint
identities, preserve approved roles and canonical classes, and exclude unknown
pixels and padding from supervised metrics (WI-07-AC-1).

#### Scenario: Partial lab artifact evaluated on development
- **WHEN** a verified candidate is evaluated on the approved validation role
- **THEN** original-coordinate counts retain supervision identity and unknown
  coverage without scoring test/excluded samples or converting unknown to background

#### Scenario: Identity or role mismatch
- **WHEN** data/checkpoint digests, mappings or requested roles violate the recorded protocol
- **THEN** evaluation fails before generating a misleading comparison or changing prior artifacts

### Requirement: Measured candidates with explicit gates and recovery
The spike SHALL produce real baseline/SegFormer evidence, an actual DINOv3 probe
or supported exclusion, and documented 2D-TLK/MaskTerial admission decisions within
the reviewed finite stages. Admitted training SHALL retain reproducible initialization,
configuration and durable cross-session state (WI-07-AC-2).

#### Scenario: Candidate admitted
- **WHEN** license/access, pretrained identity, finite partial-loss optimization,
  resource and compatibility checks pass
- **THEN** the candidate uses the declared training roles/protocol and retains
  actual run/checkpoint/environment evidence for comparison

#### Scenario: Optional candidate cannot pass its gate
- **WHEN** required access, reproducibility or resource evidence is unavailable
- **THEN** the report records the specific exclusion without pretending a run succeeded
  or replacing weights/architecture silently

#### Scenario: Colab resumes on a later day
- **WHEN** a replacement interactive runtime restores a complete retained generation
- **THEN** checkpoint/config/data integrity is verified and optimization continues
  with its saved state and schedule rather than restarting the experiment

### Requirement: Supported quality and detection reporting
Reports SHALL include aggregate/per-image supervised confusion metrics, deterministic
annotated-component matching and misses, known-support unmatched detections,
indeterminate unknown detections and explicit unavailable reasons for unsupported
full-image metrics (WI-07-AC-3).

#### Scenario: Prediction crosses unknown coverage
- **WHEN** a predicted component intersects unknown pixels
- **THEN** its unknown extent is reported and an unmatched component is indeterminate
  rather than automatically a false detection or a correct unannotated flake

#### Scenario: Reference class or ranking support absent
- **WHEN** a class denominator or exhaustive coverage ranking reference is absent
- **THEN** the corresponding measure is null with support/reason and no perfect
  score or fabricated ranking agreement is assigned

### Requirement: Development trade-offs and feasibility evidence
The spike SHALL report development-only threshold/geometry comparisons, finalist
seed sensitivity, supported uncertainty, original-coordinate errors and measured
training/GPU/CPU resources with hardware and protocol identity (WI-07-AC-4).

#### Scenario: Finalists compared
- **WHEN** candidate settings/configurations are shortlisted on validation
- **THEN** quality and resource evidence uses common support, retains ablations
  and seed variability, and distinguishes small-sample uncertainty from independent-test evidence

#### Scenario: A resource or independence claim is unverified
- **WHEN** target-hardware measurement or acquisition-group identity is unavailable
- **THEN** the report records the limitation instead of borrowing published latency
  or assuming independent flakes/pixels

### Requirement: Reviewed decision and frozen test
The result SHALL contain a stakeholder-reviewed feasible model/settings recommendation
or an explicitly inconclusive answer and next step. Final-test evaluation SHALL
require a prior frozen identity, with explicit deferral allowed; results SHALL NOT
be used to reopen selection (WI-07-AC-5).

#### Scenario: Test requested before selection freeze
- **WHEN** no reviewed immutable checkpoint/settings/support record exists
- **THEN** test predictions/scoring/panels are refused and development evidence remains separate

#### Scenario: Frozen selection evaluated or deferred
- **WHEN** the stakeholder freezes one candidate or explicitly defers final-test evaluation
- **THEN** the handoff records that choice and its supported results/limitations
  without claiming full-background accuracy, guaranteed optimum or ONNX parity
