# portable-model-contract Specification

## Purpose
Define a portable ONNX package and shared tensor, class, geometry and decision semantics
for the Colab exporter, local inference runtime and custom-model authors. Require bounded
compatibility validation without treating package compatibility as measured lab accuracy.
## Requirements
### Requirement: Explicit versioned package semantics
The shared producer/consumer contract SHALL define a v1 package containing exactly
`model.onnx`, `manifest.json` and `evaluation.json`. Identity, checksum, canonical
classes, normalization, geometry, tensor names/shapes/types and decision semantics
MUST be explicit and resolved identically by both consumers. Implements WI-02-AC-1.

#### Scenario: Validate a supported producer package
- **GIVEN** a synthetic package produced using the documented v1 schema/profile
- **WHEN** the consumer validates it
- **THEN** it returns the declared model identity, checked artifact digest and matching preprocessing/output semantics
- **AND** it never guesses an adapter from architecture text or the filename

#### Scenario: An incompatible or ambiguous schema is supplied
- **WHEN** required semantics are absent, JSON keys are duplicated, fields conflict or schema/profile is unsupported
- **THEN** validation rejects the package with a specific compatibility reason
- **AND** no implicit class mapping, normalization or geometry default makes it compatible

### Requirement: Canonical three-class graph compatibility
Supported graphs SHALL consume one fixed float32 RGB NCHW tensor with batch 1
and emit one finite float32 NCHW full-input-resolution logit tensor with exactly
three channels, ordered 0 background, 1 few-layer, 2 bulk. One-channel binary
outputs MUST NOT be interpreted as these three classes. Implements AC-1/AC-3.

#### Scenario: A three-class manifest accompanies a binary graph
- **WHEN** the declared class list has three entries but the graph has one output channel
- **THEN** compatibility validation rejects the package
- **AND** it does not derive class IDs from numeric score ranges

#### Scenario: Graph interface disagrees with the manifest
- **WHEN** graph names, rank, shape, dtype, spatial output dimensions or supported IR/opset disagree with the declaration
- **THEN** validation reports the interface incompatibility before returning success

### Requirement: Bounded archive and model checking
Validation SHALL enforce configured packed/expanded/member/resource bounds on
both declarations and actual data. It SHALL reject unsafe/extra/duplicate archive
members, wrong digests, external tensors and unsupported graph constructs.
Native parsing/checking/smoke execution MUST run in a disposable resource-limited
CPU worker and never in the serving process. Implements AC-2/AC-3.

#### Scenario: Unsafe or oversized archive is supplied
- **WHEN** members escape the allowed three root names, are duplicated/symlinked/encrypted or exceed a configured size bound
- **THEN** validation rejects the archive with a specific reason
- **AND** it does not perform unrestricted extraction or modify workspace records

#### Scenario: Data integrity fails
- **WHEN** the model digest, byte size, CRC or actual streamed member length disagrees with the package declaration
- **THEN** validation rejects the package and does not return a compatible model

#### Scenario: External or unsupported graph behavior is present
- **WHEN** the graph contains external tensor references, unsupported domains/functions/subgraphs or unsupported declarations
- **THEN** validation rejects it without resolving external files or registering custom operators

#### Scenario: CPU validation exceeds resources or returns invalid output
- **WHEN** the validation worker exceeds its configured time/memory bounds, fails or returns non-finite/incompatible logits
- **THEN** the parent reports a bounded validation failure and reaps the worker
- **AND** temporary validation artifacts are cleaned and local runtime state is unchanged

### Requirement: Shared RGB preprocessing
Producer and consumer SHALL use one versioned preprocessing implementation on
decoded oriented uint8 RGB pixels, with explicit scaling/mean/std, layout and
geometry. Unsupported input arrays MUST be rejected instead of guessed or
silently rescaled. Implements AC-1/AC-4.

#### Scenario: Known RGB fixture is prepared by both consumers
- **GIVEN** known RGB values and declared normalization for square and non-square fixtures
- **WHEN** producer and consumer prepare their model tensors
- **THEN** their tensors match the independent expected float32 channel/normalization/layout values
- **AND** both retain exact original sizes and geometry metadata

#### Scenario: Unsupported channel depth or ordering is supplied
- **WHEN** input is not the declared uint8 RGB HWC array
- **THEN** preprocessing rejects it rather than swapping channels or assuming a scale

### Requirement: Original-coordinate reconstruction and explicit decision
The shared geometry policy SHALL restore logits to original coordinates before
class selection. Letterbox removes recorded padding before float-logit resize;
native tiles average overlapping logits with complete pixel coverage and discard
padding. Decisions SHALL use declared argmax or few-layer softmax-threshold rules,
with deterministic canonical tie handling. Implements AC-1/AC-4.

#### Scenario: Letterbox has asymmetric padding
- **GIVEN** an odd-dimension portrait or landscape fixture with known spatial signals
- **WHEN** original-size logits and masks are reconstructed
- **THEN** reconstruction uses the exact recorded resize/padding and returns original dimensions
- **AND** independent coordinate/channel fixtures show no axis, padding or class-ID shift

#### Scenario: Native tiles overlap and meet image edges
- **GIVEN** overlapping tiles over a non-square fixture or an image smaller than a tile
- **WHEN** logits are reconstructed
- **THEN** each original pixel receives the documented mean of its contributing logits
- **AND** padded pixels are excluded and class selection occurs after merging

#### Scenario: Class-ID decision reaches a threshold or tie
- **WHEN** original-size probabilities reach the declared few-layer threshold or an argmax/background-bulk tie
- **THEN** the documented inclusive threshold and lower-ID tie rules determine IDs 0/1/2
- **AND** no interpolated fractional mask IDs or class 255 are emitted

#### Scenario: Reconstruction would exceed its allocation policy
- **WHEN** decoded-image or accumulation dimensions exceed the configured budget
- **THEN** reconstruction rejects them before allocating unbounded tensors

### Requirement: Compatibility does not certify lab performance
Package evaluation SHALL distinguish unmeasured evidence from supplied reported
measurements with provenance/support/definitions. Validation MUST NOT invent
accuracy, perfect absent-class metrics or a calibrated threshold, and MUST NOT
present supplied measurements as independently verified. Implements AC-1.

#### Scenario: Synthetic or custom package is unmeasured
- **WHEN** a compatible package declares unmeasured evaluation with a reason
- **THEN** it can pass technical compatibility while retaining unmeasured evidence
- **AND** no lab usefulness or recall claim is produced

#### Scenario: Reported measurements contradict package settings
- **WHEN** reported identity/checkpoint/preprocessing/decision settings contradict the manifest
- **THEN** validation rejects the inconsistent report with an explicit reason
- **AND** missing support/results cannot become fabricated measurements

### Requirement: Shared contract is independently consumable
The contract library SHALL be installable by the exporter and local consumer
without training/cloud frameworks, and optional model validation MUST NOT become
a default dependency of WI-01 health/startup. Implements AC-1/AC-4.

#### Scenario: Producer and consumer use the packaged library
- **WHEN** the synthetic producer builds a package and a distinct consumer validates/prepares/reconstructs it
- **THEN** their contract and golden-fixture results agree in the documented Python environment
- **AND** the core import has no PyTorch/TensorFlow/cloud initialization

#### Scenario: Local workspace runs without model extras
- **WHEN** WI-01 is installed and started without model-validation extras
- **THEN** account-free health and persistence continue to work

