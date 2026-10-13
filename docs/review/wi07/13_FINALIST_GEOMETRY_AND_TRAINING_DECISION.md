# WI-07 finalist geometry and training adjustment

Checked: 2026-10-12. The stakeholder explicitly approved U-Net/ResNet18 and
SegFormer-B0 after the initial pilot/resource review. This record supports the
approved finite training-adjustment stage; final checkpoint/settings freeze and
test use remain separate review gates.

Four completed inference screens used the exact seed-42 checkpoints, four
validation images, original-coordinate support and eight allowed decisions.
Training remained 512 letterbox throughout these screens. Native tiles use
512 pixels, stride 384 and mean-logit merging. All reports/panels were copied to
Drive and every copied file was verified in the current mount. This does not
prove independent retention after a replacement runtime.

| Model / inference geometry | FG Dice | Few-layer recall | Few-layer precision | Reviewed BG recall | Matches / 15 | Known-support unmatched |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| U-Net / 512 letterbox reference | 0.9132 | 0.8238 | 0.8626 | 1.0000 | 5 | 1 |
| U-Net / 1024 letterbox | 0.8551 | 0.8609 | 0.6436 | 0.5359 | 3 | 15 |
| U-Net / native tiles | 0.7930 | 0.9721 | 0.4683 | 0.000015 | 1 | 154 |
| SegFormer / 512 letterbox reference | 0.9305 | 0.8681 | 0.8766 | 0.9834 | 5 | 13 |
| SegFormer / 1024 letterbox | 0.8649 | 0.8555 | 0.6683 | 0.6229 | 3 | 27 |
| SegFormer / native tiles | 0.5424 | 0.1118 | 0.1655 | 0.9985 | 3 | 237 |

These rows use argmax. The complete finite sweep is retained in
[geometry aggregates](12_FINALIST_GEOMETRY_SCREEN.json). Neither geometry
improved pooled Dice at any of its screened thresholds relative to the original
argmax checkpoint. SegFormer native tiles at threshold 0.2 match 5/15 components
but recover only 0.2019 of supported few-layer pixels. U-Net native tiles cover
many labels but overpredict reviewed background and bulk; high recall alone is
insufficient. Unknown-region predictions remain indeterminate.

The smallest reference components contain 538, 580 and 917 original pixels.
At original 512 inference, U-Net completely misses three other/reference regions
of 4403, 1792 and 917 pixels; SegFormer completely misses regions of 1974 and
917 pixels. Increased inference resolution recovers some coverage but introduces
major known-pixel confusion and does not establish better localization.
The private eight-row contact sheet (`.workspace/wi07/geometry-panels.jpg`)
was inspected: U-Net tiles cover reviewed background with few-layer predictions,
whereas SegFormer tiles miss known few-layer interiors. Thumbnail review does
not establish fine boundaries; the original-coordinate reports/panels remain
authoritative. Changing only inference resolution therefore cannot justify a
deployment change.
The inference scale shift also does not establish the quality of a model trained
at the new resolution.

One declared training adjustment per finalist will test **1024 letterbox training
and matched 1024 letterbox inference**, starting from the same pinned pretrained
initialization and seed 42. Only input size changes: batch 2, float32, 30 epochs,
AdamW 0.001/0.0001, cosine schedule, masked CE + foreground Dice and no added
augmentation stay fixed. This addresses the demonstrated small-region misses
while removing the train/inference scale mismatch. It is a hypothesis, not an
assumed improvement. Real pretrained forward/backward memory admission precedes
each trial; an admission failure is recorded rather than silently changing batch,
precision, learning rate or architecture.

Preserve the original 512 trial and the single 1024 adjustment trial. Review their
supported errors and resources, freeze each finalist's training configuration,
then run seeds 42/43/44 without mixing configurations. A completed seed-42 run
may contribute only to the matching frozen configuration. No second adjustment
or further geometry search is included. [Matching CPU/T4 geometry benchmarks](14_FINALIST_GEOMETRY_RESOURCES.json)
completed before adjustment training: CPU median / p95 is U-Net 1024
9.20 / 11.87 s, U-Net tiles 70.44 / 71.81 s, SegFormer 1024 6.26 / 6.72 s
and SegFormer tiles 28.49 / 28.80 s. T4 medians are 0.47 / 1.00 / 0.56 / 1.79 s
respectively. All measured settings fit the accepted time/RAM assumptions.
Initialization is measured separately and OS-cached reads are not cold-disk
latency. Private checkpoint-bound logits are retained; all 128 cached decisions
reproduced the exact per-image supervised confusion before training began.

The SegFormer adjustment trial will intentionally pause after epoch 5 with its
original 30-epoch schedule. Its complete contiguous state and resume archive will
be verified before requesting a replacement runtime. Actual continuation at epoch
6 in the replacement runtime is still required; an archive/model load alone is
insufficient. The final test remains untouched.
