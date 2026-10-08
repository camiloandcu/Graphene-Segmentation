# Decisions and work item hierarchy

Status: WI-01 through WI-04 merged; WI-03 and WI-04 stakeholder accepted on
2026-10-08. WI-05 software is implemented and technically verified; PR #19 open; stakeholder item acceptance/merge pending.
Later items remain provisional. Apply the hierarchy **delivery increment -> feature -> executable
work item -> implementation task**. Epics are optional and are omitted because
they would duplicate the delivery increments in this project.

The former seven phases were delivery groupings, not atomic executable items.
Identifiers below are stable parent/dependency references. The stakeholder asked
to continue with WI-01 and explicitly approved its single proposal.
WI-01 and WI-02 are implemented, technically verified and merged. WI-03's approved
audit is technically verified and stakeholder accepted. WI-04 is implemented,
merged and stakeholder accepted. WI-05 is implemented below; later candidates
remain provisional.

## Decision log

| Decision | Status | Consequence |
| --- | --- | --- |
| Prioritize finding few-layer flakes | Confirmed by stakeholder | Primary evaluation is few-layer detection recall; false detections are measured alongside it. |
| Initial deployment on lab computer | Confirmed | CPU inference required; cloud hosting deferred. |
| Linux / 16 GB RAM / RTX 3090; 40+ images per batch | Stakeholder-provided planning assumption | Bounded batch queue; optional GPU execution and configurable limits for stronger machines. |
| Free-tier Colab training/validation | Confirmed | Small models, checkpoint/resume, bounded candidate comparison. |
| Use MCP for dataset account access | Confirmed | Roboflow plugin discovery returned no match; its public project page returned 403. Request a dataset export or explicitly agree another route before account access. |
| Rank images by predicted few-layer coverage; batch upload | Confirmed | Coverage percentage determines ranking; flake recall remains a separate quality metric. |
| Local persistence; no mandatory accounts/cloud | Confirmed | SQLite/files replace the mandatory Supabase runtime; bind to loopback initially. |
| Colab-only training | Confirmed | Replace the in-app trainer with a guided Colab handoff. |
| English interface | Confirmed | User-facing copy, code, and files use English. |
| Acquisition metadata absent; lab members supplied labels | Confirmed | Audit duplicates/overlap; do not claim known independent sample groups. |
| Annotation completeness / physical label validation | Unverified | Stakeholder sees no obvious unlabeled areas; inspect masks and seek lab clarification for ambiguous labels. |
| WI-03 export audit | Technically verified; stakeholder accepted 2026-10-08 | 40 images, 759 polygon records, reversed source class IDs, 10 conflicting-label images; conditional pilot readiness and inconclusive independent evaluation. See the audit report. |
| Thick_Graphene equivalence to lab bulk | Proposed, requires label review | External-data mapping cannot silently assume equivalent thickness definitions. |
| ONNX package for app inference | WI-02 v1 contract approved | Small CPU runtime; package validation replaces framework guessing. |
| U-Net baseline / compact SegFormer challenger | Recommended, awaiting approval | Model selection follows measured lab performance, not a SOTA claim. |
| Frozen small DINOv3 segmentation probe | Optional, access/resource gated | Recent limited-label transfer candidate; include only after license/access, export, and runtime feasibility checks. |
| Figshare pretraining | Optional, gated by audit/comparison | Include only if it helps held-out lab performance without excessive false detections. |

## Delivery increments and features

### INC-01: usable local screening with a validated lab model

Consumer: lab members locating few-layer graphene and occasional model trainers.
Outcome: run the application locally, inspect and rank image batches, export
traceable predictions, and train/import a replacement model through Colab.

