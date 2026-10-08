# PROGRESS (Master prompt v2)

Resume rule: after any restart or context compaction, re-read docs/MASTER_PROMPT_V2.md, this file, docs/OPTIMIZATION_PLAN.md and docs/PREREGISTRATION.md before doing anything. Decision log: `DECISIONS.md` at the repo root (the file CLAUDE.md names; the prompt's "docs/DECISIONS.md" refers to it, so there is one log, not two).

## Current phase
P4 Multi-dataset benchmark: development run in progress (P0-P3 done)

## Definition of done (status / evidence)
| # | Item | Status | Evidence |
|---|---|---|---|
| D1 | `v1-baseline` tag + scorecard vs HEAD | tag done; scorecard pending | `git tag` -> v1-baseline at 0d9b07c; docs/SCORECARD.md (P10) |
| D2 | >= 12 datasets accepted and benchmarked | accepted: 13 + sanity; benchmark running | backend/ml/quantum/registry.py, results/multi/ |
| D3 | PREREGISTRATION committed before multi-dataset results | done (41fdfc9) | docs/PREREGISTRATION.md commit hash |
| D4 | All D4 models tuned by nested CV, equal budget | partial (7 models + E-variants, single CV) | evaluate.TUNING_GRIDS |
| D5 | Multi-dataset statistics (corrected t, Friedman, Wilcoxon-Holm, CD, W/T/L, effect sizes) | pending | |
| D6 | Data-complexity analysis | pending | |
| D7 | Calibration (Brier, ECE, slope/intercept, reliability), sens@90/95, decision curves | partial (no slope/intercept, no DCA, 2 datasets) | evaluate.calibration_summary |
| D8 | Simulator layer, two-qubit noise, shots, scaling, qiskit transpile | partial (code in noise.py; runs + qiskit pending) | backend/ml/quantum/noise.py |
| D9 | Explainability validation on >= 5 datasets + plain-language text | pending | |
| D10 | Platform features | pending | |
| D11 | Reproducibility (reproduce script, pins, schema, Dockerfile/compose) | pending | |
| D12 | Quality gates green | green at 6acc2bd (pytest 97.4%, type-check, build, vitest) | |
| D13 | SIH deliverables + scripts/check_numbers.py | pending | |
| D14 | docs/SCORECARD.md | pending | |

## Machine (measured 2026-10-08)
- CPU: Intel Core Ultra 5 125U, 12 physical cores, 14 logical; RAM 15.4 GB total, ~4.7 GB free while two benchmark processes ran.
- Windows 11, PowerShell 5.1; Python 3.13.3 (.venv), Node 24.19.0, npm 11.17.0.
- .venv: pennylane 0.45.1, pennylane_lightning 0.45.0, torch 2.14.1+cpu, scikit-learn 1.9.1, numpy 2.5.3, pandas 3.0.6, shap 0.52.0, scipy 1.18.1.
- Not available: Kaggle credentials (neither ~/.kaggle/kaggle.json nor KAGGLE_* env vars), Docker, qiskit in .venv (qiskit MCP exists; connection state varies).
- Measured cost: tuned (6 configs x 3 inner folds) VQC, 5 outer folds, 200-row training cap: ~6 min per dataset; 3-layer VQC ~10 min (single process, others running). Classical models and QSVM: seconds.
- Run budget: torch threads = 1 per worker, at most 6 parallel workers (RAM-bound), every job checkpointed per dataset x model x repeat x fold.

## Baseline (v1-baseline, results/summary.json at 0413f33, untuned, 5-fold, mean AUC)
| Dataset | LogReg | RBF-SVM | RF | MLP | QSVM | VQC | Hybrid |
|---|---|---|---|---|---|---|---|
| Breast cancer | 0.979 | 0.978 | 0.977 | 0.981 | 0.955 | 0.980 | 0.980 |
| Heart (Cleveland) | 0.901 | 0.902 | 0.900 | 0.888 | 0.836 | 0.755 | 0.861 |

## Development-round results already logged (2 datasets, single 5-fold, commit e731b88)
- E3 (results/experiments/e3_qsvm_bandwidth/): tuned bandwidth raised QSVM pooled-OOF AUC vs untuned by +0.033 [0.017, 0.050] (breast) and +0.054 [0.015, 0.096] (heart), both significant after Holm; the C-only control did not (-0.001, -0.014, n.s.); tuned QSVM vs tuned LogReg n.s. on both. Chosen s in {0.1, 0.2, 0.35}.

## Running jobs
| Job | Started | Log | Notes |
|---|---|---|---|
| E6 then E4 (tuned, cv-only, 2 datasets) | 21:02 | results/experiments/e6.console.txt, e4.console.txt | PID 7084 launcher; not checkpointed (pre-v2 harness) |

## Blockers
- Kaggle-only candidates (Stroke, Framingham, Cardiovascular 70k, Lung cancer survey) cannot be downloaded: no credentials. UCI/OpenML fallbacks used.
- Docker not installed: Dockerfile/compose written, not built.

## Log
- P0: committed dev-round work (0264a3f..7ebabfc), new docs (6acc2bd), tagged v1-baseline at 0d9b07c.

## Resume point (2026-10-08, ~22:10)
- Commits: P1 cf83ace, P2 41fdfc9, P3 d29a97e + 65849b7, P4 runner 1f4570f. Gates green at 1f4570f (pytest 96.4%, type-check, build, vitest).
- RUNNING: development run (4 dev datasets x 19 models x 3 repeats x 5 folds), launched detached (PID 21664). Log: backend/ml/quantum/results/multi/run.log; checkpoints: results/multi/checkpoints/. Relaunch the same command to resume:
  python -m backend.ml.quantum.multibench run --split development --models logreg,svm_rbf,random_forest,mlp,hgb,mlp_matched,qsvm,qsvm_fixed,vqc,vqc_3layer,vqc_scale,vqc_reupload_scale,vqc_allz,vqc_allz_noent,vqc_twin,hybrid_qnn,hybrid_classical,residual_qnn,residual_classical --repeats 3 --workers 6
- NEXT: aggregate dev (multibench aggregate --split development), apply the VQC-variant selection rule (PREREGISTRATION sec. 6), run confirmation once, then P5-P10.
- Untracked: results/experiments/ (E0/E3/E6 dev-round outputs; e0/e6 summary.md have mojibake from the earlier encoding bug - regenerate before committing).
