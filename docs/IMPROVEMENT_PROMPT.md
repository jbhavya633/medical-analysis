# Improvement prompt for Claude Code (paste into `claude` in the repo)

```
Read docs/RELATED_WORK.md and docs/LEARN_FROM.md first. Work autonomously, no questions. Rules: real metrics only, same seed 42 and the same 5 folds for every model, tune quantum and classical models with the same nested-CV budget, never tune on outer test folds, no copying code from other repos, commit locally in small atomic commits, push only to a remote named `mine` (never `origin`).

Implement, re-run the benchmark, and report before and after:
1. Nested-CV tuning for ALL models. Quantum: kernel bandwidth / feature-map scaling for the QSVM; learning rate, layers and epochs for the VQC and hybrid QNN. Classical: an equal-size grid.
2. A data re-uploading VQC variant with angle encoding (see C9 in LEARN_FROM.md) and a "dressed quantum circuit" variant (classical layer, quantum layer, classical layer).
3. Ablations: VQC without the CNOT ring; hybrid QNN with the quantum layer replaced by a same-size classical layer.
4. Paired significance tests per metric across folds with Holm correction; mark non-significant differences in the results table.
5. Calibration (Brier score, expected calibration error), a reliability plot, and sensitivity at fixed specificity (90% and 95%).
6. Noisy-simulator run (depolarising p in {0.001, 0.01, 0.05, 0.1}, finite shots) with a metric-versus-noise plot.
7. A threshold slider and risk bands (low / medium / high) on the Quantum Lab page, using the API's saved predictions.
8. Optional if time allows: a TorchQuantum path (check its Python/PyTorch compatibility first) and one Qiskit transpile with gate counts. No hardware submission without my approval.

Update the README results, the Delivery Table and the deck from the new results/*.json only (script-check that README numbers equal the JSON). Run pytest (coverage >= 80% on backend/ml/quantum), type-check, build, vitest. Final report (max 25 lines): before/after table, which hypotheses held, what failed, what needs my manual action.
```
