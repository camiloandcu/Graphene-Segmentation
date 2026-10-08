# Lab export audit report

Checked: 2026-10-08. WI-03 / Spike; INC-01 / F-01; Issue #3.
Question: can the supplied labels support training, and what evaluation independence
can be supported without acquisition metadata?

## Source and coverage

The stakeholder supplied `2D Materials segmentation.v2i.coco-segmentation.zip`.
Its SHA-256 is
`bc362e5e774e63cd62e677522abbf2bc632422cadd7b5e9642bbfa3ca97eede3`.
The export README identifies Roboflow version 2, dated 2025-09-22, and the
[lab project](https://universe.roboflow.com/integrador-i/2d-materials-segmentation-zrowi).
Both the supplied README and COCO license record declare CC BY 4.0. Attribution
must retain the source; the export does not name an individual contributor.
This is evidence from the supplied export, not newly verified account metadata.

The README reports 40 images and no augmentation; its preprocessing section is
blank, so preprocessing details remain unknown. The identical COCO `date_captured`
values match the export timestamp and are not accepted as acquisition timestamps.
Annotation by lab members and absent acquisition metadata are stakeholder-reported;
reviewer identity, annotation history and physical thickness validation are unknown.

All 40 images and all 759 associated annotations were checked. All images decode
to 2560 x 1920. No missing referenced image, orphan annotation, unreferenced image
file, malformed coordinate list, non-finite/out-of-bounds coordinate, zero-area
polygon or empty polygon raster was found within the implemented checks.
This does not certify polygon topology or physical label correctness.

| Supplied split | Images | Polygon annotation records | Few-layer pixels | Bulk pixels | Conflict pixels |
| --- | ---: | ---: | ---: | ---: | ---: |
| Train | 32 | 567 | 617,212 | 31,858,968 | 10,275 |
| Validation | 5 | 123 | 116,012 | 5,864,412 | 70 |
| Test | 3 | 69 | 59,740 | 2,093,164 | 233 |
| Total | 40 | 759 | 792,964 | 39,816,544 | 10,578 |

Pixel counts use original-resolution COCO polygon rasterization, not the source
`area` or bounding-box fields. Annotation records are not verified physical flake
instances; touching regions and multiple polygons complicate instance interpretation.

## Class mapping and label support

The source categories explicitly declare ID 1 `bulk` and ID 2 `few-layer`.
The audit maps names to canonical mask IDs 2 bulk and 1 few-layer. Source numeric
IDs must not be copied directly into canonical masks. The existing legacy converter
would reverse these classes for this export and was not invoked.

ID 0 `monolayer-graphene` is also declared as a parent category, but has zero actual
annotations. Its presence and the generic README wording do not establish monolayer
examples or require assigning it to background. Its meaning would need review if
annotated records appear in another export. The physical few-layer/bulk boundary
remains a question for the lab; named classes alone do not verify thickness.

| Canonical class | Original-resolution pixels | Share of all pixels | Image support |
| --- | ---: | ---: | ---: |
| Background / uncovered region | 155,987,914 | 79.3396% | 40 |
| Few-layer | 792,964 | 0.4033% | 40 |
| Bulk | 39,816,544 | 20.2517% | 40 |
| Ignored conflicting labels | 10,578 | 0.0054% | 10 |

Every image has both bulk and few-layer annotations. There are no fully background
images to establish image-level negative performance. Uncovered pixels are a
rasterization default, not independent proof that all foreground was annotated.
The very small few-layer pixel fraction motivates explicit class support and
original-resolution review. Accuracy dominated by background would be misleading;
training configuration and performance measurement remain outside this spike.

## Conflicting labels and visual review

Bulk and few-layer polygons overlap in 10 of 40 images, covering 10,578 pixels.
The audit marks these pixels 255 ignored, retaining the conflicts for review;
it does not silently choose annotation order as class precedence.

| Audit image ID | Conflicting pixels |
| --- | ---: |
| test-001 | 233 |
| train-002 | 19 |
| train-005 | 417 |
| train-011 | 346 |
| train-014 | 1,438 |
| train-016 | 6,971 |
| train-017 | 979 |
| train-020 | 14 |
| train-028 | 91 |
| valid-001 | 70 |

Agent visual screening inspected all 40 overlays on four contact sheets, all 15
candidate-pair sheets, and five individual overlay images (`test-000`, `test-001`,
`test-002`, `train-016`, `valid-001`). This is screening coverage, not expert lab
review of every polygon. The largest conflict, `train-016`, appears along the
boundary between annotated bulk and few-layer regions. Thin boundary conflicts
are also visible in `valid-001`. The lab should decide correction or justified
ignore handling; the audit masks are evidence, not approved training ground truth.

Visible scale bars/text are retained in images and normally lie in uncovered
regions. Their possible effect on training is unmeasured. Small-region completeness,
flake identity and physical thickness cannot be certified from optical appearance.

## Duplicates, grouping and proposed split

Byte checksums and decoded RGB checksums found zero exact duplicate pairs among
all 780 image pairs. Near-image retrieval used 64-bit dHash (distance <= 12),
64 x 48 grayscale thumbnail correlation (>= 0.90), and filename sample/date cues.
All 15 candidates were retrieved by filename cues; none met the visual similarity
thresholds. Candidate-pair inspection showed differing fields, with physical
overlap and shared acquisition identity unresolved.

There are 31 filename-derived group candidates, not 31 verified independent samples.
Two pairs cross existing split roles:

- `test-001` / `valid-002`: same filename sample/date cue, different fields.
- `test-000` / `train-007`: same filename sample/date cue, different fields.

Thus two of the three supplied test images have candidate group relationships to
development data. This is evidence of possible group leakage, not confirmed pixel
overlap. A negative hash/similarity test does not prove independence.

The proposed manifest retains all original roles and leaves all 40 proposed roles
unassigned. That is a deliberate deferred evaluation assignment, not a usable
training split. Co-group the related fields provisionally; have the lab validate
filename cues and any broader acquisition batches before selecting a grouped
development/evaluation policy. If that cannot be established, report exploratory
within-dataset results with explicit uncertainty and obtain separate data before
making an independent held-out performance claim. No split fraction is invented.

## Recommendation and remaining limits

The export is technically inspectable and has both target classes. It can support
planning a pilot after the lab confirms the class definition, resolves/accepts
overlap handling and reviews annotation completeness. Independent evaluation
readiness is inconclusive with this export. The three-image supplied test is not
accepted as a validated independent benchmark.

The next decisions and their owners are recorded in
[the readiness decision](03_READINESS_DECISION.md). No training, importer,
Figshare audit, label correction, account access or accuracy experiment ran.
