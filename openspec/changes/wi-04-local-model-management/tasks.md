## 1. Review and execution gates

- [ ] 1.1 Obtain explicit approval of proposal/design/specs and proposed import/identity/recovery policies; record G-02 approval.
- [ ] 1.2 Refine existing Issue #4 from approved criteria; create linked work branch with `gh issue develop`; preserve unrelated edits.

## 2. Durable registry

- [ ] 2.1 Implement transactional v1-to-v2 upgrade, immutable model records and singleton selection, preserving unrelated artifacts (AC-1/2/4).
- [ ] 2.2 Extend file-before-metadata publication to commit artifact plus model atomically; add identity deduplication/conflict and availability recovery (AC-1/3/4).
- [ ] 2.3 Verify populated-v1 migration and interruption/corruption/restart boundaries with focused fixtures (AC-4).

## 3. Local management API

- [ ] 3.1 Add bounded streamed import, single validation slot/deadline, cleanup and lazy WI-02 validation; keep health responsive without extras (AC-1/3/4).
- [ ] 3.2 Add list/detail and integrity/current-compatibility checked explicit selection; expose sanitized error/status semantics and required local CORS (AC-1/2/3).
- [ ] 3.3 Verify two fixture identities, restart, repeated/conflicting imports, failed selection, concurrent mutations, lost response and missing-runtime behavior (AC-1–4).

## 4. Usable Models interaction

- [ ] 4.1 Extend current shell with Models navigation, import/list/details/selection and Workspace selection summary; retain truthful prediction messaging (AC-1/2/5).
- [ ] 4.2 Implement pending/error/stale/unavailable recovery, safe metadata rendering and reported/unmeasured evaluation labels (AC-3/4/5).
- [ ] 4.3 Check UI/API/restart flow, keyboard/focus, long-content rendering and desktop/narrow layout; record browser evidence (AC-1/2/5).

## 5. Verify and deliver

- [ ] 5.1 Run focused backend regressions and frontend typecheck/build; record AC-1–5 evidence in `docs/review/12_WI_04_VERIFICATION.md` (G-03/G-04).
- [ ] 5.2 Update usage/setup and technical recovery docs; update index/work-item/Issue references and human acceptance status (G-04).
- [ ] 5.3 Sync resulting specifications and archive the technically verified change; commit/push coherent Conventional Commits and open PR with `Closes #4` and acceptance evidence (G-04).

All tasks are pending. Proposal validation does not establish implementation acceptance.
