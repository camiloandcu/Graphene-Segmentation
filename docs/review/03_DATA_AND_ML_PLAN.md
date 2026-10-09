# Data evidence and ML plan

Checked: 2026-10-07. No training experiment has been run.

Update 2026-10-08: [WI-03](wi03/00_INDEX.md) inspected the stakeholder-supplied
version-2 lab export. Its verified counts, class mapping, conflicts and split
limitations supersede the historical lab-export unknowns below. Broader training
recommendations remain planning decisions; no experiment has been run.

Update 2026-10-09: the stakeholder-supplied v3 export supersedes v2 for training.
See [v3 evidence](wi06/01_DATASET_V3_REVIEW.md): same 40 image bytes, 621 polygons,
39 remapped IDs, six conflict images/1,792 ignored pixels and approved grouped
31/4/5 assignments. The old source ZIP was deleted with authorization; historical
WI-03 results remain historical. Relative refinement does not establish exhaustive
coverage; the stakeholder explicitly keeps that uncertainty.

Confirmed policy for the revised WI-06 design: retain eligible labeled foreground,
ignore overlaps and treat every other unannotated pixel as unknown. Supervised
background needs reviewed regions or material-free controls, not absent polygons.
Extend the dataset contract with an explicit partial-v2 mode, preserving dense-v1
compatibility and binding anchors/supervision to fingerprints. No such ready v2
handoff or reviewed background anchors currently exists. The 40 current masks are
analysis previews only; real training stays blocked pending those inputs and
the full revised proposal approval.

