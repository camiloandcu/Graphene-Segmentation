# WI-03 verification evidence

Checked: 2026-10-08. Issue #3; branch `feat/wi-03-lab-dataset-audit`.
Proposal approval, source ZIP relocation and a 90-minute investigation limit were
explicitly authorized by the stakeholder. Technical delivery is verified. Stakeholder accepted WI-03 on 2026-10-08;
PR #17 is merged. Remaining real-label/split decisions and release are separate.
The handoff paragraph below records the original submission state.

Handoff: [PR #17](https://github.com/camiloandcu/Graphene-Segmentation/pull/17) is
open with `Closes #3`; GitHub confirms that association. Implementation commit:
`d2223bb`. The preceding `27f4c9a` contains the separately approved project context
map. The specification is synced at `openspec/specs/lab-dataset-audit/spec.md` and
the verified change archived at
`openspec/changes/archive/2026-10-08-wi-03-lab-dataset-audit/`.

## Result and evidence

The supplied version-2 COCO polygon export contains 40 images at 2560 x 1920 and
759 annotations. Both target classes appear in every image, with few-layer pixels
covering 0.4033% of the total. Source category IDs require explicit name mapping.
There are 10 overlapping-class images and two cross-split filename group cues.
No exact duplicate was found. Independent acquisition/evaluation remains unknown.

- [Audit report](wi03/01_AUDIT_REPORT.md): source identity/license, counts, overlays,
  label conflicts, visual-review coverage and leakage limitations.
- [Reproduction](wi03/02_REPRODUCTION.md): pinned environment, commands, checks.
- [Decision record](wi03/03_READINESS_DECISION.md): conditional pilot recommendation,
  inconclusive independent evaluation, lab owners and next actions.
- [Measured summary](wi03/04_AUDIT_SUMMARY.json),
  [pair review](wi03/05_DUPLICATE_REVIEW.json),
  [proposed manifest](wi03/06_PROPOSED_SPLIT.json) and
  [evidence fingerprints](wi03/07_EVIDENCE_MANIFEST.json).

Raw images, masks, overlays and source-path manifests remain under ignored
`.workspace/wi03/`. No dataset account or cloud storage was accessed.

## Acceptance status

| Criterion | Technical status | Evidence / boundary |
| --- | --- | --- |
| WI-03-AC-1 | Passed | All-file inventory, 40 decoded images, 759 structurally checked polygons, canonical mapping, pixel/image support, version/license, label conflicts and explicit provenance unknowns; 40 contact-sheet overlays and five individual overlays screened. |
| WI-03-AC-2 | Passed | All 780 image-pair exact checks; 15 candidate-pair sheets screened, two cross-split group cues; original roles preserved with proposed assignment deferred and independence uncertainty explicit. |
| WI-03-AC-3 | Passed for deliverable | Supported conditional/inconclusive readiness recommendation with blocking questions and next-step owners. Stakeholder accepted the audit on 2026-10-08; downstream lab decisions remain. |

The audit's inconclusive evaluation finding is valid spike evidence. It is not a
failed requirement to train a model, and no trained-model claim is made.

## Checks run

- Two complete real-export audit runs. Inventory, metadata, candidate pairs,
  proposed manifest, 40 masks, 40 overlays, four contact sheets and 15 pair sheets
  reproduced byte-for-byte. Common summary fields agree.
- `.workspace/wi03/venv/bin/python -m pytest scripts/tests/test_lab_dataset_audit.py -q`:
  20 passed. Source ID reversal, conflicting label order, unknown classes,
  polygon/geometry errors, archive boundaries, missing/unlabeled images, orphan
  annotations, different-byte decoded duplicates and unchanged input are covered.
- Strict OpenSpec validation and whitespace checks passed; local evidence
  fingerprints and documentation links were verified.

An upstream pycocotools/NumPy array-interface deprecation warning is present;
actual runs and focused checks succeeded. No app runtime or UI changed, so app
tests/build were not needed for this standalone audit path.

## Remaining human decisions

Lab review must confirm physical class definitions, overlap correction/ignore
handling, annotation completeness and filename-derived grouping. The supplied
test split is not accepted as an independent benchmark. The proposed assignment
remains unassigned until the split policy is reviewed; it is evidence for a
decision, not a training-ready split. No label files or source roles were changed.
