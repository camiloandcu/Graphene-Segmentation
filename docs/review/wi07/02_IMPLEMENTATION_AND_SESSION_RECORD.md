# WI-07 implementation and session evidence

Checked: 2026-10-12. Issue [#7](https://github.com/camiloandcu/Graphene-Segmentation/issues/7).
Branch: `feat/wi-07-model-selection`; draft [PR #21](https://github.com/camiloandcu/Graphene-Segmentation/pull/21), `Closes #7`.
Status: implementing. Initial challenger training/validation is complete;
continued-training recovery, finalist sensitivity and stakeholder selection remain pending.
Test is untouched. The approved OpenSpec change remains active.

## Implementation and immutable source

The separate `graphene-evaluation` package implements checkpoint-bound original-
coordinate scoring, unknown-pixel exclusion, component matching/censoring, finite
threshold sweeps, panels, common-support/group/seed comparison, benchmarks and
stakeholder freeze enforcement. WI-06 source/configuration remains unchanged.
Guide: [model selection](../../15_MODEL_SELECTION_EVALUATION.md).
Notebook: [Colab evaluation](../../../notebooks/02_COLAB_MODEL_SELECTION.ipynb).

| Run/evaluator | Pinned source | Purpose |
| --- | --- | --- |
| Original SegFormer and completed DINO probe | `8abeb9f2d10762d5420c539748832a5b29d28c16` | Original approved evaluator/training bundle |
| SegFormer replacement and DeepLab | `33eb57af378b32ed80a552c44119c4ab7e805ff7` | Incremental verified challenger persistence |
| Corrected benchmarks/new notebook | `9bea06aad3ae97858090c94f8e040a26d3d0564d` | Complete inference timing and separate initialization |

Strict training recovery must use each run's recorded source/runtime. The newer
benchmark evaluator is installed separately; it does not modify active training.
The original DINO model/state can be loaded for inference with unchanged adapters.
Training the same configuration does not imply byte-identical checkpoint files.

DeepLab's newly initialized global-pooling decoder uses 32-group GroupNorm in
place of BatchNorm to retain the final singleton batch. Its approved ResNet18
ImageNet encoder initialization remains unchanged. This is recorded explicitly.

## Actual candidate gates

SegFormer real pinned pretrained CPU and T4 admission passed: 3,714,915 trainable
parameters, finite backward loss, zero ignored-output gradients. Weight digest
`d9c6889002284c00022a369560a76493e6094fac9aea695cb884640826017a5b`;
revision `80983a413c30d36a39c20203974ae7807835e2b4`. Admission peaks:
903,049,728 allocated / 1,140,850,688 reserved CUDA bytes.
Its [author license](https://github.com/NVlabs/SegFormer/blob/master/LICENSE)
permits the approved research comparison; this is not commercial deployment approval.

DINO access was granted to the stakeholder, who enabled `HF_TOKEN` and retrieved
it manually through Colab's UI. No token was printed or persisted. Actual pinned
T4 admission passed: 21,597,699 total / 1,155 trainable parameters, finite loss,
zero ignored-output gradients, frozen encoder. Pinned author/adapter configuration
has no substantive differences. See [admission](04_DINOV3_GPU_ADMISSION.json).
Weight digest `643110675d072f171af2af5a5228d0453e00ca476b3066ffa13e8215721faf39`;
revision `114c1379950215c8b35dfcd4e90a5c251dde0d32`. Peaks:
186,051,072 allocated / 195,035,136 reserved CUDA bytes.

DeepLab real-weight T4 admission passed: 12,329,811 trainable parameters,
641,131,520 allocated peak bytes. See [admission](07_DEEPLAB_GPU_ADMISSION.json).
All admission inputs are synthetic objective fixtures, not accuracy evidence.

2D-TLK was not admitted because usable author licensing, pinned pretrained
identity and partial three-class reproduction remain unestablished. The approved
DeepLab fallback occupies that slot. MaskTerial remains a compatibility assessment:
class-agnostic detection and physical thickness classes do not establish this
visual few/bulk/background semantic contract. See
[literature and gates](01_LITERATURE_AND_CANDIDATES.md).

## Initial real validation

Each challenger completed the common seed-42, 30-epoch protocol. All reports use
the same four validation images, dataset/split/supervision identities and original
coordinates. Unknown pixels are 14,017,959/19,660,800 (71.299%); they do not become
background negatives. Component counts refer to annotated semantic components
at the reviewed IoU proxy, not a census of physical flakes.

| Candidate/checkpoint | Foreground macro Dice | Few-layer pixel recall | Matched components | Unknown-intersecting unmatched | Wholly known-support unmatched |
| --- | ---: | ---: | ---: | ---: | ---: |
| U-Net/ResNet18, epoch 23 | 0.913150 | 0.823811 | 5/15 | 71 | 1 |
| SegFormer-B0, replacement epoch 19 | 0.930539 | 0.868121 | 5/15 | 149 | 13 |
| Frozen DINOv3 probe, epoch 20 | 0.551403 | 0.123514 | 0/15 | 8 | 0 |
| DeepLabv3+/ResNet18, epoch 4 | 0.869623 | 0.754175 | 2/15 | 21 | 0 |

Independent checkpoint-bound evaluation exactly reproduces the selected training
scores. U-Net also reproduces retained confusion counts exactly. Public aggregates:
[baseline](03_INITIAL_ADMISSION_AND_BASELINE.json),
[DINO](05_DINOV3_INITIAL_VALIDATION.json),
[SegFormer](06_SEGFORMER_INITIAL_VALIDATION.json),
[DeepLab](08_DEEPLAB_INITIAL_VALIDATION.json).
Their report fingerprints identify full private reports; extracted summaries
are not themselves those complete reports.

Finite threshold trade-offs include:

- U-Net threshold 0.2: Dice 0.892941, 6/15 component matches, 129 indeterminate
  unmatched predictions.
- SegFormer threshold 0.3: Dice 0.9178, few-layer recall 0.9130, 8/15 matches,
  197 indeterminate and five wholly known-support unmatched predictions.
- DINO threshold 0.2: Dice 0.817734, recall 0.816278, 1/15 matches, seven
  indeterminate unmatched predictions. Its initial probe remains weaker than
  U-Net on these development results; no general claim about DINOv3 follows.
- DeepLab threshold 0.2: Dice 0.8838, recall 0.8160, 3/15 matches, 32
  indeterminate and one wholly known-support unmatched prediction.

These are development trade-offs, not selected operating points. Four images and
one seed do not establish architectural superiority. The stakeholder must review
pilot errors and a Pareto shortlist of at most two before finalist screens/seeds.
Full reports/panels stay privately under Drive `trials`; no test ranking is permitted.

## Storage migration and recovery

The first SegFormer run, `wi07-segformer-b0-seed42-20261011`, completed 30 epochs
but all `checkpoint.pt` files were absent in the replacement runtime despite
surviving histories/markers. Strict recovery failed. The stakeholder confirmed
no move/deletion. Storage was nearly exhausted; specific loss causation is
unproven. Its history alone was never treated as checkpoint-bound quality evidence.

The stakeholder migrated actual files and notebook to another storage account.
The verified data directory is `/content/drive/MyDrive/Graphene (1)`; the sibling
`Graphene` is a regular file. Use this path directly. The approved dataset archive
matches SHA-256 `4aa3bc1ad4d29181338901d773d602613fb2bdc6613ea5d18155e28534ebbea7`
and is 16,411,686 bytes. The DINO selected/latest archive retained exactly
161,134,926 bytes and SHA-256
`80927f63525182578bad075763d7fd9ff2864b6855ff2ed309e91bd3c97e4264`
across account/runtime replacement. Both generations pass checksum verification
and safe state loading. The selected model loads strictly and its complete
report/dataset binding matches. This is actual retention/inference recovery;
the two-generation archive cannot prove contiguous-run continued training.

The replacement SegFormer run, `wi07-segformer-b0-seed42-20261012-rerun`, exactly
reproduces the lost run's best score and epoch. Its selected SHA-256 is
`a3dc42c64f1e13bde09c1c97aabb36fdbced679b2f11309e3e334760a8533831`.
The selected/latest archive is 83,091,065 bytes, SHA-256
`b3d0054594b3efb23208b975800335036d9b97fbc4c5d2d31b9b4a3bc9e0d8d9`.
DeepLab run `wi07-deeplabv3plus-resnet18-seed42-20261012` has selected SHA-256
`da759e0969e9ecfd594956b4a0bb6b1a37a7e427ab851e5f4f54907ec08d98b8`.
Its archive is 274,585,646 bytes, SHA-256
`83e6317723f2823442565ef0ab3547527947e6626219a4c7de3155b0e511bded`.
Both new runs have all 30 checkpoints visible in Drive; their archives pass
current-mount readback hashes. Replacement-runtime continued-training recovery
remains required. Do not infer remote durability from marker counts alone.

A synchronous Drive flush blocked MCP and was interrupted by the stakeholder;
its remount check did not finish. Do not repeat synchronous unbounded flushing.
The stable bridge is connected. Private command files and session/worker details
are maintained in `.workspace/wi07/ledger.json` and `.workspace/wi06/`.

## Resource evidence and feasibility assumptions

The fresh process uses Python 3.13.15, Torch 2.7.1+cu126/CuDNN 90501 and T4;
Colab's preinstalled Torch 2.11 is not the reviewed runtime. The measured CPU is
Intel Xeon @ 2.00 GHz, two logical CPUs, with 13,605,830,656 RAM bytes.
The stakeholder accepts a Colab-equivalent machine with at least 16 GB RAM,
a two-minute target and three-minute ceiling per image. Actual laboratory
hardware equivalence is assumed, not directly verified.

SegFormer actual training peaks: 968,481,792 allocated / 1,193,279,488 reserved
CUDA bytes. Median persistence is 1.048 seconds and median total epoch time
10.015 seconds. The older DINO run spent 95–102 seconds persisting epochs
24–26 after approximately four seconds optimizing/validating. The new runner
fully inspects at session entry, then verifies each newly copied generation with
completion markers last. These observations are not a controlled cross-model
speed comparison or an explanation of the old missing weights.

Benchmark timing initially excluded decoding/decision despite AC-4. The corrected
benchmark includes image read/checksum/decode, normalization, inference,
original-coordinate restoration and the bound decision, with per-phase repeats.
Checkpoint/data verification, construction/state load and device transfer are
measured separately as initialization. Reads use operating-system caches;
plotting is excluded. RSS is cumulative process high-water, not model-exclusive
RAM. Fresh processes run one model/device at a time after training/evaluation
exits. Common protocol: one CPU thread, two warmups and five repeats per image.

All eight fresh-process CPU/T4 benchmarks completed. See
[resource aggregates](09_INITIAL_RESOURCE_BENCHMARKS.json). CPU medians are
2.142 seconds (U-Net), 1.023 (SegFormer), 1.050 (DINO) and 1.085 (DeepLab);
p95 values are all below 2.61 seconds. GPU medians are 0.368/0.413/0.382/0.346
seconds respectively. Initialization, including checkpoint/data verification,
is 31–44 seconds and is reported separately. Every measured process high-water
RSS is below 2.31 GB, within the accepted >=16 GB machine assumption. These
measurements cover the four validation images at 512 letterbox, not every
possible future image or native-tile geometry. DINO argmax panels/full per-image
inputs were restored. The regenerated DINO argmax report exactly reproduces
its selected Dice. The [four-model common-support comparison](10_INITIAL_COMMON_SUPPORT_COMPARISON.json)
verifies full report fingerprints, per-image image/mask/supervised counts and
group identities. Acquisition groups are unverified, so group resampling and
a generalization interval are unavailable. U-Net scores better on two of
four individual images despite SegFormer's higher pooled foreground Dice.

## Verification and acceptance

- Initial evaluator contract suite: all eight cases passed, including the
  corrected DeepLab singleton adapter; unchanged WI-06 cases passed in the
  combined regression run, with the local CUDA-only case skipped.
- Persistence/replay focused checks: four passed (32.68 seconds), including
  exact model/RNG/generator replay, interrupted-copy authority and corrupt prior
  acknowledgement rejection. Synthetic replay does not replace actual recovery.
- Benchmark focused checks: two passed (25.14 seconds), covering phase timing,
  role isolation, threshold binding and rejecting changed bytes in repeated reads.
- `openspec validate --all --strict`: seven passed, zero failed. Python/notebook
  syntax (eight code cells, no outputs), aggregate support and whitespace checks
  passed. Existing pycocotools/NumPy deprecation warnings remain.

| Criterion | Current evidence and remaining work |
| --- | --- |
| AC-1 traceability/isolation | Actual checkpoint/data/support binding and baseline exact counts/panels verified; test remains gated |
| AC-2 candidates/recovery | Real admissions and initial runs verified; DINO retention/model load across replacement verified; actual interrupted challenger continuation pending |
| AC-3 supported quality/errors | Initial checkpoint-bound metrics/panels complete; common-support comparison verified; stakeholder pilot/shortlist approved 2026-10-12 |
| AC-4 sensitivity/resources | Training telemetry measured, all initial CPU/T4 benchmarks verified; four finalist geometry screens complete; matching resources, single declared adjustment and seeds 42/43/44 pending |
| AC-5 reviewed selection/test | Shortlist approved; final recommendation, exact freeze or explicit inconclusive/test-deferral decision pending |

Continue with the approved U-Net/ResNet18 and SegFormer-B0
finalist screens/seeds and genuine replacement-runtime training continuation.
Only after stakeholder checkpoint/settings freeze may the single selection use
the five-image test role; test lacks reviewed background. Sync specifications and
archive only once the actual required outcome is verified. No WI-08 proposal or
model export is authorized by this implementation.

The migrated baseline folder lacked the full-image panels needed for visual
review. A fresh argmax evaluator reproduced its full pixel metrics and component
totals exactly, then restored the four panels to
`trials/wi07-baseline-migrated-argmax-20261012`. All four candidates now have
private original-coordinate pilot panels in the migrated account.
[Initial pilot and shortlist review](11_INITIAL_PILOT_AND_SHORTLIST_REVIEW.md)
records the stakeholder-approved U-Net/ResNet18 and SegFormer-B0 shortlist
(2026-10-12). This approval covers the geometry/seed stage, not final test use.
U-Net leads on two individual images and SegFormer on the other two.
The mean per-image Dice favors U-Net; pooled Dice favors SegFormer.

The private four-image contact sheet was generated and visually inspected. DINO
and DeepLab show broad few-layer predictions including reviewed background
patches. Reviewed-background recall at argmax is 1.0000/0.9834/0.0000/0.6573
for U-Net/SegFormer/DINO/DeepLab, respectively. A zero wholly-known unmatched
component count does not establish zero known pixel errors. Additional regions
on unknown support remain review candidates. The contact sheet is a thumbnail
overview; exact small-component boundaries require full-resolution panels.

The four finalist inference geometry screens completed on the migrated T4.
[Geometry evidence and the single declared training adjustment](13_FINALIST_GEOMETRY_AND_TRAINING_DECISION.md)
record the scale-shift failures, supported small-region misses and next finite
1024-training trials. Matching geometry resources, cache retention and actual
replacement-runtime continuation remain to be verified.
