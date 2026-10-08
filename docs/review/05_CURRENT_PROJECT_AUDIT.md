# Current project audit

Checked: 2026-10-07. Findings below are source-verified unless labeled otherwise.
No live database, external account, or trained model was accessed.

## ML and inference defects

| Severity | Evidence | User impact / repair |
| --- | --- | --- |
| Critical | `model_manager.py:146,180` divides a single binary output into three IDs using 0.33/0.66. | Binary scores cannot establish background/few-layer/bulk classes. Require a validated multiclass contract. |
| Critical | `training_service.py:443` selects the first saved segmentation as a training mask; `datasets.py:171` can save predictions into the same table. | No ground-truth provenance check; predictions can be treated as truth. Separate annotations from predictions. |
| High | `training_service.py:477` stretches training inputs; inference letterboxes at `model_manager.py:84`. | Training/inference mismatch. Share exact preprocessing and mask geometry. |
| High | Pretrained SMP encoders are used, but input processing only divides by 255. | Encoder normalization is not represented in the inference contract. Record and apply required preprocessing. |
| High | `training_service.py:487` uses first 20% of database records for validation, ignoring imported split roles and acquisition groups. | Split leakage and biased evaluation; retain a deterministic reviewed split manifest. |
| High | `training_service.py:510` constructs a fresh ImageNet model rather than loading selected model weights. | The UI's selected-model training does not actually fine-tune that model. Make initialization explicit. |
| High | `training_service.py:529` gives absent classes IoU 1.0 and averages batch metrics; `:658` removes background rows/columns. | Inflated/ambiguous evaluation and hidden errors; accumulate full confusion counts and report support. |
| High | `training_service.py:684` exports the final model, while best metrics are tracked separately. | Reported best performance can refer to different weights. Export/evaluate the selected checkpoint. |
| High | `datasets.py:369` writes raw COCO category IDs into masks. | Source taxonomy can silently conflict with model output IDs. Map reviewed class names explicitly. |
| High | Imported annotations and image errors are swallowed; empty annotation sets do not produce validated background masks. | Apparently successful datasets can have missing/incorrect labels. Provide a structured import report and fail invalid imports. |
| High | Dataset importer writes `images.split` and `segmentations.classes_found`; committed schema initially defines neither `images.split` nor `classes_found` (`classes_present` is defined instead). | New installations can fail or silently import incomplete data. Align schema/code with repeatable migrations. |
| High | `datasets.py:175` accepts `model_id`, but inference uses the process-global active service without loading/verifying that ID. | Saved result provenance can name a different model from the one used. Bind inference to requested identity. |
| Medium | `experiments.py:50` contains a synthetic training-results generator. Current `/train` calls the real TrainingService; no call to the generator was found. | Dead simulated metrics code should be removed; do not claim current endpoint produces fake metrics. |

## Application and access defects

- `app/core/config.py:36` prints the Supabase key and JWT secret when settings load.
- `app/api/routes/auth.py:23,170` accepts an admin role during public registration.
- `app/api/routes/users.py` exposes user listing/detail/deletion without authentication dependencies.
- `model_manager.py:285` calls `torch.load(..., weights_only=False)` on an uploaded checkpoint.
- Model selection/inference is process-global despite user-scoped registry loading;
  loading a model can affect other sessions and preprocessing is not snapshotted
  consistently with the adapter.
- Registry activation deactivates/updates records one by one; the README's
  atomic-activation claim is not supported by a database transaction.
- Registry deletion removes the artifact before database deletion; rollback creates
  an empty file rather than restoring its contents.
- Uploads and ZIP/image expansion lack deliberate size/resource bounds.
- CORS combines wildcard origins with credentials.
- Frontend requests often bypass the shared API client; App does not subscribe to
  its `auth:logout` event or verify restored roles/session on startup.
- Dependency definitions disagree. Training/import dependencies are missing from
  `requirements.txt`; the project dependencies include both TensorFlow and
  TensorFlow Intel alongside PyTorch without a clear deployment target.
- Existing API tests substitute a model service and do not override newly required
  auth dependencies. They cannot currently establish the real model import/predict flow.

## UX and export defects

- Navigation gives Experiments, Datasets, Models, Analytics equal prominence to
  the primary lab task. Prediction handles only one image and provides no batch ranking.
- Model upload requires framework/architecture/encoder/class/config choices that
  should be supplied by a validated package, not ordinary lab users.
- Overlay blends black background across the entire image, reducing original-image clarity.
- Export saves original JPEG/TIFF bytes with a `.png` name, omits the raw mask from
  its main ZIP flow, interpolates unescaped filenames/model text into HTML, and
  spreads whole image byte arrays into `String.fromCharCode`, which can fail on large files.
- The fixed sidebar/app layout and modal implementation need responsive and
  keyboard/focus verification; dialogs lack accessible role/focus management.
- UI findings are from source inspection; no browser visual assessment is claimed.

## Baseline checks

- Working tree was clean on `main` before review artifacts/dependency installation.
- Python AST parsing: all 37 source files parsed successfully.
- Python runtime dependencies (including pytest/FastAPI/PyTorch/Supabase) are not
  installed in the provided environment. Backend tests and inference were not run.
- Frontend dependencies installed for baseline build/type-check assessment.
- `npm run build` reached Vite's transform stage; `npx tsc --noEmit` started but
  produced no diagnostic result. Both were interrupted after several minutes
  without completion. Neither check is recorded as passing or failing; investigate
  the runtime/dependency behavior and rerun in the implementation environment.
- Dataset annotations were inspected through public byte-range reads without
  downloading the full 2.11 GB archive. Image pixels and lab masks remain unreviewed.
