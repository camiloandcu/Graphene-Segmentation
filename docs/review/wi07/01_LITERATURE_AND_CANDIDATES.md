# Literature and candidate evidence for WI-07

Checked: 2026-10-11. Decision: which methods merit measured comparison for
background/few-layer/bulk semantic masks in local optical-microscopy screening?
This targeted scan informs engineering selection; it is not a systematic review
or proof of a universal state-of-the-art winner.

## Search and evidence limits

Searched current web indices for graphene/2D-material optical segmentation,
U-Net/Mask R-CNN/transformer comparisons, 2025–2026 methods, materials SAM and
microscopy foundation models. Representative queries included `graphene optical
microscopy segmentation deep learning 2025 2026`, `two dimensional materials
optical microscopy segmentation SegFormer SAM`, `MaskTerial`, `2D-TLK code`,
and `Segment Anything for Microscopy`. Included primary papers and author
repositories; followed domain-paper citations to earlier comparators. Deduplicated
by DOI/arXiv identifier. No private account, new dataset or model weights accessed.

**Verified** below means the source was opened and supports the stated method or
author-reported result; experiments were not independently reproduced.
**Inference** is our assessment of relevance. **Unknown** marks access or execution
details that the source inspection did not establish. Cross-paper Dice, mIoU,
AP and speed values are not comparable leaderboards: modality, labels, splits,
hardware and supervision differ.

## Compact primary-source index

