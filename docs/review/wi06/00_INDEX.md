# WI-06 training-data review

Checked: 2026-10-10. Consumer: lab trainer and stakeholder reviewing WI-06.

1. [Dataset v3 review](01_DATASET_V3_REVIEW.md): verified source replacement,
   remapped identities, grouped assignments, partial-label preview and blockers.
2. [WI-06 proposal](../../../openspec/changes/archive/2026-10-10-wi-06-colab-baseline-training/proposal.md):
   one revised training work item, explicitly approved on 2026-10-09.
3. [Human review UX](../02_REQUIREMENTS_AND_UX.md#human-review-of-predicted-regions):
   requested future app workflow; no new OpenSpec proposal or UI implementation.

Private source, audit panels, comparison records and partial-mask previews are
under `.workspace/wi06/`. Historical WI-03/WI-05 evidence describes dataset v2;
it must not be used as current v3 sample identity or a ready training handoff.

4. [Software verification](../14_WI_06_VERIFICATION.md): implemented partial contract,
   pretrained smoke, resume checks and real Colab acceptance evidence.

5. [Synthetic CPU smoke record](02_CPU_SMOKE_RECORD.json): actual pretrained weights,
   epoch metrics and new-process CLI recovery; no lab/Colab performance claim.

6. [Label confirmation/background review](03_LABEL_CONFIRMATION_AND_BACKGROUND_REVIEW.md):
   lab-human visual labels accepted for the exploratory baseline (subjective 7/10),
   ready partial handoff with eight reviewed background interiors, real GPU setup and
   30 retained epochs and verified replacement-runtime recovery.

7. [Real Colab trial record](04_COLAB_REAL_TRIAL_RECORD.json): 30 actual GPU epochs,
   verified Drive retention, replacement-runtime recovery and reconciled selection.

8. [Training curves](05_COLAB_TRAINING_CURVES.png): masked training loss and
   supervised validation Dice; runtime replaced after epoch 2.
