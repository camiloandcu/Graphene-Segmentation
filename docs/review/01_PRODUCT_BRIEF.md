# Product brief

## Problem and audience

Microscopy lab members need to locate few-layer graphene in optical microscope
images and prioritize images for inspection. Most users do not know ML terminology.
Some users may prepare new labeled datasets and train replacement models.

The stakeholder identifies missed few-layer flakes as unacceptable. Finding as many
few-layer flakes as possible and finding the images with the most few-layer material
are the primary outcomes. A numeric acceptance threshold has not been agreed.

## Confirmed constraints

- Initial application deployment: a lab computer.
- Training and validation: Google Colab with a free-tier GPU.
- Target material labels: few-layer and bulk, with substrate/background as a third pixel class.
- Monolayer is included in the lab's few-layer definition.
- Cloud deployment is a future proposal, not an approved deployment task.
- Persistence is local-first without mandatory accounts or cloud services.
- Training in Colab is sufficient; training inside the web app is not required.
- Interface language: English.
- Batch ranking: largest fraction of the image covered by predicted few-layer.
- Planning hardware assumption supplied by stakeholder: Linux, 16 GB RAM,
  RTX 3090; allow stronger hardware. Batches are roughly 40 images or more.
- Prefer an available MCP for external account access. No relevant Roboflow,
  Supabase, or Colab account connector is exposed in this session.

## Proposed value and proof

The value assumption is that a batch ranked by predicted few-layer content, with
inspectable overlays, helps lab members choose promising images with less manual
screening while retaining the flakes they care about.

Measure few-layer flake detection recall on independent, human-labeled lab images;
report false detections alongside it. Pixel recall and overlap measure segmentation
quality but do not by themselves establish that individual flakes are being found.
Validate batch ranking against human assessment on lab images. Observe whether a
lab member can upload, inspect, and export a result without ML assistance.

The app supports microscopy screening. Its masks represent model predictions;
optical appearance alone does not establish independently measured layer thickness.

## Release shape

Prediction is the default workspace. Model management and a guided Colab training
workflow are secondary destinations. Detailed evaluation is available to users who
need it. Existing framework and interface foundations can be reused where sound.

The stakeholder reports that the lab images lack metadata and were labeled by
lab members; no obviously unlabeled areas were noticed by the stakeholder.
Acquisition independence and physical label validation are not established.

Pending inputs: dataset export and actual image dimensions; physical definition
of the thickness boundary; numeric performance acceptance
after pilot error review. Duplicate/overlap auditing substitutes for missing
group metadata where evidence supports it; residual uncertainty remains explicit.
