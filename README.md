# Graphene Workspace

A local microscopy workspace for a lab studying graphene. The intended workflow
is to inspect segmentation masks and prioritize image batches by the fraction
covered by few-layer graphene. Training will run separately in free-tier Colab.

**Current delivery: local workspace, portable model contract, dataset audit and
model management, offline dataset preparation and a separate baseline trainer (WI-01 through WI-06 software).** Open without an account, import a
compatible model ZIP, inspect its supplied evaluation, and explicitly select it.
Model files, metadata and selection persist locally across restarts.

Prediction, batch ranking and result exports are later Work Items and are not
available in this build. The separate trainer and Colab notebook are available;
real lab training and fresh-runtime Colab recovery remain unverified. Compatibility does not certify lab accuracy;
no trained model or lab performance is claimed.

The [lab dataset audit](docs/review/wi03/00_INDEX.md) now records the supplied
40-image export's label support, conflicts and evaluation limitations. It supports
conditional pilot planning; it does not establish an independent test benchmark.

For trainers, the [offline dataset workflow](docs/13_VALIDATED_DATASETS.md)
validates the COCO export, preserves canonical classes/provenance and enforces
reviewed split decisions. The [current v3 review](docs/review/wi06/01_DATASET_V3_REVIEW.md)
records refined labels on the same 40 images and grouped assignments. Coverage
remains uncertain. Partial-v2 preparation is implemented; laboratory visual labels and eight
background regions are stakeholder-confirmed. Real Colab training/recovery remains pending. Saved predictions cannot enter ground truth automatically.
Regional human review is a planned workflow, not an available feature.
The [training guide](docs/14_COLAB_BASELINE_TRAINING.md) explains the separate
CLI/notebook, masked validation metrics and verified checkpoint recovery.

## Run on Linux

Requirements: Python 3.12, [uv](https://docs.astral.sh/uv/), Node.js 24, and npm.
Internet is needed to install dependencies. Normal use is offline; Supabase/JWT
credentials and cloud accounts are not needed.

From the repository:

```bash
cd backend
uv sync --locked --no-dev --extra models --python 3.12
cd ../frontend
npm ci --registry=https://registry.npmjs.org --ignore-scripts --no-audit --no-fund
npm run build
cd ..
./scripts/start-local.sh
```

Open **http://127.0.0.1:8000**. Stop with **Ctrl+C**. Restart using the same launcher.
The server defaults to loopback and a single worker. No GPU is required for model
management; inference/GPU support belongs to later items.

Data defaults to `~/.local/share/graphene-segmentation` (or the configured XDG data
directory). To choose another location:

```bash
GRAPHENE_WORKSPACE_DIR=/path/to/lab-workspace ./scripts/start-local.sh
```

See [local setup, backup and recovery](docs/09_LOCAL_WORKSPACE.md) before copying
or restoring a workspace. Existing Supabase and legacy model/MLflow data are
untouched; this version starts a separate local workspace.

## Import and select a model

Open **Models**, choose a v1 model ZIP (maximum 256 MiB), and select **Import
model**. Review its details, then choose **Select model**. Importing keeps your
current selection. Reimporting the same ZIP reuses its entry; changed packages
must use a new model ID. Few-layer settings come from the package.

Evaluation is labeled **unmeasured** or **reported**. Reported results are supplied
by the exporter and are not independently verified by the workspace. A selected
model prepares the later prediction workflow; prediction is still unavailable.

Model support is optional. For the storage-only installation, omit `--extra models`;
the app still opens and shows saved model details, with installation guidance for
import/selection. If a selected file is missing or damaged, choose an intact model
or restore a complete workspace backup; the app never silently switches models.
See [model management and recovery](docs/11_LOCAL_MODEL_MANAGEMENT.md).

## Development and verification

```bash
cd backend
uv sync --locked --python 3.12
.venv/bin/python -m pytest
cd ../frontend
npm run build
```

The supported suite is `backend/tests_local`; legacy cloud tests/screens are
retained as reference but are outside this runtime and its type-check entry graph.
The build includes TypeScript checking for the supported frontend. Vite development
uses `npm run dev` at http://127.0.0.1:3000 with the local backend running.

For model contract development, install the optional CPU validation runtime and
run its shared tests alongside the local app tests:

```bash
cd backend
uv sync --locked --extra models --python 3.12
.venv/bin/python -m pytest tests_local ../packages/graphene-model-contract/tests
```

See the [portable model contract](docs/10_PORTABLE_MODEL_CONTRACT.md) for package
requirements, standalone installation, synthetic examples, and resource limits.

- [Product, architecture and repair review](docs/review/00_INDEX.md)
- [Work Items and GitHub Issues](docs/review/08_GITHUB_WORK_ITEMS.md)
- [WI-01 verification evidence](docs/review/09_WI_01_VERIFICATION.md)
- [WI-02 verification evidence](docs/review/10_WI_02_VERIFICATION.md)
- [WI-03 dataset audit evidence](docs/review/11_WI_03_VERIFICATION.md)
- [WI-04 model management evidence](docs/review/12_WI_04_VERIFICATION.md)
- [WI-05 validated dataset evidence](docs/review/13_WI_05_VERIFICATION.md)

Work proceeds one approved OpenSpec change at a time. Implementation branches
link to their Issue, and PRs include the acceptance evidence and a closing link.
