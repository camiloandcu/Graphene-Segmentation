# WI-05 dataset handoff design

Status: explicitly approved by stakeholder on 2026-10-08.

## Architecture and downstream use

Create `packages/graphene-dataset-contract/`, an independently installable Python
library/CLI usable locally and in Colab. Keep NumPy/Pillow/pycocotools/schema
validation dependencies separate from ONNX and the app runtime. Reference the
existing canonical class contract; do not import backend services/cloud clients.
Reuse tested WI-03 validation/rasterization ideas where suitable, but preserve the
read-only audit's behavior and its archived evidence. The legacy Supabase converter
is not part of the new path.

Proposed commands: `graphene-dataset prepare SOURCE.zip --review REVIEW.json
--output NEW_DIR` and `graphene-dataset check DATASET_DIR`. Preparation without a
review may emit a review template and a blocked report; templates contain unresolved
values, not positive attestations. Both commands expose machine-readable reports,
readable remedies and nonzero status for invalid/blocked inputs. The library exposes
validation plus iteration by explicit role over verified original-resolution RGB
images and uint8 masks. No resize, patches, normalization or augmentation here.

A blocked report is diagnostic evidence and has no ready manifest. A ready artifact
is accepted only after consumer validation; directory existence is insufficient.
WI-06 must consume this validator rather than globbing arbitrary image/mask folders.

## Source adapter and bounded validation

Support split-directory `_annotations.coco.json` files and referenced images from
the supplied ZIP. Validate unique IDs within each source split, references,
category definitions, consistent mappings, unique image paths, image decoding,
dimensions, polygon coordinate shape/finite bounds/nonzero raster and all annotations.
Reject RLE/crowd/box-only annotations for this version with a concrete reason.
Reject unknown annotated categories; an unused parent category is retained as source
metadata and never silently mapped to background. Reject missing/orphan records
and unaccounted image files instead of silently skipping them.

Resolve source category names through an explicit reviewed mapping; validate names
against IDs in each annotation file. For the real export source 1 bulk maps to 2,
and source 2 few-layer maps to 1. Preserve category metadata and mapping evidence.
Rasterize same-class unions at original size. Different-class intersections fail
unless the applicable review authorizes ignore; then all conflicts become 255,
regardless of annotation ordering. Background is 0 only when the review accepts
exhaustive annotation for the included image scope. Non-exhaustive images are
excluded in v1 rather than treating unknown uncovered regions as negative examples.
An annotation-free image is eligible only with an explicit verified-background
review. Entirely ignored masks are ineligible.

Proposed default source limits match the verified audit: 2,000 members, 100 MiB
expanded source bytes and 16 million pixels per decoded image. Enforce actual read
budgets as well as declared sizes. Bound annotation files/coordinate lists by
those byte budgets, process one image at a time, and reject unsafe/duplicate paths,
symlinks and unsupported special members. Consumer validation bounds files and
image pixels too. Record conversion/library versions; supported environment
changes require raster reproducibility checks. No source extraction to arbitrary
paths, pickle, executable review data or network access.

## Review record v1

Bind the review to the source ZIP digest and source image IDs/paths. Record review
reference, reviewer identifier and date as user-supplied provenance, with no claim
that the software authenticates expertise. Store private records outside Git.
Dataset-level decisions can cover named image scopes; per-image overrides are
explicit. Reject contradictory, missing, unknown or stale records.

Required decisions for every included image:

- Approved canonical mapping and acknowledged physical-category semantics.
- Annotation origin `human`, evidence reference and human eligibility review.
  `prediction`, `unknown` or missing origin is ineligible; exclusions need reasons.
- Exhaustive annotation/background decision, or verified background-only status.
- Conflict policy `reject` or reviewed `ignore`, with rationale/scope.
- Effective split role and group status/evidence; exclusions retain their reason.
- Evaluation status `exploratory` or `independence-reviewed`, evidence reference
  and explicit remaining limitations. Unknown acquisition facts remain unknown.

Do not infer these statements from stakeholder acceptance of the WI-03 spike.
Label correction means supplying a separately identifiable corrected source export
and review bound to its new checksum, not mutating the accepted source in place.
Do not promote saved predictions through folder names or mask value checks.
Explicit provenance prevents accidental contamination; false user attestations
cannot be ruled out by this local software.

## Splits and leakage