| Feature | Capability | Child work items | Aggregate acceptance |
| --- | --- | --- | --- |
| F-01 | Trustworthy annotated datasets | WI-03, WI-05 | Reviewed labels/splits reach training with provenance preserved; predictions are excluded from ground truth. |
| F-02 | Portable training and measured model selection | WI-06, WI-07, WI-08 | A Colab-trained selected checkpoint has measured lab evaluation and produces matching exported-model predictions. |
| F-03 | Local model management and correct inference | WI-01, WI-02, WI-04, WI-09 | The lab can import/select a compatible model and run identity-consistent predictions without cloud accounts. |
| F-04 | Few-layer screening workspace | WI-10, WI-11, WI-12 | Users inspect masks, rank 40+ images by coverage, recover individual failures, and export aligned results. |
| F-05 | Guided replacement-model workflow | WI-13 | An occasional trainer can validate data, use Colab, and return a compatible model to the app. |

Increment acceptance is the combined feature evidence and the release gates
below. Completing scaffolding, notebooks, or implementation tasks alone does
not establish a working app or a trained, validated model.

### INC-02: optional external-data improvement

Consumer: stakeholder deciding whether extra training data improves lab screening.

| Feature | Capability | Child work items | Aggregate acceptance |
| --- | --- | --- | --- |
| F-06 | Evidence-based use of external graphene data | WI-14 | A controlled comparison supports inclusion or exclusion of Figshare pretraining using held-out lab outcomes. |

INC-02 does not block INC-01. DINOv3 is a gated candidate inside model selection,
not a separate required delivery. Cloud hosting is outside both increments.

## Detailed work items and readiness

WI-01 and WI-02 are merged; their acceptance evidence is recorded separately.
WI-03 has verified audit evidence and a conditional/inconclusive recommendation.
Stakeholder accepted WI-03 and WI-04 on 2026-10-08. Real training remains
dependent on reviewed labels and a reviewed split policy; accepting the audit
does not resolve its remaining label/group questions.

### WI-01 — Enabler: run and persist the local workspace

Parent: INC-01 / F-03. Consumer: lab operator and downstream model-management UI.
Outcome: a local workspace starts without external credentials and retains its
metadata/artifacts across restarts.

Scope: Linux setup, local SQLite/files, loopback startup, dependency/runtime
configuration, and removal of mandatory cloud/auth initialization from this path.
Exclusions: live Supabase migration/deletion, shared-network access, model import
semantics, GPU benchmarking, and unrelated admin-screen repairs.

Dependencies: architecture approval (G-01). Existing frontend build/type-check
non-completion needs diagnosis before a passing baseline can be claimed. If the
cause requires an independent investigation, refine a separate spike before work.
Applicable completion gates: G-01 through G-04.

Proposal: [WI-01 local workspace](../../openspec/changes/archive/2026-10-08-wi-01-local-workspace/proposal.md).
Status: approved and implemented. AC-1 through AC-3 passed; see
[verification evidence](09_WI_01_VERIFICATION.md). Stakeholder acceptance/merge
remain separate from technical verification.

| Criterion | Observable acceptance | Verification evidence |
| --- | --- | --- |
| WI-01-AC-1 | On a clean supported setup without Supabase/JWT credentials or a cloud connection, the documented command starts the local workspace and its health endpoint responds. | Recorded installation/startup smoke run in the supported environment. |
| WI-01-AC-2 | A local metadata/artifact write survives restart; failed writes do not leave a usable record pointing to a missing artifact. | Persistence/recovery integration checks and restart observations. |
| WI-01-AC-3 | Startup binds to loopback by default and logs contain no secrets; the local path does not initialize cloud services. | Configuration and startup-log inspection with external clients disabled. |

WI-01 implementation tasks (completed in its archived OpenSpec change):

- T-01: connect local metadata/files to the startup path (AC-1, AC-2).
- T-02: configure local startup and remove mandatory cloud initialization (AC-1, AC-3).
- T-03: verify installation, restart, and failure behavior; record evidence (AC-1–AC-3).

### WI-02 — Enabler: define and validate the portable model contract

