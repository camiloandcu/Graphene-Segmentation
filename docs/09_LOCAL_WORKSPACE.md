# Local workspace operations

Consumer: the operator setting up or recovering the lab computer, and developers
integrating model/dataset/results services with the local persistence boundary.

## Supported environment

Linux with a local filesystem; Python 3.12, uv, Node.js 24/npm. WI-01 has no
inference dependency or GPU requirement. The lab's 16 GB/RTX 3090 assumption will
be measured when inference and batch work are implemented.

Run the exact install/start commands in [README](../README.md). Dependencies are
locked by `backend/uv.lock` and `frontend/package-lock.json`. `requirements.txt` is
an exported alternative generated from the same Python lock; do not edit it by
hand. To regenerate after an approved dependency change:

```bash
cd backend
uv export --frozen --no-dev --no-emit-project --no-hashes --output-file requirements.txt
```

The frontend installation names the public registry matching its committed lock
URLs. This also avoids an npm 12 registry-mirror mismatch during clean installation;
[it does not enable arbitrary remote URL dependencies](https://docs.npmjs.com/cli/commands/npm-ci/).
Install scripts are disabled; the current Vite build is verified with that command.
If using an organization registry, mirror/lock URLs must be consistent.

After installation/build, startup requires no outbound internet. The supported
launcher binds `127.0.0.1`; it does not run a browser automatically. If port 8000
is occupied, set `GRAPHENE_PORT=8001` and open http://127.0.0.1:8001. The built UI
uses the same origin. Keep one server per workspace; a second writer is rejected.

## Files and configuration

Default root: `$XDG_DATA_HOME/graphene-segmentation`, falling back to
`$HOME/.local/share/graphene-segmentation`. Override using
`GRAPHENE_WORKSPACE_DIR=/absolute/local/path`. No cloud `.env` files are loaded by
the local configuration.

| Entry | Purpose |
| --- | --- |
| `workspace.sqlite3` | Versioned metadata, checksum/size, relative artifact references and availability. |
| `artifacts/<generated-id>.bin` | Opaque committed bytes, including original validated model ZIPs. |
| `staging/<generated-id>.tmp` | In-progress files, cleaned by exclusive startup recovery. |
| `.workspace.lock` | OS process lock; persists as a file after shutdown. Never delete it to bypass ownership. |

Only the generated storage namespace is eligible for orphan cleanup. Operator
notes, unrelated files, and legacy backend model/MLflow data are preserved. Metadata
uses relative paths so a stopped complete workspace can move without rewriting it.
Do not manually change artifact bytes: integrity failure makes a record unavailable.

## Model registry schema and upgrade

WI-04 upgrades schema v1 to v2 under the exclusive workspace lock, in one SQLite
transaction. Existing artifact IDs, bytes and metadata are preserved. The new
`models` table references a ZIP artifact and stores immutable identity, digests,
validated documents and CPU smoke evidence. A singleton `model_selection` row
records the explicit choice. Import does not change it.

Migration failure rolls back to v1. A complete v2 workspace requires a compatible
application; older versions reject it. Back up a stopped complete workspace before
upgrading if you need a rollback path; do not downgrade by editing `user_version`.
Health reports schema v2 and `model_loaded: false`: selection is distinct from a
production inference session. See [model operations](11_LOCAL_MODEL_MANAGEMENT.md).

## Stop, back up and restore

1. Stop the server with Ctrl+C and wait for shutdown to finish. Stop any developer
   scripts using the same workspace too.
2. Copy the entire root, including SQLite metadata and artifacts, to a backup
   location. Do not copy just the database or just the artifact directory.
3. To restore, copy the complete backup into a separate local directory. Preserve
   the original until you have verified the restored copy.
4. Start with `GRAPHENE_WORKSPACE_DIR` pointing to the restored copy. Check health
   and, once a consumer is available, the saved records/artifacts.

Never copy a live workspace as if it were a consistent backup. Startup acquires
an exclusive lock before recovery; copying the lock file is harmless after the
old process has exited because ownership is an OS lock, not file contents.

## Failure recovery

Artifact publication writes/fsyncs staging bytes, atomically moves them on the
same filesystem, fsyncs the destination directory, then commits SQLite metadata.
Success follows both file durability and commit. Failed writes roll back metadata
and clean generated files; interruption leaves orphans for startup recovery.

Missing/corrupt artifacts remain unavailable and are never replaced with empty
files. Recovery reports counts rather than paths or data. Restore an intact complete
backup to a separate directory if committed data was lost. Unknown newer schema
versions fail startup without resetting the database; use a compatible application.

| Symptom | Action |
| --- | --- |
| Frontend assets missing | Run the README frontend installation/build commands. |
| Backend environment missing | Run `uv sync --locked --no-dev --python 3.12` in backend. |
| Workspace already open | Stop the other server; do not remove its lock file. |
| Cannot initialize/write workspace | Check directory permissions and available local disk space. |
| Connection unavailable | Start the server, use the right port/origin, then select Check connection. |
| Unsupported schema | Use a compatible application or restore a compatible backup separately. |

## Verification boundary

Health is runtime/storage readiness, not evidence of a trained or working model.
The UI accurately reports no ready model. There is no public opaque-artifact upload
endpoint. The internal `Workspace.publish/lookup/read` service is tested for
persistence and recovery; model validation is WI-02/WI-04.

The production installation has no Supabase, TensorFlow, PyTorch, MLflow or auth
packages. Legacy modules/tests remain in source but are not imported/mounted in
local startup. They are not supported by the new local dependency set. Cloud
migration and shared-network use require separate approval.

Lifecycle cleanup uses [FastAPI lifespan](https://fastapi.tiangolo.com/advanced/events/).
SQLite metadata commits use [explicit transactions](https://docs.python.org/3.12/library/sqlite3.html).
The supported dependency install follows [uv's locked sync](https://docs.astral.sh/uv/concepts/projects/sync/).
