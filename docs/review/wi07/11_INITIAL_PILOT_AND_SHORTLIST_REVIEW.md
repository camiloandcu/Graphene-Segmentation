# WI-07 initial pilot and finalist review

Checked: 2026-10-12. Decision consumer: stakeholder choosing at most two finalists for the already approved geometry/seed stage. Status: initial pilot verified; stakeholder approved U-Net/ResNet18 + SegFormer-B0 on 2026-10-12. Final test is untouched.

Approved finalists: **U-Net/ResNet18 + SegFormer-B0** for the next stage. U-Net retains stronger results on two of four individual images and fewer known-support unmatched components. SegFormer improves pooled few-layer recall and offers a useful sensitivity setting. Both comfortably fit the accepted compute assumptions. This is a shortlist recommendation, not a final checkpoint or release choice.

| Initial seed-42 checkpoint | Pooled FG Dice | Few-layer recall | Component matches | Known-support unmatched | CPU median / p95 | T4 median | CPU process peak RSS |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| unet-resnet18, epoch 23 | 0.9132 | 0.8238 | 5/15 | 1 | 2.14 / 2.61 s | 0.37 s | 1.25 GB |
| segformer-b0, epoch 19 | 0.9305 | 0.8681 | 5/15 | 13 | 1.02 / 1.40 s | 0.41 s | 1.85 GB |
| dinov3-vits16-linear, epoch 20 | 0.5514 | 0.1235 | 0/15 | 0 | 1.05 / 1.56 s | 0.38 s | 1.94 GB |
| deeplabv3plus-resnet18, epoch 4 | 0.8696 | 0.7542 | 2/15 | 0 | 1.08 / 1.61 s | 0.35 s | 1.04 GB |

Metrics use exactly the same four validation images and supervised pixels. Unknown coverage is 71.299%; unmatched predictions touching unknown regions are indeterminate (U-Net 71, SegFormer 149, DINO 8, DeepLab 21 at argmax). Component matching is an annotated semantic IoU proxy, not physical-flake counting. Counts above must not be extrapolated to all unlabelled regions.

The benchmark includes image read/checksum/decode through original-coordinate decision at 512 letterbox, one CPU thread, two warmups and five repeats per image, fresh process per model/device. Initialization including checkpoint/data verification takes 31–44 seconds separately. RSS is cumulative process high-water. All measured settings fit the stakeholder's Colab-equivalent >=16 GB assumption, 120-second target and 180-second ceiling. Actual lab equivalence and other image sizes remain unmeasured.

Per-image foreground Dice makes the pooling trade-off visible:

| Validation order | U-Net | SegFormer | DINO probe | DeepLab |
| --- | ---: | ---: | ---: | ---: |
| 1 | 0.9876 | 0.7616 | 0.6594 | 0.6358 |
| 2 | 0.9263 | 0.9636 | 0.4708 | 0.9204 |
| 3 | 0.7991 | 0.8264 | 0.6219 | 0.6209 |
| 4 | 0.9230 | 0.6074 | 0.5476 | 0.6049 |

The simple mean across image-level scores is unet-resnet18: 0.9090, segformer-b0: 0.7897, dinov3-vits16-linear: 0.5749, deeplabv3plus-resnet18: 0.6955. This describes the four images; it is a different aggregation from pooled pixel counts. No verified acquisition groups are available, so no group bootstrap or generalization interval is claimed. One seed per candidate does not measure seed variation.

SegFormer threshold **0.3** gives few-layer recall **0.9130**, Dice **0.9178**, **8/15** component matches, **5** wholly known-support unmatched and **197** indeterminate unmatched predictions. U-Net threshold 0.2 matches 6/15 with Dice 0.8929. These finite development settings explain why retaining both models is useful. Threshold-specific timings will be measured if such a setting is chosen.

DeepLab has zero wholly-known unmatched components and lower measured memory, but lower pixel precision/recall and fewer component matches. The zero component count does not establish absence of pixel errors: broad unmatched regions intersecting unknown support are censored as components even when they contain known pixel mistakes. It is not declared strictly dominated. DINO evidence applies only to this frozen encoder plus linear head; it does not rule out other DINO adaptations. Its initial settings do not offer a persuasive recall/quality benefit here.

Known-support pixel metrics give that distinction context:

| Candidate | Few-layer pixel precision | Recall on reviewed background patches |
| --- | ---: | ---: |
| U-Net | 0.8626 | 1.0000 |
| SegFormer | 0.8766 | 0.9834 |
| DINO probe | 0.1969 | 0.0000 |
| DeepLab | 0.7519 | 0.6573 |

Visual review of all four images shows broad few-layer regions for the DINO probe and DeepLab that overlap reviewed background patches. U-Net and SegFormer mark additional regions on gray/unknown support; those regions remain review candidates, not confirmed mistakes. The thumbnail overview cannot establish small-component boundaries; inspect full panels and the supported metrics for that task.

Private visual evidence is retained on Drive under `Graphene (1)/trials`: `wi07-baseline-migrated-argmax-20261012`, `wi07-segformer-rerun-validation-20261012`, `wi07-dino-migrated-argmax-20261012`, and `wi07-deeplab-validation-20261012`. Review all four original-coordinate panels; gray means unknown. The local private contact sheet is `.workspace/wi07/initial-pilot-panels.jpg` (a thumbnail overview, not small-component boundary evidence).

Following the explicit shortlist approval on 2026-10-12, run the approved 1024-letterbox/native-512-tile screens, assess at most one justified training adjustment per finalist, freeze each configuration and run seeds 42/43/44. Actual interrupted challenger continuation across runtimes is still required. Final checkpoint/settings freeze or explicit inconclusive/test deferral comes afterward; this review does not authorize test predictions.

Evidence: [validation comparison](10_INITIAL_COMMON_SUPPORT_COMPARISON.json), [resource measurements](09_INITIAL_RESOURCE_BENCHMARKS.json), [full acceptance/session record](02_IMPLEMENTATION_AND_SESSION_RECORD.md).
