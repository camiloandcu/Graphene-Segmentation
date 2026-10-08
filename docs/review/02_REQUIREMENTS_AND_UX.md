# Requirements and UX brief

## Primary task: find few-layer graphene

Surface mode: Operate. Preserve useful existing interface foundations and focus
composition on the microscopy image, legible labels, and reliable interaction.
This is a functional interface improvement; a separate visual brand is not required.

Proposed flow:

1. Open **Predict** and see the selected, validated model and its readiness.
2. Upload one image or a batch. See supported formats and actionable validation errors.
3. Choose **Find few-layer graphene**. Show progress and allow recovery from individual failures.
4. Review a sortable image list with thumbnails ranked by predicted few-layer
   coverage (few-layer pixels / eligible image pixels).
5. Inspect an image using original, overlay, and class-mask views, with zoom/pan,
   an opacity control, class visibility controls, and a persistent text legend.
6. Export original images, integer class masks, overlays, and a CSV/JSON summary
   recording the exact model and prediction settings.

Default class labels: **Few-layer graphene**, **Bulk graphene**, **Background**.
Use both text and color to explain results. Keep background transparent in the
overlay; do not darken the entire original image. Preserve original coordinates.

Few-layer sensitivity is a validated model setting. Prefer a readable operating
mode such as **Find more candidates** over exposing arbitrary technical thresholds.
Show its measured recall/false-detection trade-off in model details. Confidence,
when present, must not be described as guaranteed probability of correctness.

Coverage means percentage of eligible image pixels, not physical area. Physical
measurements require calibration. Separate touching flakes may not be separable
from semantic masks; any connected-region count must be labeled accordingly.

## Secondary task: train a replacement model

Proposed flow: open **Train a model**, read the label requirements, validate/export
an annotated dataset, open the Colab notebook, train/evaluate, download the model
package, import it into **Models**, review measured results, then select it.

Most users should never need to choose an encoder, edit JSON, or interpret a
confusion matrix to make a prediction. Keep advanced options in the training and
model detail views. Training runs in Colab; an in-app training server is outside
the proposed release scope. The interface is English.

## Acceptance criteria

- Prediction works on the agreed lab computer and never requires a training GPU.
- Single-image and batch uploads return the exact selected model ID and settings.
- Batches of at least 40 typical lab images are processed incrementally without
  exceeding the planned 16 GB system RAM; measure with actual image dimensions.
- Failed images remain identifiable and can be retried without losing completed results.
- Ranked results use the stakeholder-approved measure; ties are deterministic.
- Overlay and exported masks align with the decoded original image dimensions.
- Results clear or become visibly stale when their input/model/settings change.
- Unsupported models are rejected with a readable explanation before becoming usable.
- Empty, loading, success, invalid-file, no-model, and failed-inference states have
  clear next actions; buttons cannot launch invalid or duplicate work.
- Keyboard navigation, visible focus, dialog focus management, accessible control
  names, contrast, and smaller-screen layout are checked on critical flows.
- Downloads contain a raw class-ID PNG and reproducible metadata, preserve original
  file formats, escape user text, and handle ordinary large microscopy images.
- Basic users can complete upload, inspection, and export without opening ML settings.

## Scope boundaries

Core release: reliable prediction, batch prioritization, model-package import,
Colab training/evaluation, dataset validation, focused UX, and regression checks.

Optional: Figshare pretraining comparison and new-dataset conveniences that reuse
the core pipeline. Deferred: cloud provisioning, arbitrary model runtimes, a large
annotation editor, automated retraining, and distributed training infrastructure.

Replace the mandatory account/admin flow with a local workspace. Existing cloud
data is not deleted or migrated without an agreed data-preservation procedure.
