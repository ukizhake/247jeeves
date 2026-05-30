#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

if [[ ! -d .venv ]]; then
  python3 -m venv .venv
  .venv/bin/pip install -r requirements.txt -q
fi

export PYTHONPATH="$ROOT"
.venv/bin/uvicorn api.main:app --reload --port 8888 &
API_PID=$!

cd web
npm run dev &
WEB_PID=$!

trap 'kill $API_PID $WEB_PID 2>/dev/null' EXIT
wait
