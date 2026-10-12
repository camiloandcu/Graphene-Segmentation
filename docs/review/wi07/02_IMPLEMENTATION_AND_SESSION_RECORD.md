# WI-07 implementation and session evidence

Checked: 2026-10-11. Issue [#7](https://github.com/camiloandcu/Graphene-Segmentation/issues/7).
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
pretrained substitution is provided. The stakeholder submitted the DINO access request and will report approval;
keep this candidate pending rather than declaring exclusion. DINO execution
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

The T4 environment and Drive mount are verified; actual baseline counts reproduce
exactly. Pinned source `8abeb9f` remains the immutable training bundle. Finish
the initial SegFormer run and run admitted challengers sequentially, preserve durable run records and verify
replacement-session recovery. Then obtain stakeholder shortlist priorities,
execute approved finalist screens/seeds and record a reviewed selection or
inconclusive outcome. No WI-08 proposal or model export is authorized by this
implementation. Keep this change active until the real acceptance gates are met.