| ID / year / stable identifier | Verified method and setting | Relevance and limits for our decision |
| --- | --- | --- |
| P01 / 2020 / DOI 10.1038/s41699-020-0137-z | [Masubuchi et al.](https://www.nature.com/articles/s41699-020-0137-z): Mask R-CNN for optical images of graphene, hBN, MoS2 and WTe2; author code/data/weights linked. | Direct domain precedent for instance detection. Their physical thickness categories and much larger training collection differ from our visual few/bulk classes. Our incomplete instance coverage prevents treating missing objects as negatives. |
| P02 / 2021 preprint / arXiv 2103.13495 | [MLA-GDCC](https://arxiv.org/abs/2103.13495): modified U-Net with color correction for monolayer/bilayer graphene detection. | Supports testing imaging/contrast handling rather than architecture alone. Calibration and physical-class equivalence in our lab are unknown; avoid unreviewed color correction. |
| P03 / 2024 / DOI 10.1038/s41598-024-79386-z | [Leger et al.](https://pmc.ncbi.nlm.nih.gov/articles/PMC11560962/): compares SegNet, 1D U-Net and 2D U-Net, including color-based preprocessing for optical layer identification. | Direct evidence that preprocessing and label construction matter. Their layer targets do not establish our three-class performance or justify automatic relabeling. |
| P04 / 2025 / DOI 10.1039/D5DD00156K | [MaskTerial](https://pmc.ncbi.nlm.nih.gov/articles/PMC12598537/): synthetic-pretrained Mask2Former detector plus optical-contrast classification; eight datasets/five materials and few-shot experiments. Authors report merging nearby flakes and missing very small flakes. | Strong domain-specific candidate to assess. Detector is class agnostic; published thickness classifiers are not our visual few/bulk model. Synthetic pretraining is reusable evidence, not permission to generate new lab labels or external-data experiments. |
| P05 / 2025 / DOI 10.1016/j.commatsci.2025.114106 | [Author-institution record](https://investigadores.uta.cl/en/publications/a-lightweight-model-and-multi-agent-system-for-layer-identificati/) describes FastViT + LRASPP/KNet (2D-TLK), trained on 134 MoS2 images, with graphene/WS2 adaptation. [Author repository](https://github.com/zhouruiliangxian/2D-TLK) contains MMSegmentation code and graphene configs. | Promising compact semantic comparator. Full publisher text returned 403; protocol detail, upstream licensing, pretrained identity and working reproduction remain unknown. Treat abstract results as author claims. Agent-system features are irrelevant to this task. |
| P06 / 2025 / DOI 10.1038/s41524-025-01870-5 | [Graphene-grid study](https://www.nature.com/articles/s41524-025-01870-5) compares seven models on SEM defects and selects U-Net for its study. | Counterexample to assuming newer models always win. SEM rupture/contamination is a different modality/task; it cannot rank our optical thickness categories. |
| P07 / 2026 / DOI 10.32664/icobits.v1.109 | [YOLO11-seg proceeding](https://icobits.ubhinus.ac.id/index.php/ICoBITS/article/view/109): 1,775 optical graphene images, four layer classes, three runs; reports recall 0.67 and mAP50 0.71. | A relevant instance-model lead, not demonstrated superiority. Exhaustive objects, compatible labels and review of the complete evaluation protocol would be needed before our comparison. |
| P08 / 2024 preprint / arXiv 2401.05638 | [MatSAM](https://arxiv.org/html/2401.05638v2): structure-aware SAM prompts on 16 optical/SEM materials-microstructure datasets; [author code](https://github.com/USTB-AI3DVIP/matsam) linked. | Useful boundary/annotation inspiration. Grains/phases and class-agnostic masks are not a ready few/bulk classifier. Ground-truth prompts would make an automatic comparison invalid. |
| P09 / 2025 / DOI 10.1038/s41592-024-02580-4 | [µSAM primary abstract](https://pubmed.ncbi.nlm.nih.gov/39939717/): fine-tuned light/electron microscopy models with automatic and interactive segmentation; [author implementation](https://github.com/computational-cell-analytics/micro-sam). | Related biological microscopy supports domain adaptation and annotation assistance. Cellular objects differ from low-contrast flakes; prompts and labels must be accounted for. Full PMC retrieval was challenged; abstract/method scope verified. |
| P10 / 2021 / arXiv 2105.15203 | [SegFormer](https://arxiv.org/abs/2105.15203): hierarchical multiscale transformer with lightweight decoder; [B0 ImageNet encoder](https://huggingface.co/nvidia/mit-b0) is available. | Practical pretrained semantic challenger; published general-scene benchmarks do not validate graphene. [Official processor docs](https://huggingface.co/docs/transformers/model_doc/segformer) require preserving class 0 with label reduction disabled for our background class. |
| P11 / current author release / DINOv3 | [Official DINOv3 repository](https://github.com/facebookresearch/dinov3) lists ViT-S/16 and dense-feature/segmentation examples, with access-controlled weights and its own license. | Frozen-feature transfer is worth a probe under scarce labels. Patch scale, optical-contrast sensitivity, Colab memory, CPU time and later export remain unmeasured. It is not established as graphene SOTA. |

Unresolved leads: [2DU²-Net layer identification](https://www.mdpi.com/2079-6412/12/10/1551)
(DOI 10.3390/coatings12101551, 2022) surfaced a sixteen-model comparison in the
publisher search abstract; full-text/PDF retrieval failed. Do not base a ranking
on its headline score. [RepELA-Net](https://www.sciencedirect.com/science/article/pii/S1369800126005846)
(DOI 10.1016/j.mssp.2026.110988) surfaced a lightweight 2D-material model but has
a future 2026-11-15 issue date relative to this check; online publication date,
full protocol/code/weights were not verified. Retain as a lead, not an executable
candidate or evidence that our selected models are obsolete.

## Reproducibility and deployment inspection

[MaskTerial source](https://github.com/Jaluus/MaskTerial) documents Python 3.12,
Torch/Detectron2 and custom deformable-attention dependencies, plus a Colab demo.
[Author weight record](https://zenodo.org/records/15765516) openly lists synthetic
segmentation and material-specific checkpoints. This establishes availability,
not successful downloads, checksums, Colab execution or CPU/export suitability.
Its instance masks plus contrast classifier are not the current app's three-logit
contract. No silent replacement with a generic randomly initialized Mask2Former.

2D-TLK's [graphene config](https://github.com/zhouruiliangxian/2D-TLK/blob/main/2D-TLK_configs/graphene.py)
was read using authorized `gh`: FastViT-T8, two-class heads, `reduce_zero_label=True`,
random crops and a local `work_dirs/...pth` checkpoint path. Those settings cannot
be copied into our three-class partial-label comparison. GitHub's license endpoint
returned 404; a usable author-code license is not established. This is a current
admission blocker, not a claim that no license could exist elsewhere. Pretrained
weights and a successful reproduction are still unverified.

The existing baseline is **ImageNet-pretrained U-Net/ResNet-18**, not the original
vanilla U-Net trained from scratch. Its measured development score is supported
only on annotated pixels. No opened source establishes a common benchmark where
that baseline, SegFormer, DINOv3 and the domain models are fairly ranked on our
partial visual lab categories. **Inference:** measured local selection is essential.

## Proposed experiment priority

1. Re-evaluate the exact WI-06 checkpoint with complete supported error/resource
   reporting; retain it as a stable reference.
2. Train SegFormer-B0 and probe frozen DINOv3 ViT-S/16 with a small semantic head,
   sequentially, after their respective license/access/runtime gates.
3. Inspect 2D-TLK for a fourth semantic challenger; admit it only after code,
   weights, partial-loss, session recovery and three-logit compatibility checks.
   If that gate remains closed, propose DeepLabv3+/ResNet-18 with the same
   pretrained encoder as the baseline: a controlled multiscale-decoder hypothesis
   supported by the related P06 comparison, not a claim of domain superiority.
   Independently assess MaskTerial for domain transfer; a detection-only preview
   cannot win the complete few/bulk task or satisfy WI-08 readiness.
4. Test resolution/small-flake hypotheses for the shortlist before adding larger
   encoders. Confirm finalists across seeds and quantify the quality/resource
   trade-off on the same support. Keep test untouched during all selection.
5. Stop with a supported feasible recommendation or explicitly inconclusive
   conclusion when remaining uncertainty is a data/label/hardware limitation.
   New methods are hypotheses, not fabricated successful experiments.

All priorities are proposed. Multi-day Colab recovery is stakeholder-supported;
there is no invented fixed GPU-hour cap. Finite stages and any further candidate
expansion are reviewed in the single WI-07 proposal.
