# Label confirmation and background review

Checked: 2026-10-09. Consumer: stakeholder/lab reviewer deciding whether proposed
substrate patches can supply background supervision for WI-06.

## Confirmed by the stakeholder

The v3 polygons were made by laboratory personnel. The stakeholder considers them
usable for the exploratory baseline and reports subjective reliability **7/10**.
This is a personal assessment, not measured pixel accuracy, a probability,
a class weight or a guarantee of complete annotation.

After consulting the lab, the stakeholder reports that few/mono assignment was
**visual**: a somewhat transparent flake resembling examples previously classified
as few/mono, interpreted using annotator experience. Few-layer includes monolayer
in this project's target category. Retain bulk as the existing lab category;
a measured layer count and a >10-layer boundary are **not established**. No more
specific bulk visual decision rule was supplied. Predictions and evaluation refer
to these visual reference categories, not independently measured physical thickness.

The source-bound private schema-2 review now records human origin/eligibility and
approval of these visual label semantics. Its non-exhaustive coverage, exploratory
limitations, group decisions and 31/4/5 roles are retained. The label confirmation alone
did not edit any image, polygon, split or pixel label. The subsequent background
review adds only the eight approved class-0 interiors.

## Label-only preparation before background review

Preparation at `.workspace/wi06/dataset-v3/labels-confirmed-v2/` produces a valid
partial dataset, with zero review blockers. It contains supervised existing
foreground and unknown unannotated pixels. This does **not** satisfy the trainer's
all-three-class support gate: background remains zero in both train and validation.
The CLI preflight rejects this shortage before pretrained initialization or training.
Previous 41-blocker diagnostics are historical snapshots, not current label status.

## First background proposal round

A private gallery under `.workspace/wi06/background-review-round-01/` displays
four train samples and all four validation samples. No final-test image is proposed
or displayed. Each figure shows the original, nearby context and the exact proposed
256-by-256-pixel region, without changing colors or drawing inside the candidate
crop. Selection uses low texture/color deviation outside source annotations with
an annotation-free margin; this heuristic is **not evidence of substrate**. Faint
unannotated flakes can pass it. The user/lab must decide from the image/context.

`candidates.json` binds each proposed rectangle to its sample, effective role,
original image-byte/RGB/crop hashes, original coordinates, source/dataset/split
fingerprints and a pending decision. Original-coordinate crop PNGs are available
for inspection. The original proposals remain immutable. A separate `review-decisions.json` records
the stakeholder reply **"All are background"** for A1–A8 on 2026-10-09.
All eight become source-bound anchors in a new review/artifact, without claiming
that a laboratory expert personally inspected these particular patches.

For each candidate, use one of:

- **Background confirmed:** the whole proposed interior is sufficiently reliable
  substrate for regional supervision; record the reviewer/date/evidence.
- **Not background:** material or another unsuitable image region is present.
- **Uncertain:** possible transparent material or insufficient visual evidence;
  retain unknown supervision and select another region if needed.

Regional review does not require reliable pixel-by-pixel tracing of every flake or
complete background coverage. Confirm only conservative interiors. If a proposed
region contains ambiguity, reject it or request a smaller region; do not approve
it merely because the source has no polygon. Confirmations will be converted into
source-bound original-coordinate class-0 anchors in a new dataset artifact;
rejections/uncertainty remain separate evidence. Group roles and frozen test remain
unchanged. This static scientific gallery is not the future WI-15 prediction-review UI.

## Reproduce the gallery

Use the separate WI-06 Python environment and install the plotting dependency:

```bash
UV_CACHE_DIR=.workspace/wi06/uv-cache uv pip install --python .workspace/wi06/venv/bin/python \
  -r scripts/requirements-wi06-review.txt
.workspace/wi06/venv/bin/python scripts/prepare_background_review.py \
  .workspace/wi06/dataset-v3/labels-confirmed-v2 --output NEW_GALLERY_DIRECTORY
```

The reviewed dataset must pass its consumer contract. The output must be a new
directory. Figures/crops stay private under `.workspace/`; no lab pixels or newly
approved background labels are published by this script.

## Confirmed background handoff

The source-bound `background-reviewed-lab-review.json` records only the exact
approved interiors, with the stakeholder as reviewer and the actual date/evidence.
The active handoff is `.workspace/wi06/dataset-v3/background-confirmed-v2-round-01/`.
Original proposals, rejected initial diagnostic outputs and the zero-background
handoff remain distinct historical artifacts. Source foreground/conflicts and
test masks are unchanged; all other unannotated pixels remain 255.