Proposal: [WI-02 portable model contract](../../openspec/changes/archive/2026-10-08-wi-02-portable-model-contract/proposal.md).
Status: explicitly approved and implemented on 2026-10-08. See
[verification evidence](10_WI_02_VERIFICATION.md) for AC-1 through AC-4.
Resource/tensor/geometry decisions implement the approved technical design;
lab calibration is not assumed.

Parent: INC-01 / F-03. Consumers: Colab exporter, inference runtime, and custom-model
authors. Outcome: both producer and consumer agree on class IDs, preprocessing,
geometry, output semantics, and model identity before a model can be used.

Scope: versioned package/manifest schema, canonical pixel classes, shared
preprocessing/geometry policy, compatibility validation, and representative fixtures.
Exclusions: app import UI, full training runs, arbitrary framework runtimes,
and final choice of model architecture.

Dependencies: approval of the ONNX contract (G-01), received. Initial fixtures can
use synthetic images; microscope-specific resize/tiling settings remain subject
to the real-image audit (WI-03). Applicable completion gates: G-01 through G-04.

| Criterion | Observable acceptance | Verification evidence |
| --- | --- | --- |
| WI-02-AC-1 | A compatible package unambiguously declares ordered class IDs, input/output semantics, normalization, geometry settings, identity, and checksum; training and inference resolve them identically. | Schema/contract review and producer/consumer fixture validation. |
| WI-02-AC-2 | Wrong checksums, unsupported schemas, inconsistent class/output counts, and unsafe or oversized archive members are rejected with specific reasons. | Representative invalid-package cases and resource-bound checks. |
| WI-02-AC-3 | A one-channel binary output cannot be accepted as background/few-layer/bulk; class mapping is explicit rather than inferred from numeric score ranges. | Binary-output rejection regression and three-class compatibility check. |
| WI-02-AC-4 | Shared preprocessing and inverse geometry preserve class IDs and original coordinates on square and non-square fixture images. | Paired producer/consumer tensors and original-coordinate mask comparisons. |

Implementation tasks (recorded in the WI-02 OpenSpec change):

- T-01: specify the package, classes, and geometry policy (AC-1, AC-3, AC-4).
- T-02: implement bounded compatibility validation (AC-2, AC-3).
- T-03: establish export/consumer fixtures and record contract evidence (AC-1–AC-4).

### WI-03 — Spike: establish what the lab dataset can support

Proposal: [WI-03 lab dataset audit](../../openspec/changes/archive/2026-10-08-wi-03-lab-dataset-audit/proposal.md).
Status: proposal explicitly approved on 2026-10-08; stakeholder supplied the local
export and authorized a 90-minute investigation. AC-1 through AC-3 have technical
evidence; merged via PR #17 and stakeholder accepted on 2026-10-08. See
[WI-03 verification](11_WI_03_VERIFICATION.md) and [audit report](wi03/00_INDEX.md).

Parent: INC-01 / F-01. Consumers: model trainer and stakeholder.
Question: are the supplied masks/taxonomy suitable for training, and what
evaluation independence can be supported without acquisition metadata?

Scope: the supplied lab export, class/geometry/provenance checks, visual label
review, duplicates/overlap, class support, and a recommended split policy.
Exclusions: new annotation campaigns, production importer implementation,
Figshare inspection, and training/architecture search.

Execution inputs resolved: stakeholder supplied the COCO Segmentation version-2
ZIP and approved a 90-minute limit. The export is stored under ignored
`.workspace/wi03/source/`. Physical few-layer/bulk definitions, conflicting-label
handling, annotation completeness and group identity remain downstream lab-review
questions; a documented inconclusive audit answer is valid completion.
Applicable completion gates: G-01 through G-04.