Use stable sample IDs scoped by source split and source image ID, preserving the
WI-03 audit identity where possible. Store original roles independently from
reviewed effective roles. No split seed/fraction or auto-rebalancing is introduced.
Validate exactly one role for each source image, allowing reasoned exclusions.
Require nonempty train and validation sets with reported target class support;
test may be absent and then no test evaluation is available.

Compare exact file and decoded RGB digests. Duplicate images or reviewed groups
cannot span active roles; conflicting duplicate annotations must be resolved or
excluded. Import WI-03 candidate groups through an explicitly supplied evidence
record bound to source identity. For the supplied export, retain its two cross-split
candidates as review blockers. Candidates must be co-grouped/excluded or explicitly
dispositioned with rationale; unrelatedness is not inferred from a weak visual hash.
No generic near-duplicate search or new audit is added to this item.

Exploratory mode can acknowledge absent acquisition metadata and reviewed residual
candidate uncertainty, but cannot override known-group/exact-duplicate isolation.
`independence-reviewed` requires affirmative grouping/evaluation evidence and no
unresolved relevant candidate; the software records that claim and its evidence,
it does not establish physical independence. Preserve all limitations for WI-06/07.

## Artifact contract and consumer verification

Publish a versioned directory with `manifest.json`, `validation.json`,
`images/<sample-id>.<source-extension>` and `masks/<sample-id>.png`. Copy original
image bytes; mask pixels align to their decoded coordinates. Reject orientation
metadata requiring unreviewed geometry changes. Use safe generated filenames and
portable relative paths. Do not include unreferenced predictions or workspace data.

Manifest fields include schema/converter version; source digest/version/license/
attribution and explicit unknowns; ordered classes/ignore semantics; settings;
normalized review/evidence identity; and per-sample source ID/path, original/effective
role, group/candidate disposition, provenance, review reference, dimensions,
source/decoded/image/mask digests, annotation counts and class/ignore pixel support.
Keep original annotation-file digests and source traceability. Aggregate validation
includes exclusions, support, warnings and evaluation limitation status.

Dataset fingerprint hashes canonical semantic manifest content plus referenced
artifact digests, including review decisions/settings, excluding its own digest
and volatile output paths/run timestamps. Split fingerprint hashes stable sample
identity, image content identity, effective roles, exclusions and reviewed grouping.
Canonical ordering/JSON encoding must be specified and tested; source order does
not become accidental split randomness. Changing label pixels changes dataset
identity; changing roles/groups changes both relevant identities.

Consumer validation checks strict schema/version, safe relative paths, complete
file inventory, digests/fingerprints, mask dimensions/dtype/legal values, class support,
review readiness and split/group invariants before yielding samples. Treat copied
artifacts as untrusted input. Reject tampering, symlinks, missing files and artifacts
that claim readiness without complete decisions. Retain report/evidence references
rather than confusing checksums with authenticated human provenance.

## Publication and recovery

Source files are read-only. Require a new output destination and stage beside it;
validate all required artifacts before atomic directory publication on the same
filesystem. No overwrite of prior ready output. Invalid source or review may
publish only a clearly blocked diagnostic report/template, which `check` rejects
as a training artifact. Distinguish invalid source, blocked review and I/O failure.
On interruption, incomplete staging is never a ready dataset. Retrying uses a new
destination; cleanup touches only staging owned by that attempt. Test validation,
write and publication failures with a prior artifact present.

## Verification and limits

Reconcile the real source's 40 images/759 records, class reversal, 10 conflicts and
deferred splits against WI-03. Run without invented lab statements: unresolved
review produces blockers. Two repeated runs compare stable report/fingerprint
fields. Run a ready-path synthetic dataset with actual fixture attestations and
consume every active split. If the lab supplies a real review, additionally prepare
and inspect the real ready artifact; otherwise that evidence remains pending.

Test non-square masks, malformed source/unknown labels, annotation order, empty
and all-ignore masks, background-only review, stale review digest, origin rejection,
source split preservation, cross-role duplicates/groups, candidate dispositions,
fingerprint changes, tampering, resource/path boundaries and publication recovery.
Run strict OpenSpec and relevant package/audit regression checks. No frontend/backend
build is needed unless implementation materially touches those paths.

Trade-offs: narrow polygon support and explicit review improve traceability but
require trainer input. A local review record cannot authenticate biological truth.
No independent performance, real training or release readiness is established by
successful conversion. Real label/split readiness is a downstream human gate.
