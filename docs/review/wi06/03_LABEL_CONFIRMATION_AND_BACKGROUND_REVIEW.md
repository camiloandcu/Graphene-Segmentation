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

Connection follow-up: the browser-opening attempt was interrupted. The resumed
conversation no longer exposed the native Colab tool, so a private local stdio
client of the installed official MCP is used as a fallback. No browser connection
was confirmed within the initial timeout; an interactive client remains available
for user authorization. No dataset upload, Drive mount or training is claimed.


## Browser timeout diagnosis and local repair

The restarted host process was listening on IPv4 loopback, and its log recorded
incoming WebSocket connections after the browser-open tool had timed out. Browser
access still failed. The installed upstream code passed the long-lived proxy
initialization task into a gather cancelled by `asyncio.wait_for` on timeout.
A targeted asynchronous reproduction confirmed that the handshake task became
cancelled after the timeout.

The private installation now applies [this one-line local patch](../../../scripts/colab-mcp-timeout.patch)
to the pinned upstream revision: shield the proxy initialization task while waiting.
Its timeout still returns normally, but initialization can continue when the user
connects later. Verification passes for early connection, task survival across
timeout, late initialization and a subsequent wait. The original upstream source
is retained privately for rollback. This is a local repair, not an upstream release
or a change to the training package. The corrected host instance was restarted;
actual browser/notebook access remains unconfirmed and no lab run has started.


Browser connection is now verified: the official MCP returned `result: true`,
exposed notebook editing/reading tools, and `get_cells` successfully returned one
empty code cell with no error. The private client adapter was corrected to serialize
FastMCP's dataclass response through its content/structured-content fields and to
retain the session on tool errors. Its host restart preserved the connection URL,
port and token, and the subsequent real read completed without terminating the
client. This establishes browser/notebook access only; compute-runtime access,
Drive mounting/authorization, dataset upload and actual training remain unverified.


Notebook preparation, 2026-10-10: with explicit stakeholder authorization, the ten
cells from `notebooks/01_COLAB_BASELINE_TRAINING.ipynb` were copied into the
connected Colab notebook, reusing its original empty code cell. Public `get_cells`
readback verified every cell's order, type and source. The only source adaptations
select `PERSISTENCE_CHOICE = "drive"` and run ID
`graphene-baseline-wi06-20261010-001`; `DEVICE = "cuda"` and the pinned revision
remain as in the template. The stakeholder reports selecting a GPU runtime and
will authorize Drive when prompted. No cell was executed during the copy: runtime
GPU verification, dependency installation, dataset transfer, Drive mounting and
actual training/recovery remain pending. Private cell IDs/readback records are
under `.workspace/wi06/colab-notebook-copy.json`.


## Live GPU setup and transfer status, 2026-10-10

Executing code through the connected browser verified Python 3.13.15 and a Tesla
T4 with 15,360 MiB. Installation completed in the Colab runtime; a subsequent
probe imported the training package and verified Torch 2.7.1+cu126, CUDA
availability and an actual CUDA tensor operation. Installed package versions were
Torchvision 0.22.1, segmentation-models-pytorch 0.5.0, graphene-training 1.0.0
and graphene-dataset-contract 2.0.0. The installation cell exceeded the MCP call
timeout, but the later executable probe confirmed completion.

Reconnecting the browser reset the visible notebook to one empty cell while
preserving the GPU runtime and installed packages. The queued archive transfer
failed before writing any data because its temporary notebook cell no longer
existed. A new runtime probe confirmed that the transfer ZIP is absent. Notebook
restoration then exposed an unavailable tool name in the private batch helper;
the helper was corrected and restarted on the same connection link. Restoration
must use the actual advertised tool schemas after reconnection.

Notebook restoration subsequently passed type/source readback using the browser's
advertised `add_text_cell` and `add_code_cell` tools. All 68 transfer commands
completed. Remote SHA-256 verification matched
`4aa3bc1ad4d29181338901d773d602613fb2bdc6613ea5d18155e28534ebbea7`
for the 16,411,686-byte archive, extracted 40 images and confirmed dataset identity
`d3b35af44c8d2364e70732d1708d68809405ee95301f173080bd004b8fa622c1`.
The temporary transfer cell was removed. Private retained evidence is in
`.workspace/wi06/colab-transfer-verified.json`.

A dependency consistency probe found NumPy 2.1.3 still loaded while 2.2.6 was
installed. Restarting only the Python kernel through its shutdown/restart API
resolved the mismatch without replacing the VM or losing staged files. The next
probe verified NumPy 2.2.6, Pillow 11.3.0, CUDA/Tesla T4, archive size and actual
Git revision `12be26b90bf3cd576a7574101b36a92246bb004c`. This setup
restart is not evidence of checkpoint recovery. The stakeholder authorized Drive; notebook output confirms mounting at
`/content/drive` and completed public trainer preflight. All three classes retain
support after resizing, with no per-image resize support losses. Private evidence
is in `.workspace/wi06/colab-preflight-verified.json`.

The trial retained the checksum-verified dataset archive in Drive and downloaded
the actual pretrained encoder. It then failed on the first GPU loss computation:
`nll_loss2d_forward_out_cuda_template` rejects sum/mean spatial reduction under
Torch 2.7 strict deterministic mode. No epoch completed. The original run ID
`graphene-baseline-wi06-20261010-001` is diagnostic state, not a resumable
completed generation. Preserve it rather than treating initialization as recovery.

Fix `b0480172dd80181efbd7241b7c8e2853818407f4` computes unreduced per-pixel CE
then reduces the tensor separately, retaining the ignored-pixel denominator and
foreground Dice. The pinned [Torch 2.7.1 kernel source](https://github.com/pytorch/pytorch/blob/v2.7.1/aten/src/ATen/native/cuda/NLLLoss2d.cu)
confirms atomic additions are specific to the spatial sum/mean path. Training
regressions pass: 21 passed, one CUDA test skipped locally. The new regression
compares CPU CE values/gradients and the CUDA test requires strict deterministic
forward/backward with exact repeated values/gradients and zero ignored gradients.
Actual execution of that CUDA regression and a new lab trial are pending.

The private helper now accepts file-backed commands and handles malformed input
without terminating; this addresses terminal truncation during the GPU-probe
submission. The source fix is pushed on the existing feature branch. The user has
a saved Drive notebook copy and will connect MCP there; inspect its actual cells
and runtime before edits or execution. Update to the fixed code pin and use a new
run ID (proposed `graphene-baseline-wi06-20261010-002`) rather than reusing the
failed initialization. Actual completed epochs, checkpoint retention and
fresh-runtime recovery remain unverified. Private client/session/transfer
records remain under `.workspace/wi06/`. Save the browser notebook in Drive to
preserve cells across scratch-notebook reloads; notebook persistence and verified
training checkpoint retention are separate requirements.