| Criterion | Observable acceptance | Verification evidence |
| --- | --- | --- |
| WI-03-AC-1 | The report identifies actual image/mask counts, class mappings/support, dimensions, missing/invalid labels, provenance, and dataset version/license or marks unknowns explicitly. | Dataset audit manifest, count summaries, and representative label overlays. |
| WI-03-AC-2 | Duplicate/overlap evidence and unavailable acquisition information support a proposed split policy with explicit remaining leakage uncertainty. | Duplicate review, proposed split manifest, and documented exclusions/unknowns. |
| WI-03-AC-3 | The stakeholder receives a supported readiness recommendation or an inconclusive conclusion listing blocking label/data questions and the next step. | Reviewable audit report and decision record; a positive answer is not required. |

Candidate investigation tasks:

- T-01: inspect export contents and labels (AC-1).
- T-02: assess duplicates, overlap, and candidate split support (AC-2).
- T-03: deliver limitations and a readiness recommendation (AC-3).

## WI-04 / US: import and select a compatible local model

Parent: **INC-01 / F-03**. Consumer: lab member or occasional trainer importing
a v1 model ZIP without manually entering ML configuration. Dependencies: merged
WI-01 and WI-02; WI-03 lab acceptance and real training are not prerequisites.

Status: stakeholder explicitly approved proposal/design/specs on 2026-10-08.
Implemented and technically verified on `feat/wi-04-local-model-management`, linked
using `gh issue develop 4`. Reuses Issue #4. See
[verification](12_WI_04_VERIFICATION.md) for acceptance, checks and PR references.
The verified OpenSpec change is synced and archived under
`2026-10-08-wi-04-local-model-management`. PR #18 is merged (checked via `gh`);
stakeholder acceptance confirmed on 2026-10-08. Release remains separate.

Scope delivered: bounded local ZIP import, immutable model registry, readable
metadata/evaluation, explicit durable selection, transactional v1-to-v2 upgrade,
file recovery and UI/API integration. Prediction, training, image/batch upload,
model deletion/editing and cloud registry remain outside this item.

Approved policies: import never auto-selects; identical packages reuse the entry;
same ID with different bundle bytes is rejected; unavailable selected models retain
their identity until explicit selection of an intact alternative.

Numbered Given/When/Then criteria remain authoritative in the archived proposal:
**AC-1** import/inspect exact identity; **AC-2** explicit selection across restart;
**AC-3** failures/concurrency preserve state; **AC-4** transactional upgrade/recovery
and no-extras startup; **AC-5** accessible Models workflow. All five are technically
**passed** with synthetic integration/browser evidence. G-02 approved; G-04 verified;
human acceptance is confirmed; G-05 real trained-model/release gates remain pending.

## WI-05 / Enabler: validated labeled datasets for the trainer

Parent: INC-01 / F-01. Consumer: occasional trainer and WI-06 Colab loader.
Outcome: a validated canonical dataset with reviewed annotation provenance and
explicit split identity, or an actionable blocked report when readiness is unresolved.
Dependencies: merged WI-02 and accepted WI-03; WI-04 is not a prerequisite.