Actual preparation returns **ready**, zero blockers, 40 images, 621 source polygons
and 1,792 unchanged conflict pixels. All 40 decoded masks were compared with the
label-confirmed handoff: only the eight exact 256-by-256 interiors change from
255 to 0; the five test mask file hashes are unchanged. No extra border pixels
were admitted by polygon rasterization.

| Effective role | Images | Background | Few-layer | Bulk | Unknown |
| --- | ---: | ---: | ---: | ---: | ---: |
| Train | 31 | 262,144 | 993,405 | 27,819,254 | 123,296,397 |
| Validation | 4 | 262,144 | 549,443 | 4,831,254 | 14,017,959 |
| Test | 5 | 0 | 84,933 | 4,584,350 | 19,906,717 |

Dataset fingerprint:
`d3b35af44c8d2364e70732d1708d68809405ee95301f173080bd004b8fa622c1`.
Split fingerprint (unchanged):
`92f9b55e88d17c9951da798bc8008b765c64ed888d06589484287d832600616e`.
Supervision fingerprint:
`c8795dc48e8ca8df50d84da7cddd21d651a228ea602a519091e1890ac41e451a`.

Public `graphene-train check` passes with the approved default 512-pixel configuration:
all three classes retain support in both roles, every active image retains usable
supervision and `resize_support_losses` is empty for train and validation.
The preflight initializes no model and performs no training.

A private 16,411,686-byte ZIP, `.workspace/wi06/background-confirmed-ready-dataset.zip`,
is prepared with `ready-dataset/` as its root. Every archived file was compared
byte-for-byte with the confirmed handoff. SHA-256:
`4aa3bc1ad4d29181338901d773d602613fb2bdc6613ea5d18155e28534ebbea7`.
It is not committed or published.

Gallery script compilation, native-crop/hash/margin checks, 19 Markdown link
checks, whitespace and strict active-change OpenSpec validation pass. Training
implementation is unchanged, so the prior 158 regressions and synthetic recovery
are not rerun or represented as new real-data training evidence.


## Remaining sequence

After the confirmed handoff passes preparation, consumer integrity and trainer
preflight, choose the Colab access/persistence method and start actual lab training. During the run,
retain completed generations outside Colab, recreate the runtime and resume.
The stakeholder accepts doing the real recovery trial when feasible; MCP access is preferred if available; the stakeholder allows either persistence
option, so Google Drive is selected for recovery. Actual browser/account
authorization and an active remote session remain required. No real lab
training, Google account connection or fresh-Colab-runtime evidence exists yet.


## Colab access preparation

The stakeholder prefers MCP if available and authorized its installation; either
persistence method is acceptable, so Google Drive is selected. Plugin-directory
search for Colab/Jupyter returned no available integration. The official Google
[Colab MCP repository](https://github.com/googlecolab/colab-mcp) was installed
privately at revision `b9ab3899e0f1fa493390b1fd6d54aa2e464ecdf1`, using its frozen
lock and a separate Python 3.13.14 environment. This does not alter the Python
3.12 training environment or dependencies.

A machine-local `.codex/config.toml` registers the separate executable only for
this repository, as supported by [official Codex configuration](https://learn.chatgpt.com/docs/config-file/config-basic).
The protected-directory write was explicitly approved through sandbox escalation.
No global agent settings were edited. `codex mcp get colab` confirms enabled stdio
registration. The local MCP startup/handshake lists its browser-connection tool;
remote tools require the user's authenticated browser session. Configuration and
installation remain private/ignored rather than publishing machine-specific paths.

The installed `google.colab` VS Code extension is version 0.9.7. Its
[official guide](https://github.com/googlecolab/colab-vscode/wiki/User-Guide)
describes notebook kernels, file uploads and Drive mounting; its UI is not directly
exposed to this agent. The official MCP bridges a browser session, rather than
implicitly inheriting the VS Code extension's account connection.

Next user step: reload the Codex client/window so it loads the configured MCP,
then authorize the browser/account connection when opened. Google Drive is chosen,
but no Drive mount, notebook upload, remote optimization or recovery trial has
happened yet. Do not claim mandatory AC-5 or archive WI-06 on installation alone.
