#!/usr/bin/env bash
# One-command demo: install deps, run the benchmark, start the API (:8000) and the frontend (:3000).
# Research prototype - not a diagnostic tool.
set -euo pipefail
cd "$(dirname "$0")/.."
PY="${PYTHON:-python}"

echo "==> Installing Python dependencies (CPU torch + QML stack)"
"$PY" -m pip install -q torch==2.14.1 torchvision==0.29.1 --index-url https://download.pytorch.org/whl/cpu
"$PY" -m pip install -q -r backend/requirements-qml.txt

echo "==> Installing frontend dependencies"
npm ci --no-audit --no-fund

if [ "${SKIP_BENCHMARK:-0}" != "1" ]; then
  echo "==> Running benchmark (about 7 minutes on a laptop CPU)"
  "$PY" -m backend.ml.quantum.benchmark --dataset all --seed 42 --n-qubits 6
fi

echo "==> Starting API on http://localhost:8000 (docs at /docs)"
"$PY" -m uvicorn backend.main:app --port 8000 &
API_PID=$!
trap 'kill $API_PID 2>/dev/null || true' EXIT

echo "==> Starting frontend on http://localhost:3000 -> open /quantum-lab"
npm run dev
