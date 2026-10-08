#!/usr/bin/env bash
set -euo pipefail
project_dir="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")/.." && pwd)"
if [[ ! -f "$project_dir/frontend/dist/index.html" ]]; then
  echo 'Frontend assets are missing. Run: cd frontend && npm ci && npm run build' >&2
  exit 1
fi
if [[ ! -x "$project_dir/backend/.venv/bin/python" ]]; then
  echo 'Backend environment is missing. Run: cd backend && uv sync --locked --no-dev --python 3.12' >&2
  exit 1
fi
cd "$project_dir/backend"
workspace_port="${GRAPHENE_PORT:-8000}"
if [[ ! "$workspace_port" =~ ^[0-9]+$ ]] || (( workspace_port < 1 || workspace_port > 65535 )); then
  echo 'GRAPHENE_PORT must be a port number between 1 and 65535.' >&2
  exit 1
fi
exec .venv/bin/python -m uvicorn main:app --host 127.0.0.1 --port "$workspace_port" --workers 1