Use masked development metrics with fixed supervised support and unknown coverage;
do not infer whole-image accuracy, full false detections or complete flake recall.
This proposed approach follows the partial-label principle of keeping unannotated
pixels unknown, as illustrated by
[ScribbleSup](https://openaccess.thecvf.com/content_cvpr_2016/html/Lin_ScribbleSup_Scribble-Supervised_Convolutional_CVPR_2016_paper.html)
(primary source checked 2026-10-08); its benchmark performance does not establish
graphene suitability. Automated propagation/pseudo-labeling is outside WI-06.

Requested future human-in-the-loop review records regional class opinions tied
to exact predictions. A correct/incorrect/unsure vote does not approve boundaries,
become pixel ground truth or initiate training. Curate evidence separately, keep
disagreements/revisions and isolate frozen test groups. See the UX/architecture
brief and provisional WI-15; no second OpenSpec proposal is prepared.

## Verified sources and remaining unknowns

| Source | Verified evidence | Unknown / implication |
| --- | --- | --- |
| [Lab Roboflow project](https://universe.roboflow.com/integrador-i/2d-materials-segmentation-zrowi) | Stakeholder states 40 images, bulk/few-layer; public [workspace listing](https://universe.roboflow.com/integrador-i) also reports 40 semantic-segmentation images. | Direct project access returned HTTP 403. Export version, license, masks, preprocessing, augmentation, label IDs, acquisition groups, and annotation completeness remain unverified. |
| [Figshare metadata API](https://api.figshare.com/v2/articles/11881053) | Version 2; CC BY 4.0; `DL_2DMaterials.zip`, file 21930396, 2,113,233,250 bytes. | Dataset attribution is required; visual label suitability still needs review. |
| [Figshare archive](https://doi.org/10.6084/m9.figshare.11881053.v2) | Byte-range inspection of graphene COCO JSONs found 773 train images / 3,719 instances and 196 validation images / 1,093 instances, all recorded as 2040 x 1086. | 969 image records differs from the stakeholder's stated 959. Reconcile actual files and duplicate records before use. |

Graphene categories in the inspected JSON files: ID 1 `Mono_Graphene`, ID 2
`Few_Graphene`, ID 3 `Thick_Graphene`. Annotations contain COCO segmentation,
bounding boxes, areas, and `iscrowd`. The ensemble dataset also declares BN,
MoS2, and WTe2 classes. This confirms segmentation labels exist; it does not
confirm exhaustive labeling or that other materials coexist in any particular image.

The stakeholder confirms that acquisition metadata is absent and lab members
provided the labels. Duplicate/overlap review is therefore essential, and sample
independence cannot be established merely from the image count. Roboflow plugin
discovery returned no matching integration; a user-provided export or another
explicitly agreed access route is needed before inspecting the lab masks.

The [authors' repository](https://github.com/tdmms/tdmms_DL) documents the original
Mask R-CNN work and links the [paper](https://www.nature.com/articles/s41699-020-0137-z).
Reusing annotated data is distinct from restoring that legacy TensorFlow runtime.

## Dataset contract and audit

- Canonical pixel IDs: 0 background, 1 few-layer, 2 bulk; 255 reserved for ignored pixels.
- Map by explicit category names and reviewed aliases, never by guessed source IDs.
- Merge mono/few graphene into few-layer. `Thick_Graphene` to bulk is proposed,
  subject to lab confirmation of the thickness boundary and source compatibility.
- Require real pixel masks/polygons; bounding boxes alone are insufficient.
- Record human annotation, reviewed annotation, and model prediction separately.
  Predictions are not ground truth; optional pseudo-labeling must be explicit.
- Validate image/mask dimensions, legal class values, empty/background images,
  missing files, overlapping incompatible labels, per-class pixel/flake support,
  identical/near-identical images, and inherited augmentations.
- Store a dataset manifest with original image ID, acquisition/sample group when
  available, source, split, annotation provenance, checksums, and mapping.
- Split original acquisition groups before patches/augmentation. Preserve existing
  train/validation/test roles unless a reviewed leakage correction requires replacement.

## Proposed model comparison

Start with an ImageNet-pretrained U-Net using a compact encoder such as ResNet-18
as a reproducible baseline. Compare a compact pretrained SegFormer B0/B1 under
the same splits, preprocessing policy, and evaluation. These are candidates;
neither is claimed to be the best model for these images before measurement.

To incorporate recent representation-learning advances, add a bounded optional
probe of a frozen DINOv3 ViT-S/16 encoder with a small trainable segmentation head.
The [official implementation](https://github.com/facebookresearch/dinov3)
lists a 21M-parameter small model and semantic segmentation probing code. This
is a recent candidate suited to testing limited-label transfer; suitability for
graphene, small-flake boundaries, Colab memory, ONNX export, and lab CPU latency
remains unmeasured. Its pretrained weights require approved access and license
review. Do not let that dependency block the accessible baseline/SegFormer path.
Run sequentially and shortlist before cross-validation rather than funding a
large architecture search. Generic benchmark leadership is not lab validation.

[SMP documentation](https://segmentation-models-pytorch.readthedocs.io/en/latest/quickstart.html)
describes pretrained encoders and their required preprocessing.
[SegFormer documentation](https://huggingface.co/docs/transformers/model_doc/segformer)
describes its semantic-segmentation model and image processing.

Avoid choosing a large foundation model solely because it leads a general
benchmark. Selection depends on few-layer detection, false detections, mask
quality, training cost, and CPU inference on the lab's hardware.

## Colab training design

- A documented notebook calls reusable training/data/evaluation modules.
- Training environment is versioned separately from inference dependencies.
- Use transfer learning, AdamW, a scheduled learning rate, small batches,
  mixed precision where supported, and resume checkpoints outside transient storage.
- Use cross-entropy plus Dice as an initial loss; tune class weights or a
  recall-focused loss on development data only if the baseline warrants it.
- Start with 512-pixel inputs/patches as a measured configuration, not an assumed
  optimum. Preserve small flakes through reviewed crops and overlapping inference
  tiles when whole-image downsampling loses useful detail.
- Geometric transforms preserve masks; image color/illumination changes are modest
  and validated because optical contrast carries thickness information.
- Record seeds, dataset fingerprint, split manifest, pretrained weights, package
  versions, config, training curves, measured GPU memory, and elapsed time.
- Select and save the best validation checkpoint, not merely the final epoch.
- Start with one development split; use grouped cross-validation for shortlisted
  candidates if the acquisition groups and free-tier budget permit. Do not invent
  independent groups if no grouping metadata exists.

[Colab resources](https://research.google.com/colaboratory/faq.html) are variable
and not guaranteed. Notebook execution remains interactive; the lab app does not
use a free Colab runtime as its production web server or remotely driven trainer.

## Evaluation and operating settings

Primary: few-layer flake detection recall, with explicit matching criteria and
annotation support. Human instance annotations are preferable; connected
components of semantic labels are an approximation and cannot resolve touching
flakes reliably. Report missed-flake examples and false detections per image.

Also report few-layer pixel recall/precision, per-class IoU and Dice, foreground
macro averages, a full confusion matrix including background, ranking agreement,
and original-resolution visual error panels. Compute metrics from accumulated
counts; do not award perfect scores to classes absent from both target and prediction.

Tune few-layer sensitivity on development predictions; report the recall/precision
trade-off. Keep the final lab test untouched until model/settings are frozen.
Use image/group-level uncertainty estimates where sample support permits; report
the small sample size and exclusions. If an independent test is too small to
support a reliable claim, state that rather than presenting folds as an independent test.

No numeric release threshold is agreed. The stakeholder must approve minimum
few-layer recall and an acceptable false-detection burden after seeing pilot errors.

## Optional external-data experiment

Compare lab-only transfer learning with Figshare pretraining followed by lab
fine-tuning, using identical held-out lab evaluation. Do not pool external images
into the lab test. Review other-material regions: confidently annotated non-target
regions can be useful negatives; ambiguous/unlabeled regions may need ignore masks.
Prevent overlap/duplicate leakage across sources. Include external pretraining
only if measured lab performance and false detections support it.

## Export and handoff

Export an ONNX inference model plus a versioned manifest, evaluation report, and
checksum in one package. Keep a separate restricted-load training checkpoint for
resume/fine-tuning. Verify PyTorch/ONNX logit agreement and matching class masks
on representative images, including non-square inputs and boundary cases.
The package records normalization, class/color mapping, tile/resize policy,
output layout, operating settings, dataset/split fingerprints, and model identity.
