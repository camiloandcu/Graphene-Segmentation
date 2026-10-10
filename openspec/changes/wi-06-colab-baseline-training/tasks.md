# WI-06 implementation tasks

Status: revised and explicitly approved on 2026-10-09. Dataset-v3 audit/replacement and
31/4/5 partial-mask previews and software implementation are complete. CPU checks pass; real Colab setup/data preflight passed. The first GPU trial
failed before completing an epoch; the deterministic loss fix is pushed and
successful lab training/recovery remain unverified. See
`docs/review/14_WI_06_VERIFICATION.md`.

- [x] 1. Obtain explicit approval of proposal/design/specs and ML policies (G-01/2).
- [x] 2. Refine Issue #6, link `feat/wi-06-colab-baseline-training` with `gh issue develop 6`, and commit approved context.
- [x] 3. Extend the dataset contract with explicit partial-v2 review/masks/anchors/supervision identity and preserve dense-v1 behavior; implement the separate training package/configuration/environment and validated role adapter (AC-1/2).
- [x] 4. Implement pretrained model initialization, shared letterbox adapter, paired transforms and ignore-aware loss (AC-2).
- [x] 5. Implement deterministic original-coordinate supervised development counts/metrics, unknown/support disclosure and best/tie selection (AC-4).
- [x] 6. Implement immutable completed-epoch generations, full state/RNG restoration, compatibility checks and persistence recovery (AC-3).
- [x] 7. Add meaningful loader/geometry/loss/selection and interrupted-versus-resumed CPU checks, including tamper/write/mismatch failures (AC-1–4).
- [x] 8. Create thin Colab notebook and setup/persistence/recovery guide; verify clean separate installation and notebook syntax (AC-2/5).
- [x] 9. Laboratory human origin/visual semantics and eight stakeholder-reviewed background interiors are confirmed. MCP is preferred and locally installed/registered; Google Drive is selected. Browser execution and Tesla T4/CUDA package setup are verified; dataset transfer is checksum-verified, Drive is authorized/mounted and public Colab preflight passed (AC-1/5) (AC-1/5).
- [ ] 10. Run the pretrained baseline in interactive Colab, retain checkpoints outside transient storage, recreate runtime and resume; reconcile best history/handoff (AC-2–5).
- [x] 11. Record actual evidence and AC-1–5 status in `docs/review/14_WI_06_VERIFICATION.md`; update README and authoritative tracking (G-03/4).
- [x] 12a. Run affected package regressions, strict OpenSpec and whitespace/link checks (G-04).
- [ ] 12b. Sync specifications/archive only after required real verification passes (G-04); AC-5 remains unverified.
- [x] 13. Push coherent Conventional Commits, open PR with `Closes #6` and criterion evidence, and record references/pending gates (G-04). Keep item acceptance open if real execution remains unverified.

Submission: [draft PR #20](https://github.com/camiloandcu/Graphene-Segmentation/pull/20) contains `Closes #6`.
The branch is pushed. Tasks 10 and 12b remain pending because completed optimization, checkpoint retention and fresh-Colab-runtime
evidence remain pending. AC-5 is
unverified; no completed archive/spec sync is claimed.
