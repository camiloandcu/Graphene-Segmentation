# WI-07 implementation and session evidence

Checked: 2026-10-12. Issue [#7](https://github.com/camiloandcu/Graphene-Segmentation/issues/7).
Branch: `feat/wi-07-model-selection`. Planning commit: `b23f65b`. Implementation commit: `8abeb9f` (pushed).
Draft [PR #21](https://github.com/camiloandcu/Graphene-Segmentation/pull/21)
contains `Closes #7` and explicitly records pending real-run acceptance.
Status: implementing; model selection and final test remain unverified.

## Delivered implementation

The separate `graphene-evaluation` package provides checkpoint-bound scoring,
original-coordinate confusion/component metrics, censored unknown detections,
finite threshold sweeps, panels, warmed benchmarks, common-support/group/seed
comparisons and a reviewed freeze gate. Its challenger runner preserves immutable
WI-06 epoch formats while recording its own source/runtime identity and additional
training/resource telemetry. WI-06 source remains unchanged.

SegFormer-B0, frozen DINOv3 ViT-S/16 plus 1x1 head, and DeepLabv3+/ResNet18 adapters
are implemented. DeepLab's newly initialized global-pooling head uses 32-group
GroupNorm instead of BatchNorm to handle the real training role's final singleton
batch. Encoder initialization remains the same approved ImageNet ResNet18.
This implementation detail is recorded rather than silently dropping an image.

Guide: [model selection](../../15_MODEL_SELECTION_EVALUATION.md).
Notebook: [interactive Colab comparison](../../../notebooks/02_COLAB_MODEL_SELECTION.ipynb).
Reviewed source commit for Colab: `8abeb9f2d10762d5420c539748832a5b29d28c16`.
The completed DINO initial run retains that bundle. New runs use persistence-fix
commit `33eb57af378b32ed80a552c44119c4ab7e805ff7`; the notebook pins this newer
bundle. Keep the source corresponding to each recorded run for strict recovery.
Source and synthetic tests: `packages/graphene-evaluation/`.

## Actual access and recovery checks

Through the previously authorized Colab MCP connection:

- The first connected runtime reported Python 3.13.16 and CUDA unavailable.
- Drive mount succeeded. The retained baseline generation exists with
  172,151,774 checkpoint bytes. Streaming SHA-256 exactly reproduced
  `c199f87a1d3f06f013dbef0db7982c6d4e3e2ba852146c1ca57f735ec25e267f`.
  Evaluator validation has now reproduced the retained confusion counts and
  foreground macro Dice exactly. See the [actual aggregate record](03_INITIAL_ADMISSION_AND_BASELINE.json).
- The approved ready-dataset archive exists in the existing Graphene datasets
  directory, named by SHA-256
  `4aa3bc1ad4d29181338901d773d602613fb2bdc6613ea5d18155e28534ebbea7`.
- The stakeholder switched to GPU and confirmed reconnection. The replacement
  runtime reports Python 3.13.15, Torch 2.11.0+cu130 and Tesla T4. It needs the
  pinned package environment and a new Drive mount before real comparison runs.
  Both now succeeded: fresh process Torch 2.7.1+cu126 reports CUDA on Tesla T4.
  Do not interpret Colab's preinstalled Torch as the reviewed training environment.

Pinned Hugging Face metadata checked directly on 2026-10-11:

| Candidate | Revision | Verified access observation |
| --- | --- | --- |
| SegFormer encoder `nvidia/mit-b0` | `80983a413c30d36a39c20203974ae7807835e2b4` | Public repository, PyTorch weights; no safetensor artifact at this revision |
| DINOv3 `facebook/dinov3-vits16-pretrain-lvd1689m` | `114c1379950215c8b35dfcd4e90a5c251dde0d32` | Manual access gate; pinned safetensor HEAD request returned HTTP 401, `GatedRepo`, without credentials |

SegFormer source links its model license to the [author license](https://github.com/NVlabs/SegFormer/blob/master/LICENSE),
which limits use to research/evaluation. Approved research comparison does not
establish commercial deployment rights. Its pinned PyTorch state is loaded with
restricted `weights_only=True` under Torch >=2.6. No arbitrary unpickling or random
pretrained substitution is provided. The stakeholder subsequently reported DINO
access approval and enabled the notebook secret; actual authenticated weight
download/admission remains pending. DINO execution
requires actual approved credentials; no terms were accepted
on the stakeholder's behalf. See [literature gates](01_LITERATURE_AND_CANDIDATES.md)
for 2D-TLK and MaskTerial's distinct compatibility limitations.

## Actual initial measurements

The four-image baseline validation report has exact foreground macro Dice
0.913150140598536 and few-layer pixel recall 0.8238106591584569. At argmax,
5/15 annotated few-layer semantic components match at the reviewed IoU proxy;
71 unmatched prediction components touch unknown coverage and are indeterminate,
and one unmatched component lies wholly on known support. Unknown coverage is
71.299% of role pixels. Threshold 0.2 raises component matches to 6/15 while
lowering foreground macro Dice to 0.892941 and increasing indeterminate unmatched
components to 129. These are development trade-offs, not a chosen operating point.
Full reports and original-coordinate panels are retained privately on Drive under
`Graphene/trials/wi07-baseline-validation-20261011`. Test is untouched.

SegFormer's real pinned pretrained bytes passed CPU forward/backward admission
on synthetic objective inputs, with 3,714,915 trainable parameters, finite loss
and exactly zero objective gradients at ignored output pixels. The weight-byte
identity is `d9c6889002284c00022a369560a76493e6094fac9aea695cb884640826017a5b`.
T4 admission also passed with the same pinned bytes, finite backward loss and
zero ignored-output gradients: 903,049,728 peak allocated bytes and 1,140,850,688
peak reserved bytes at batch 2/512/float32. The admission uses synthetic inputs
and does not establish real-data accuracy. Initial real seed-42 training started as
`wi07-segformer-b0-seed42-20261011`, retaining complete epochs under the existing
Drive `Graphene/runs` directory. Completion/quality/recovery remain pending.
An initial cache-write sandbox failure was retried with approved escalation.

## Verification and acceptance status

Synthetic contract cases cover unknown bridges/censoring, hand-counted confusion,
component misses/ties, original-coordinate letterbox/tiling, interrupted replay,
freeze identity and test rejection, common-support comparison and real adapter
forward/backward shapes/frozen DINO gradients. Synthetic runs are not microscopy
quality or pretrained admission evidence.

The initial combined regression run passed 28 cases and skipped the CUDA-only
case, with one DeepLab singleton BatchNorm failure. The decoder correction passed
its focused check; the full evaluator suite subsequently passed all 8 cases.
After adding resource/source records and deterministic evaluation, all 8 evaluator
cases passed again (58.06 seconds). The unchanged WI-06 regression cases passed in
the combined run. Existing pycocotools/NumPy deprecation warnings remain.

`openspec validate --all --strict`: 7 passed, 0 failed. Python syntax, all 8
notebook code cells (no outputs), 75 local links across 8 Markdown files and
`git diff --check` passed. A separate `npx openspec`
attempt could not write npm's global cache; the installed project CLI was used
successfully. No specification has been synced or archived as completed.

| Criterion | Status | Evidence/remaining work |
| --- | --- | --- |
| AC-1 traceability/isolation | Partially verified | Synthetic identity/freeze tests; actual baseline digest and exact validation-count reproduction verified |
| AC-2 candidates/recovery | Partially verified | Adapter/replay tests, real-weight CPU admission and actual access gates; SegFormer GPU admission verified; challenger runs and actual recovery pending |
| AC-3 supported quality/errors | Implementation verified synthetically | Actual candidate metrics and stakeholder panels pending |
| AC-4 sensitivity/resources | Implemented; real evidence unverified | Benchmarks/comparison tools; finalist geometry/seeds/actual resources pending |
| AC-5 reviewed selection/test | Unverified | Stakeholder shortlist, recommendation and exact freeze or explicit deferral pending; test untouched |

## Continuation

On 2026-10-12, the stakeholder reported the runtime had ended after eight hours
and reconnected a replacement T4 runtime. Python 3.13.15 and the new Drive mount
were observed. Drive contains 30 SegFormer completion markers and its completed
summary; cryptographic generation verification and selected-checkpoint evaluation
in the replacement runtime remain pending. Do not infer quality or successful
recovery from marker counts alone. The stakeholder also reported DINO access
approval and enabled the Colab `HF_TOKEN` secret. Before interruption, secret
retrieval and pinned repository metadata succeeded without exposing credentials;
authenticated weight download and real-weight admission remain pending.
The local MCP bridge stopped after an invalid command-file request. Its private
client now catches invalid files without terminating. A restarted stable endpoint
did not receive a browser connection despite stakeholder confirmation; a fresh
endpoint/link was prepared. Runtime installation/recovery workers are ready in
private workspace storage but have not executed. Reconnect before claiming any
replacement-session checkpoint or DINO admission result.

The fresh endpoint subsequently connected and installed source `8abeb9f` with
the pinned packages successfully. Actual replacement-runtime recovery **failed**:
all 30 SegFormer epoch directories contain the three JSON members but lack
`checkpoint.pt`, both on Drive and after local copy. Strict inspection rejected
the missing members. The original U-Net checkpoint remains present. The
stakeholder confirmed no checkpoint move/deletion. The persistence-loss cause is
unknown; do not use SegFormer history alone as checkpoint-bound selection evidence.
Its history names epoch 19 with Dice 0.9305392399304415, but that score has not been
reproduced from weights. A new, identically configured seed-42 run is prepared
under `wi07-segformer-b0-seed42-20261012-rerun`; stronger independent retention
and replacement-session verification remain required.

DINO admission has not launched: `userdata.get('HF_TOKEN')` timed out through MCP.
A first notebook cell requested the secret from a manual UI execution without
printing or persisting its value. That step succeeded, and actual pretrained T4
admission subsequently passed. See [the complete admission record](04_DINOV3_GPU_ADMISSION.json):
21,597,699 total parameters, 1,155 trainable head parameters, finite loss,
zero ignored-output gradients, frozen encoder, 186,051,072 allocated and
195,035,136 reserved peak CUDA bytes. Weight digest:
`643110675d072f171af2af5a5228d0453e00ca476b3066ffa13e8215721faf39`.
Pinned author configuration and adapter configuration have no substantive
differences. This remains a synthetic-input feasibility check, not accuracy.
Initial training `wi07-dinov3-vits16-linear-seed42-20261012` completed all 30
epochs. Its history selects epoch 20 with foreground macro Dice
0.5514027542991692; a separate checkpoint-bound development report and archive
are being produced. All 30 checkpoint files are present in the current Drive
mount. Actual error analysis and replacement-mount/session durability remain pending.

Separate evaluation completed and exactly reproduced selected DINO Dice
0.5514027542991692. Argmax few-layer recall is 0.12351417708479315; annotated
component matches are 0/15, with eight unknown-intersecting unmatched predictions
and zero wholly known-support unmatched predictions. Private report/panels are
under `trials/wi07-dinov3-validation-20261012`. The selected/latest archive is
161,134,926 bytes with SHA-256
`80927f63525182578bad075763d7fd9ff2864b6855ff2ed309e91bd3c97e4264`.
The archive was checked through the current mount, but remount verification has
not succeeded. A synchronous Drive flush exceeded MCP timeouts and was interrupted
by the stakeholder; kernel responsiveness was restored. Drive logs contain many
quota-related entries, but specific storage-error classification remains pending.
The stakeholder reports storage is nearly exhausted and proposes migration to
another account with more space. Preserve the local `/content` archive and summary
before releasing this runtime: folder copies cannot recover unsynced weights.
SegFormer replacement and DeepLab admission/run have **not** started. Next runner
is installed separately at `/content/wi07-next-site`; DINO remains on `8abeb9f`.

DINO resource sidecars exposed a persistence bottleneck: epochs 24–26 spent
95–102 seconds persisting after approximately four seconds optimizing/validating,
with the GPU idle during hashing. The next source bundle changes only challenger
persistence to full inspection at session entry and incremental verified copies
of new epochs; WI-06 storage/source remains unchanged. Completion-last markers,
collision rejection and full checksum-first recovery remain mandatory. Four
focused synthetic cases passed (32.68 seconds): uninterrupted versus resumed
state/RNG/generator equality, interrupted-copy authority, rejection of a corrupted
old acknowledgement in a new session, and the existing exact experiment replay.
These fixtures do not prove remote Drive durability or explain the missing weights.
The active DINO run remains on `8abeb9f`; do not update its installed bundle while
it is running or use the newer source for its strict recovery.

The T4 environment and Drive mount are verified; actual baseline counts reproduce
exactly. Pinned source `8abeb9f` remains the immutable training bundle. Finish
the initial SegFormer run and run admitted challengers sequentially, preserve durable run records and verify
replacement-session recovery. Then obtain stakeholder shortlist priorities,
execute approved finalist screens/seeds and record a reviewed selection or
inconclusive outcome. No WI-08 proposal or model export is authorized by this
implementation. Keep this change active until the real acceptance gates are met.
