# MedFusion / SIH26139 - Hybrid Quantum ML for Early Disease Detection

Research prototype. Not a diagnostic tool.

## Stack
- Frontend: React 18 + TypeScript + Vite + Tailwind, React Query, Recharts (`src/`)
- Backend: Python 3.10+, FastAPI gateway `backend/main.py` (port 8000), scikit-learn, PyTorch (CPU), PennyLane `default.qubit`
- Persistence: JSON under `backend/ml/quantum/results/`; optional Supabase migration in `backend/db/migrations/` (not applied)

## Commands
- One command demo: `bash scripts/run_demo.sh`
- Install: `npm ci` and `pip install -r backend/requirements.txt`
- Benchmark: `python -m backend.ml.quantum.benchmark --dataset all --seed 42 --n-qubits 6`
- API: `python -m uvicorn backend.main:app --port 8000` (docs at /docs)
- Frontend: `npm run dev` (port 3000, proxies /api -> :8000)
- Tests: `python -m pytest backend/tests -q --cov=backend/ml/quantum` and `npx vitest run`
- Checks: `npm run type-check`, `npm run build`, `npm run lint` (pre-existing lint backlog is non-blocking)

## Folder map
- `backend/ml/quantum/` hybrid QML package: data, preprocess, baselines, qkernel, vqc, hybrid_qnn, explain, evaluate, benchmark, service, router
- `backend/ml/quantum/results/` committed benchmark JSON, summary.md, plots, small model files
- `backend/models/` existing ECG / X-ray / CT wrappers (503 when weights are missing)
- `backend/tests/` pytest; `src/pages/__tests__/` vitest
- `src/pages/QuantumLab.tsx` Quantum Lab UI; `docs/` README assets, deck, demo script, issues

## Rules
- Complete, runnable code; minimal explanation.
- No new abstractions; routers only delegate to service functions.
- New folders only under backend/ml/quantum/, backend/tests/, docs/, .github/workflows/.
- Never commit secrets (.env) or model binaries > 5 MB; no real patient data.
- Report real metrics only, from logged runs. Never tune on the test set or cherry-pick seeds.
- Seed 42 everywhere. Keep the "not a diagnostic tool" notice in UI, README, API docs and deck.
- Log autonomous decisions in DECISIONS.md.
