# WI-06 implementation tasks

Status: revised and explicitly approved on 2026-10-09. Dataset-v3 audit/replacement and
31/4/5 partial-mask previews are complete; no implementation or real training.

- [x] 1. Obtain explicit approval of proposal/design/specs and ML policies (G-01/2).
- [x] 2. Refine Issue #6, link `feat/wi-06-colab-baseline-training` with `gh issue develop 6`, and commit approved context.
- [ ] 3. Extend the dataset contract with explicit partial-v2 review/masks/anchors/supervision identity and preserve dense-v1 behavior; implement the separate training package/configuration/environment and validated role adapter (AC-1/2).
- [ ] 4. Implement pretrained model initialization, shared letterbox adapter, paired transforms and ignore-aware loss (AC-2).
- [ ] 5. Implement deterministic original-coordinate supervised development counts/metrics, unknown/support disclosure and best/tie selection (AC-4).
- [ ] 6. Implement immutable completed-epoch generations, full state/RNG restoration, compatibility checks and persistence recovery (AC-3).
- [ ] 7. Add meaningful loader/geometry/loss/selection and interrupted-versus-resumed CPU checks, including tamper/write/mismatch failures (AC-1–4).
- [ ] 8. Create thin Colab notebook and setup/persistence/recovery guide; verify clean separate installation and notebook syntax (AC-2/5).
- [ ] 9. Obtain reviewed label eligibility and reliable background anchors for the active v3 dataset plus account/access/persistence choice before real Colab execution; retain unresolved inputs as blockers (AC-1/5).
- [ ] 10. Run the pretrained baseline in interactive Colab, retain checkpoints outside transient storage, recreate runtime and resume; reconcile best history/handoff (AC-2–5).
- [ ] 11. Record actual evidence and AC-1–5 status in `docs/review/14_WI_06_VERIFICATION.md`; update README and authoritative tracking (G-03/4).
- [ ] 12. Run affected package regressions, strict OpenSpec and whitespace/link checks; sync/archive only after required verification passes (G-04).
- [ ] 13. Push coherent Conventional Commits, open PR with `Closes #6` and criterion evidence, and record references/pending gates (G-04). Keep item acceptance open if real execution remains unverified.
