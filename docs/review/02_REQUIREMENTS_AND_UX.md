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

## Human review of predicted regions

Requested on 2026-10-09; proposed scope addition, not implemented. Consumer:
lab users inspecting a prediction, then the trainer curating feedback. Surface
mode: Operate; preserve the existing microscopy inspection workflow. The value
assumption is that regional judgments expose useful errors and candidates without
requiring users to draw trustworthy pixel-precise masks.

Flow: open a completed prediction, select a predicted region, inspect the original
with surrounding context and toggle its overlay, choose **Correct**, **Incorrect**
or **Unsure**, then save. Explain the question as whether the region contains the
predicted material; accepting it does not approve every mask pixel or its boundary.
For **Incorrect**, allow an optional suggested class/reason without forcing a
guess. **Unsure** is a valid outcome. Keep confidence separate from the user's
judgment. Original/overlay zoom remains the focal interaction; ML configuration
is not part of the voting task.

Store the original image and prediction unchanged. Feedback retains exact image,
model/settings, result, region geometry/digest, decision, reviewer identifier and
revision/date. A local reviewer label identifies who supplied an opinion without
introducing mandatory cloud accounts; it does not authenticate expertise.
Revisiting/correcting a vote produces a traceable revision. Multiple users can
disagree; show disagreement rather than silently taking a majority as ground truth.

Observable acceptance for a future executable item:

- Given a completed current result, a lab user can inspect region/context and save
  a correct/incorrect/unsure judgment that survives restart with exact identity.
- Given competing opinions or an edited vote, every prior decision remains
  inspectable and disagreement/revision is explicit.
- Given a changed prediction/model or removed result, feedback is marked stale or
  unavailable and never silently attached to a different region.
- Given a saving/error/loading state, communicate progress and recovery; retries
  do not duplicate feedback. Empty queues and unreviewable results have readable
  next actions; no ready model routes the user to Models.
- Keyboard focus, named controls and text alongside color allow the task without
  relying on color or precision pointing. Region selection can use an accessible
  list as well as the image overlay.
- Feedback export retains provenance and its status as a regional opinion. A
  curator must separately approve any dataset promotion; no automatic retraining,
  pixel-mask creation, test leakage or model selection occurs on a vote.

Dependency: saved inspectable predictions from WI-09/10. Keep the new candidate
separate from WI-06 training; this brief does not expand its implementation into UI.

## Core acceptance criteria

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
