# WI-03 readiness decision

Checked: 2026-10-08. Consumers: stakeholder and model trainer.
Status: supported audit recommendation delivered; stakeholder acceptance pending.

## Recommendation

Treat the export as technically usable for pilot planning, conditional on label
review. Treat independent evaluation readiness as inconclusive. Do not promote
the supplied three-image test split to an independent benchmark.

Evidence: 40 decodable images, 759 polygon records, both target classes in every
image, explicit name mapping, 10 overlapping-class images, 0 exact duplicate
pairs, and 2 filename-derived group candidates crossing split roles. Few-layer
support is 0.4033% of all pixels. No background-only image is supplied.

## Next decisions

| Decision / evidence needed | Owner | Downstream effect |
| --- | --- | --- |
| Confirm that source `few-layer` and `bulk` definitions match the lab's intended physical categories. | Lab / stakeholder | Approve canonical mapping semantics; numeric source IDs are already known to be reversed. |
| Inspect conflicting polygons, especially `train-016`, and decide correction or explicit ignore policy. | Lab annotator / stakeholder | Produce reviewed labels for WI-05; audit conflict masks are not automatically approved ground truth. |
| Review whether uncovered regions are exhaustively annotated; decide how to obtain verified negative images. | Lab annotator / stakeholder | Define usable background evidence and later false-positive evaluation support. |
| Confirm whether filename sample/date cues denote shared specimens or acquisition batches, including the two cross-split pairs. | Lab / stakeholder | Establish group constraints or accept exploratory evaluation limitations. |
| Approve a grouped split policy after those decisions, or obtain separate evaluation data. | Stakeholder / trainer | Freeze a defensible development/evaluation manifest before training comparison. |

The proposed manifest holds evaluation assignment pending those decisions and
preserves all original split roles. No new split percentages, deadline, performance
threshold, training architecture or acquisition identity are approved by this audit.

## Acceptance evidence

| Criterion | Technical status | Evidence |
| --- | --- | --- |
| WI-03-AC-1 | Passed | Actual source identity/license/version, all-file inventory, name mapping, class support, structural checks, conflicts and representative overlays; unknown provenance/preprocessing/physical validation are explicit. |
| WI-03-AC-2 | Passed | All-pair exact checks, 15 reviewed grouping candidates, two cross-split pairs, deferred proposed manifest and explicit leakage limitations. |
| WI-03-AC-3 | Passed for deliverable | This supported conditional/inconclusive recommendation and concrete owner/next-step table. Stakeholder acceptance remains pending. |

Passing this spike means the uncertainty was investigated and documented. It does
not mean the dataset is certified, training is approved, or model quality is known.
No later OpenSpec proposal is authorized by completion of this item.
