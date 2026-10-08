# Graphene Workspace

A local microscopy workspace for a lab studying graphene. The intended workflow
is to inspect segmentation masks and prioritize image batches by the fraction
covered by few-layer graphene. Training will run separately in free-tier Colab.

**Current delivery: WI-01 local foundation and WI-02 portable model contract.** The application opens without
accounts, checks local storage, and keeps metadata/artifacts across restarts.
Model import, prediction, batch ranking, exports, and Colab training are tracked
in subsequent Work Items and are not available in this build. Exporters and model
authors can now use the shared package schema, image transforms, and bounded
ONNX compatibility validator. No trained model
or lab performance is claimed.

The [lab dataset audit](docs/review/wi03/00_INDEX.md) now records the supplied
40-image export's label support, conflicts and evaluation limitations. It supports
conditional pilot planning; it does not establish an independent test benchmark.

## Run on Linux

Requirements: Python 3.12, [uv](https://docs.astral.sh/uv/), Node.js 24, and npm.
Internet is needed to install dependencies. Normal use is offline; Supabase/JWT
credentials and cloud accounts are not needed.

From the repository:

```bash
cd backend
uv sync --locked --no-dev --python 3.12
cd ../frontend
npm ci --registry=https://registry.npmjs.org --ignore-scripts --no-audit --no-fund
npm run build
cd ..
./scripts/start-local.sh
```

Open **http://127.0.0.1:8000**. Stop with **Ctrl+C**. Restart using the same launcher.
The server defaults to loopback and a single worker. No GPU is required for this
foundation; inference/GPU support belongs to later items.

Data defaults to `~/.local/share/graphene-segmentation` (or the configured XDG data
directory). To choose another location:

```bash
GRAPHENE_WORKSPACE_DIR=/path/to/lab-workspace ./scripts/start-local.sh
```

See [local setup, backup and recovery](docs/09_LOCAL_WORKSPACE.md) before copying
or restoring a workspace. Existing Supabase and legacy model/MLflow data are
untouched; this version starts a separate local workspace.

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

Work proceeds one approved OpenSpec change at a time. Implementation branches
link to their Issue, and PRs include the acceptance evidence and a closing link.
