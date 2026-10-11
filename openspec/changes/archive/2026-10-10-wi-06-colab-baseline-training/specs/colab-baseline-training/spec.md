## ADDED Requirements

### Requirement: Validated reviewed dataset consumption
The trainer SHALL validate the complete WI-05 dataset before initialization and
consume only explicit train/validation roles for optimization/development scoring.
It SHALL preserve canonical 0/1/2 labels, ignore 255, effective assignments,
dataset/split fingerprints, provenance and evaluation limitations. Both foreground
classes and reviewed background SHALL have positive supervised target support in
both train and validation roles. Dense v1 and explicit partial v2 SHALL be accepted
only through their respective validated contracts. Partial v2 SHALL preserve a
supervision fingerprint and keep unannotated pixels 255 except reviewed anchors.
This requirement traces to WI-06-AC-1.

#### Scenario: Ready artifact supplies the development run
- **WHEN** a reviewed artifact satisfies the dataset and training support contracts
- **THEN** the trainer consumes verified train/validation samples with unchanged role identities and records both fingerprints and limitations
- **AND** test/excluded samples do not enter gradients, scoring or checkpoint selection

#### Scenario: Blocked, changed or unsupported artifact
- **WHEN** the dataset is diagnostic, partial, tampered, has invalid labels, or lacks required train/validation foreground support
- **THEN** the trainer stops with an actionable reason before model initialization or output mutation
- **AND** it does not repair assignments or accept arbitrary image/mask folders

#### Scenario: Partial artifact lacks reviewed background anchors
- **WHEN** source foreground labels are valid but unannotated regions are unknown and no reviewed background supervision exists in train or validation
- **THEN** three-class training is blocked with the missing support/evidence identified
- **AND** absence of polygons or model feedback is never automatically promoted to background

### Requirement: Reproducible pretrained three-class baseline
The trainer SHALL use an ImageNet-pretrained U-Net/ResNet-18 with three RGB inputs
and three finite logit channels, explicit recorded normalization/letterbox
geometry, ignored mask padding, paired train-only transforms and ignore-aware
CE plus foreground soft Dice. It SHALL record actual pretrained-weight identity,
resolved configuration, source revision, seeds, environment, optimization history,
elapsed time and measured GPU resources or unavailable reasons.
This requirement traces to WI-06-AC-2.

#### Scenario: Baseline optimization
- **WHEN** a valid run begins with the declared pretrained weights and configuration
- **THEN** optimization produces finite three-channel logits and loss with ignored pixels excluded from both loss terms
- **AND** paired mask transforms preserve legal IDs and disclose foreground lost by resize
- **AND** run artifacts identify actual initialization, dependencies, settings and resources

#### Scenario: Pretrained initialization or optimization fails
- **WHEN** weights are unavailable or mismatched, a transformed sample has no valid targets, or optimization produces nonfinite values or exceeds memory
- **THEN** the trainer reports the failure without silently substituting random weights or changing configuration
- **AND** any previous complete checkpoint remains usable

### Requirement: Recoverable completed-epoch state
The trainer SHALL publish verified immutable completed-epoch checkpoint generations
with model, optimizer, scheduler, applicable AMP, RNG/data-order state, next epoch,
history and best identity. It SHALL restore through restricted tensor/state loading
and enforce data/configuration/environment compatibility before continuation.
Changed partial supervision/anchor identity SHALL prevent continuation even when
source images and split roles are unchanged. Incomplete/corrupt generations SHALL
NOT replace complete state. Recovery SHALL
repeat incomplete epochs from the last completed boundary.
This requirement traces to WI-06-AC-3.

#### Scenario: Resume a complete generation
- **WHEN** the trainer loads a complete compatible checkpoint in a recreated supported environment
- **THEN** it restores all continuation state before generating the next training order
- **AND** the next completed epoch extends the saved history and preserves best-checkpoint identity unless a better development score is observed

#### Scenario: Interrupted checkpoint or persistence write
- **WHEN** a checkpoint generation or durable copy fails before verified completion
- **THEN** it is not eligible for resume or last/best selection
- **AND** the prior verified generation remains intact and the trainer reports the persistence failure

#### Scenario: Corruption or incompatible continuation
- **WHEN** checkpoint checksums/state/schema, dataset/split, resolved settings, source revision, dependency versions or device/precision policy are incompatible
- **THEN** resume fails before modifying the run
- **AND** it never falls back to unrestricted pickle loading or silently starts a new run

### Requirement: Original-coordinate development checkpoint selection
The trainer SHALL restore validation logits to original image coordinates, use
canonical argmax, and accumulate a three-class confusion matrix excluding ignored
and unknown pixels. It SHALL report defined per-class Dice/IoU/precision/recall and support;
zero denominators SHALL be unavailable, not perfect. Best selection SHALL maximize
foreground macro Dice over target-supported classes with earlier-epoch exact ties.
The selected handoff SHALL bind epoch, score, checksum, config and dataset/split
identity and distinguish last from best. This traces to WI-06-AC-4.

#### Scenario: Prediction occurs in an unannotated region
- **WHEN** a partial dataset marks the original target pixel unknown 255
- **THEN** the prediction is excluded from metric success and failure counts
- **AND** reports retain supervised support, unknown fraction and fixed supervision identity without claiming full-image quality

#### Scenario: Best epoch is not the last epoch
- **WHEN** an earlier epoch has a larger finite validation foreground macro Dice than the final epoch
- **THEN** the handoff identifies and loads the earlier winning checkpoint
- **AND** history reconciles its score, epoch and checksum without test-set involvement

#### Scenario: Tie or unsupported metric denominator
- **WHEN** two epoch scores are exactly equal or a reported metric denominator is zero
- **THEN** selection retains the earlier winner and the unsupported metric carries an unavailable reason
- **AND** absent-class cases never receive fabricated perfect scores

### Requirement: Interactive Colab execution and durable recovery evidence
The notebook SHALL call reusable training modules in a documented installation,
validation, training, persistence, recovery and inspection sequence. It SHALL
require an explicit persistence choice and verified complete generations outside
transient runtime storage before claiming recoverability. WI-06 acceptance SHALL
include actual multiple-epoch training on genuinely reviewed lab data, fresh-runtime
resume and reconciled selected-checkpoint evidence with recorded resources and
limitations. Synthetic/local smoke runs SHALL NOT satisfy this real-run requirement.
This traces to WI-06-AC-5.

#### Scenario: Trainer recovers after Colab runtime replacement
- **WHEN** the trainer retains a verified generation outside the original VM and follows the guide in a new supported runtime
- **THEN** optimization resumes from the saved completed epoch and produces an inspectable selected-checkpoint handoff
- **AND** executed notebook/run evidence records real dataset identity, persistence verification, environment and resumed history

#### Scenario: Real data or execution is unavailable
- **WHEN** genuine dataset readiness, permitted interactive access or actual fresh-runtime execution is missing
- **THEN** the verification record marks real-run acceptance unverified and identifies the missing input
- **AND** passing software tests do not mark WI-06 complete or certify lab performance