Status: stakeholder explicitly approved the proposal/design/specs on 2026-10-08. The single
[proposal](../../openspec/changes/archive/2026-10-08-wi-05-validated-labeled-datasets/proposal.md),
[design](../../openspec/changes/archive/2026-10-08-wi-05-validated-labeled-datasets/design.md),
[specification](../../openspec/changes/archive/2026-10-08-wi-05-validated-labeled-datasets/specs/validated-labeled-datasets/spec.md)
and [tasks](../../openspec/changes/archive/2026-10-08-wi-05-validated-labeled-datasets/tasks.md) are archived after software verification.
Issue #5 is reused; branch `feat/wi-05-validated-labeled-datasets` is linked with
`gh issue develop 5`. See [verification](13_WI_05_VERIFICATION.md): AC-1–5
software behavior passes; genuine real ready handoff remains unverified pending
lab review. [PR #19](https://github.com/camiloandcu/Graphene-Segmentation/pull/19) is open with `Closes #5`;
implementation commit `b17453f` is pushed. Stakeholder item acceptance/merge remain separate.

Scope delivered: offline COCO polygon validation/conversion, versioned review and dataset
contracts, split/group/provenance gates, reproducible artifacts and consumer checks.
Exclude UI/cloud, annotation editing, pseudo-labeling, training and new split ratios.
Approved policies: reviewed eligibility required; reject conflicts unless reviewed
ignore is authorized; preserve source roles and require explicit effective roles;
exclude predictions/unknown origins; retain exploratory evaluation limitations.

Acceptance criteria in the proposal are authoritative: AC-1 canonical real-source
validation; AC-2 traceability/reproducibility; AC-3 reviewed split isolation;
AC-4 human annotation eligibility; AC-5 complete offline handoff/recovery.
Verify real-export blockers and synthetic ready-path behavior. A real ready handoff
requires genuine lab decisions, otherwise that evidence remains pending. G-01–G-04
apply; real training/release approval remain separate.

## Later candidates in dependency order

The following is a provisional decomposition, not a queue of approved executable
records. Before promoting a row, detail its scope/exclusions, blocking decisions,
numbered type-specific acceptance criteria, evidence, and applicable gates. Each
promoted item gets its own OpenSpec change when the user starts that work.

| ID / type | Parent | Consumer and independently reviewable outcome | Dependencies | Candidate acceptance evidence |
| --- | --- | --- | --- | --- |
| WI-06 / Enabler | INC-01 / F-02 | Trainer can train/resume the pretrained baseline in Colab and select the best development checkpoint. | WI-05 | Recorded Colab training/resume, configuration/environment, checkpoint-selection evidence; a notebook smoke run alone is insufficient. |
| WI-07 / Spike | INC-01 / F-02 | Stakeholder can select a model/operating setting using few-layer misses, false detections, segmentation quality, and resource measurements. | WI-03, WI-06 | Actual baseline/challenger reports, full supported metrics, error panels, split isolation, uncertainty, and a supported recommendation. Effort limit and numeric acceptance remain to review; DINOv3 is access/resource gated. |
| WI-08 / Enabler | INC-01 / F-02 | Exporter supplies the selected checkpoint as a compatible app model with matching predictions. | WI-02, WI-06; WI-07 for the final selected model | PyTorch/ONNX logit and mask comparisons on representative square/non-square images; package records the evaluated checkpoint and settings. |
| WI-09 / Fix | INC-01 / F-03 | Lab user receives a prediction from the requested model with correct class interpretation and original-image alignment. | WI-02, WI-04; WI-08 for a trained-model check | Regressions for selected-ID/global-model mismatch, concurrent selection changes, geometry, and three-class output. Synthetic packages can verify early behavior; a real exported package verifies integration. |
| WI-10 / US | INC-01 / F-04 | Lab user uploads one image and inspects original, overlay, and mask without ML assistance. | WI-09 | Given ready/no-model/invalid-image/inference-error states, readable actions and correct results; visual and keyboard checks of zoom, opacity, legend, and stale-result behavior. |
| WI-11 / US | INC-01 / F-04 | Lab user prioritizes 40+ images by predicted few-layer coverage and retries failed images without losing completed results. | WI-10 | Given a mixed-success batch, deterministic coverage ranking, incremental progress, bounded memory, and isolated retry preserve result identity. Realistic batch measurements and workflow scenarios. |
| WI-12 / US | INC-01 / F-04 | Lab user exports inspectable masks/overlays and traceable batch summaries. | WI-10, WI-11 | Given completed results, downloads preserve formats/dimensions and raw class IDs, record exact models/settings, and handle large files and escaped user text. Artifact inspection and export regressions. |
| WI-13 / US | INC-01 / F-05 | Occasional trainer follows dataset validation -> Colab -> model import with a new compatible dataset. | WI-04, WI-05, WI-06, WI-08 | Guided workflow trial with valid/invalid datasets and measured/unverified evaluation labels; no in-app GPU trainer or arbitrary-runtime promise. |
| WI-14 / Spike | INC-02 / F-06 | Stakeholder decides whether Figshare pretraining improves held-out lab screening. | WI-03, WI-05, WI-07; source mapping review | Reconciled source counts, reviewed labels/negatives/duplicates, attribution, and matched lab-only/external-pretraining comparison. A supported exclusion is valid completion; effort budget remains to review. |

WI-04 and WI-05 consume different prerequisites; their row order is not an
artificial dependency. Training and app verification can use separate branches
of the dependency graph without requiring parallel agents. Later findings can
revise the provisional decomposition before the affected proposal is prepared.

## Shared completion and release gates

Keep these separate from item acceptance criteria and implementation tasks:

- **G-01 — Planning approval:** the stakeholder reviews the full product/UX/ML/
  architecture set and the affected open decisions. Confirmed scope decisions
  already in the log are preserved. Status: local WI-01 architecture approved;
  broader ML/release decisions remain pending.
- **G-02 — Single-item proposal approval:** after the user starts development,
  prepare exactly one OpenSpec change for the next executable item. Review and
  explicit approval precede implementation and preparation of another change.
  Status: WI-01 proposal approved/completed; WI-02 proposal explicitly approved
  and implemented. WI-03 proposal is explicitly approved and its audit is verified;
  export access and a 90-minute limit were provided. WI-04's single proposal was
  explicitly approved, implemented and technically verified.
  WI-03 and WI-04 stakeholder acceptance is confirmed on 2026-10-08.
  WI-05 proposal/design/specs explicitly approved on 2026-10-08; software
  implemented, verified, specs synced and change archived. Real-data human gate
  and item acceptance remain separate.
- **G-03 — Item acceptance:** record each criterion as passed, failed, or
  unverified with its evidence; required human review is pending until confirmed.
  For US items use Given/When/Then, for fixes preserve reproducer/boundaries,
  for spikes answer the agreed question, and for enablers prove the contract.
- **G-04 — Engineering completion:** relevant regression/integration checks,
  build/type checks where affected, reviewed schema/recovery behavior where
  applicable, updated usage docs, and coherent local commits. After an OpenSpec
  item is implemented and verified, sync specs and archive that completed change.
- **G-05 — INC-01 release readiness:** demonstrate import -> single/batch
  prediction -> inspection -> export with a real trained model; record Colab
  execution/evaluation, 40+ image resource behavior, lab acceptance of recall/
  false detections/ranking, and setup/backup/README handoff. Unexecuted Colab work
  stays unverified; a passing test suite alone does not establish lab usefulness.

Implemented/verified, stakeholder-reviewed, merged, and released are separate
states. Use short-lived local branches and small Conventional Commits after
approval. Work-branch push and a linked PR are authorized for approved items; GitHub uses `gh`.
No protected-branch push/merge/update, live migration, or cloud deployment is
authorized. Dataset account access retains its separately agreed MCP route.

## Traceability from the former delivery map

| Former grouping | Current home |
| --- | --- |
| 1. Resolve scope and obtain lab data | G-01 and WI-03 prerequisites |
| 2. Establish dataset and model contracts | WI-02 and WI-05 |
| 3. Build and verify local inference/model import | F-03: WI-01, WI-04, WI-09 |
| 4. Deliver Colab training and evaluation | F-02: WI-06, WI-07, WI-08 |
| 5. Improve prediction, ranking, and training UX | F-04 and F-05: WI-10 through WI-13 |
| 6. Compare optional external pretraining | INC-02 / F-06 / WI-14 |
| 7. Verify and hand off | G-03, G-04, G-05; verification belongs to every relevant item |

## Release acceptance still requiring stakeholder input

After pilot evaluation, agree minimum few-layer detection recall, acceptable
false detections per image, matching/size criteria, ranking usefulness, and acceptable
prediction latency on the actual lab computer. Do not invent guaranteed performance
from 40 images or claim a completed trained model before evaluation.
