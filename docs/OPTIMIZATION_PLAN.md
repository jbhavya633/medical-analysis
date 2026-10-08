# Optimisation plan (SIH26139): ranked, evidence-backed experiments

Written 2026-10-08 from `docs/LEARNING_LOG.md` (source IDs) and `docs/INFERENCES.md`. **Nothing here is implemented yet**; this is the input for `docs/IMPROVEMENT_PROMPT.md`. Success means a fairer, tuned, significance-tested comparison with an honest conclusion, not "quantum beats classical".

## Shared protocol (applies to every experiment)

- **Data and folds:** the same as today. `StratifiedKFold(5, shuffle=True, random_state=42)` on the full data, with each training fold stratified-subsampled to 200 rows using seed 42 (`evaluate.py:72-73`). Seed 42 everywhere; no seed search.
- **Nested tuning:** inner `StratifiedKFold(3, shuffle=True, random_state=42)` on the outer training fold only. The preprocessor sits **inside** the inner pipeline (MI selection is supervised). Selection metric is inner mean AUC. Outer validation rows are used only for `predict_proba`.
- **Equal budget:** every model gets the **same number of inner configurations (6)**. Report wall-clock time per model.
- **Store pooled out-of-fold (OOF) probabilities** per row and model in the results JSON (today only 60 ROC points are kept, `evaluate.py:81-82`). Every test and calibration metric below needs them.
- **Statistics:**
  - Primary: paired **stratified bootstrap of the pooled-OOF AUC difference** (2,000 resamples, seed 42) with a 95% CI, as in R2 Sec. 8.
  - Secondary: Wilcoxon signed-rank on the 5 per-fold AUCs, reported with the caveat that the minimum attainable p is 0.0625 at n = 5 (C12 Sec. 7.5).
  - **Holm correction** across the comparisons inside each experiment.
  - Say "not significant" plainly when the CI includes 0.
- **Reporting:** only logged runs from `python -m backend.ml.quantum.benchmark`. Log every autonomous design decision in `DECISIONS.md`. Never quote `scratch/` numbers as results.

## Ranking

Score = (expected gain 1-5 × confidence 0-1) / cost in minutes. Costs come from our logged timings (VQC ~8-12 s per fold at 40 epochs, QSVM ~0.04 s, classical < 0.5 s; `results/benchmark.log`) and sandbox timings (`scratch/*.out`).

| Rank | ID | Experiment | Gain | Conf. | Cost (min) | Score |
|---|---|---|---|---|---|---|
| 1 | E1 | Significance tests + pooled OOF storage on the current models | 4 | 0.9 | 2 | 1.80 |
| 2 | E2 | Calibration and sensitivity at fixed specificity | 3 | 0.9 | 3 | 0.90 |
| 3 | E3 | QSVM bandwidth + C, nested | 4 | 0.7 | 5 | 0.56 |
| 4 | E4 | Entanglement and quantum-layer ablations | 3 | 0.7 | 10 | 0.21 |
| 5 | E5 | Simulator backend comparison (default.qubit vs lightning.qubit) | 1 | 0.9 | 5 | 0.18 |
| 6 | E7 | Explainability validation by feature ablation | 2 | 0.7 | 10 | 0.14 |
| 7 | E10 | Equal-budget nested CV of all 7 models | 5 | 0.9 | 35 | 0.13* |
| 8 | E8 | Noisy simulation that can actually fail (2-qubit noise, shots, Brier, gate counts) | 3 | 0.6 | 15 | 0.12 |
| 9 | E9 | Second dataset (method-level external validation) | 3 | 0.6 | 15 (+ approval) | 0.12 |
| 10 | E6 | VQC input scaling / data re-uploading / dressed variants, nested | 4 | 0.6 | 40 | 0.06* |
| 11 | E11 | Feature selection and qubit-count sweep | 3 | 0.5 | 25 | 0.06 |

\* **Execution order differs from score order.** E10 builds the nested harness that E3, E6 and E11 run inside, so build it right after E1 and E2: **E1 → E2 → E10 → E3 → E6 → E4 → E7 → E5 → E8 → E11 → E9**. E6 has a high expected gain but a long run. Its score is low because of cost, not doubt.

---

### E1. Significance tests and OOF storage on the current models
- **Hypothesis:** On the current (untuned) table, classical vs quantum AUC differences are not significant on breast cancer. The VQC on heart disease is significantly worse than logistic regression.
- **Evidence:** C12 Table 6 (no significant differences at n = 5); C14 Tables 5/9 (DeLong-type tests); R2 Sec. 8 (bootstrap); INFERENCES A1.
- **Design:** rerun the current config unchanged, storing OOF probabilities. Compare every model with logistic regression (6 comparisons per dataset, Holm).
- **Metrics / test:** pooled-OOF AUC difference with bootstrap CI; Wilcoxon on per-fold AUC.
- **Files:**
  - `evaluate.py` (`cross_validate` returns per-row OOF scores and fold ids).
  - `benchmark.py` (writes them; summary table gets a "vs LogReg ΔAUC [95% CI]" column).
  - New `backend/ml/quantum/stats.py` (bootstrap, Wilcoxon, Holm).
  - Tests in `backend/tests/`.
- **Cost:** about 2 min of statistics on top of a full benchmark run (~7 min, needed anyway).
- **Success:** CIs and p-values reported for all 12 comparisons.
- **Stopping rule:** none, since it's a one-off.
- **Pitfalls:** pool OOF scores only from outer folds. Don't bootstrap fold means. Use the same OOF rows for both models in each pair.

### E2. Calibration and decision utility
- **Hypothesis:** On pooled OOF predictions, the VQC (and QSVM) Brier and ECE are worse than logistic regression's. Sensitivity at 90% specificity orders models differently from accuracy.
- **Evidence:** C14 Table 6 (VQC ECE 0.175); T3-3; T3-2 (TRIPOD+AI). Sandbox H4: VQC Brier 0.189 / 0.220 vs LR 0.092 / 0.140 on 2 heart folds. Platt scaling did not help.
- **Design:** from the E1 OOF probabilities, compute Brier, ECE (10 equal-width bins, pooled), a reliability plot, and sensitivity at specificity 0.90 and 0.95. Optional arm: Platt scaling fitted by inner 3-fold CV on training folds only.
- **Metrics / test:** Brier difference vs LR with bootstrap CI; sensitivity at fixed specificity with bootstrap CI.
- **Files:**
  - `evaluate.py` (`binary_metrics` adds Brier and sensitivity at fixed specificity).
  - `benchmark.py` (reliability plot `results/calibration_<dataset>.png`).
  - `src/pages/QuantumLab.tsx` (threshold slider over the stored ROC points, no retraining; idea from A2).
- **Cost:** about 3 min.
- **Success:** pooled calibration metrics for all models on both datasets, with CIs.
- **Stopping rule:** if Platt scaling changes Brier by under 0.005 on both datasets, drop it.
- **Pitfalls:** never choose a threshold or calibration on validation rows (A3's admitted mistake). Per-fold ECE at ~61 rows is noise, so pool it.

### E3. QSVM bandwidth and C (nested)
- **Hypothesis:** A bandwidth factor s that scales all data-dependent phases of the ZZ map (single 2·s·x, pair 2·s²·(π−x_i)(π−x_j)), chosen with C in the inner CV, raises QSVM pooled-OOF AUC on both datasets.
- **Evidence:** C12 Sec. 4.2, 7.1, Table 7; C14 (untuned QSVM 0.727). Sandbox H1: Δ AUC +0.084, −0.013 (heart) and +0.009, +0.065 (breast); s ∈ {0.1, 0.2} chosen every time; kernel mean off-diagonal 0.04-0.10 at s = 1 (too concentrated).
- **Design:** inner grid s ∈ {0.1, 0.2, 0.35, 0.5, 0.75, 1.0} with C fixed at 1 (6 configs, the equal budget). Control arm: C ∈ {0.01, 0.1, 1, 10, 100, 1000} at s = 1 (6 configs), to separate the bandwidth effect from regularisation. Report the chosen s per fold and the kernel spectrum (effective rank, mean off-diagonal).
- **Metrics / test:** pooled-OOF AUC, tuned vs untuned and tuned-s vs tuned-C. Bootstrap CI, Holm (2 comparisons × 2 datasets).
- **Files:**
  - `qkernel.py`: `bandwidth` parameter on `zz_feature_map` / `QuantumKernelSVM`, defaulting to 1.0 so current results reproduce exactly. The sandbox asserted s = 1 equals today's kernel.
  - `evaluate.py`: the grid.
  - `explain.py`: optional KTA-based selection reuses `kernel_alignment`.
- **Cost:** about 5 min (kernels cost ~0.4 s per fold for the whole grid).
- **Success:** the CI of tuned-s minus untuned excludes 0 on at least one dataset and is not significantly negative on the other.
- **Stopping rule:** if the C-only arm matches the s arm (|Δ| < 0.005), report "regularisation, not bandwidth" and stop. No further feature-map variants this round.
- **Pitfalls:** tune on inner folds only. Don't widen the grid after seeing outer results. Keep reps = 2 and the gate set fixed (the hardware-compatibility claim depends on it).

### E4. Entanglement and quantum-layer ablations
- **Hypothesis:** Removing the CNOT ring (with all-qubit readout) or replacing the hybrid's quantum layer with a classical `Linear(6,6)+tanh` doesn't lower AUC significantly.
- **Evidence:** C13 Sec. V.3, Fig. 13. Sandbox H2/H2b: re-uploading with all-Z 0.895 / 0.843 vs no-CNOT 0.921 / 0.885; hybrid 0.953 / 0.808 vs classical replacement 0.951 / 0.869.
- **Design:** variants `vqc_allz`, `vqc_allz_noent`, `hybrid_qnn`, `hybrid_classical`, each trained exactly like its parent (same epochs, learning rate, batch). Parameter counts reported. **Not** `<Z0>` without CNOTs, which is a light-cone artefact.
- **Metrics / test:** pooled-OOF AUC, paired with each parent. Bootstrap CI, Holm (2 pairs × 2 datasets).
- **Files:**
  - `vqc.py` (`entangle`, `readout` options).
  - `hybrid_qnn.py` (`quantum=False` option).
  - `evaluate.py` (`build_model` names).
- **Cost:** about 10 min.
- **Success:** a clear, reported answer either way.
- **Stopping rule:** a single run; no re-runs with other seeds.
- **Pitfalls:** match epochs and training procedure. Report the parameter-count difference (91 vs 73 for the hybrid). Don't present "no drop" as proof that quantumness is useless; say "not detectable at this n".

### E5. Simulator backend comparison
- **Hypothesis:** `lightning.qubit` (adjoint) gives the same predictions as `default.qubit` (backprop) to 1e-8, and is not faster at 6 qubits on this laptop.
- **Evidence:** T4-1. Sandbox H5: 6 qubits, 200 rows, `default.qubit` 0.012 s forward and 0.010 s backward; `lightning.qubit` (per-sample loop) 0.60 s and 0.21 s. B6 (TorchQuantum) is not a candidate (Python 3.7-3.9 per its README).
- **Design:** one VQC fold, the same weights, both devices. Max absolute difference of outputs, and timing at 4/6/8/10 qubits. Also a batched lightning run, if PennyLane 0.45 supports broadcasting there.
- **Metrics / test:** numerical equality; timing table (no significance test).
- **Files:** `vqc.py`, `qkernel.py` (a `device` argument threaded from config; see `docs/SIMULATOR_PLAN.md`).
- **Cost:** about 5 min.
- **Success:** equality confirmed; a default device chosen from data.
- **Stopping rule:** single run.
- **Pitfalls:** compare like with like (batched vs looped). Warm up before timing.

### E6. VQC input scaling, data re-uploading and dressed variants (nested)
- **Hypothesis:** A trainable per-feature input scale lifts the heart-disease VQC, and the lift is not explained by extra parameters.
- **Evidence:** C13 Sec. II.3 (trainable scaling in re-uploading); C9 Table 6 (re-uploading 86.84% vs 86.67%); B5 (DataReuploadingClassifier). Sandbox H2/H2b (heart, 2 folds): base 0.783 / 0.653; scale-only 0.940 / 0.847; re-uploading + scale 0.948 / 0.832.
- **Design:** four fixed variants:
  1. `vqc` (base, 26 parameters).
  2. **`vqc_3layer`** (parameter-matched control: 3 layers × 6 × 2 + 2 = 38).
  3. `vqc_scale` (38 parameters).
  4. `vqc_reupload_scale` (38 parameters).

  Each gets the same inner grid: learning rate {0.01, 0.05, 0.1} × epochs {20, 40} (6 configs). The dressed-circuit comparison is E4's hybrid pair.
- **Metrics / test:** pooled-OOF AUC; each variant vs base and vs `vqc_3layer`. Bootstrap CI, Holm (6 comparisons per dataset).
- **Files:** `vqc.py` (`input_scaling`, `reupload` options; defaults reproduce today); `evaluate.py`.
- **Cost:** about 40 min (4 variants × 6 configs × 3 inner × 5 outer × ~2-10 s, both datasets).
- **Success:** the CI of `vqc_scale` minus `vqc_3layer` excludes 0 on heart disease.
- **Stopping rule:** if scale vs the parameter-matched control is not significant on heart disease, stop and report "capacity, not scaling".
- **Pitfalls:**
  - Don't re-tune after seeing outer folds.
  - The categorical-code issue (INFERENCES 3.1) is a confounder. Record which features were selected per fold.
  - Keep `<Z0>` vs all-Z readout fixed within a comparison.

### E7. Explainability validation by feature ablation
- **Hypothesis:** Removing the top-2 permutation-ranked features and retraining lowers AUC more than removing 2 random features (mean of 5 random draws). This holds for logistic regression and the best quantum model.
- **Evidence:** B8 (removal check, qualitative only); C14 Table 15 (surrogate fidelity as another check). We already compute permutation importance and SHAP (`explain.py:19-37`).
- **Design:** inside each outer fold, rank features by permutation importance on an inner split of the training fold. Refit at k = 4 qubits without the top 2, and without 2 random features. Compare outer AUC.
- **Metrics / test:** ΔAUC(top) − ΔAUC(random), with bootstrap CI.
- **Files:** `explain.py` (`ablation_check`); `benchmark.py` (adds to `explain` in the JSON).
- **Cost:** about 10 min.
- **Success:** the CI excludes 0 for at least LR. Otherwise report that the importances don't validate.
- **Stopping rule:** single run.
- **Pitfalls:** rank on training data only (ranking on validation rows leaks). Hold k constant across arms.

### E8. Noisy simulation that can actually fail
- **Hypothesis:** With two-qubit depolarising noise on every CNOT (p₂ ∈ {0.005, 0.01, 0.02}), one-qubit p₁ = p₂/10, and 1,000 shots, VQC Brier rises materially and AUC falls. Single-qubit-only noise leaves AUC unchanged (control).
- **Evidence:**
  - INFERENCES 3.6: AUC is invariant to a monotone shrink.
  - Sandbox H5 (single-qubit noise): AUC 0.783 at p = 0 to 0.1, Brier 0.189 to 0.205; 1,000 shots gave AUC 0.777.
  - C12 Sec. 4.4 (p₁q = 1e-3, p₂q = 1e-2).
  - C14 Table 11.
- **Design:** models trained noiselessly. Noisy evaluation on `default.mixed` at 6 qubits through `qml.add_noise` (or explicit channels) on outer validation rows. Report gate counts from `qml.specs` (VQC: 42 gates incl. 12 CNOT, depth 17; QSVM map: 54 gates incl. 20 CNOT, depth 25). QSVM noise via noisy kernel estimation is optional and costlier.
- **Metrics / test:** AUC and Brier vs noise level (curve, bootstrap CI at each point).
- **Files:** new `backend/ml/quantum/noise.py` (noise-model builder), `vqc.py` (device injection), `benchmark.py` (`--noise` flag); see `docs/SIMULATOR_PLAN.md`.
- **Cost:** about 15 min (~25-30 ms per sample per noise level at 6 qubits; 2 datasets × 4 levels × 5 folds).
- **Success:** a curve that's informative either way, with the single-qubit control shown.
- **Stopping rule:** don't train under noise this round (8-qubit density matrices took 28 s per 200-row forward pass).
- **Pitfalls:** don't call the result "hardware robustness". State the noise model exactly. A transpiled count on a named device needs the qiskit MCP (reconnect first).

### E9. Second dataset: method-level external validation
- **Hypothesis:** The pipeline's ranking on breast cancer (WDBC) replicates when the whole pipeline is re-run on the Wisconsin Original cohort (n = 683, 9 ordinal features), as C14 did.
- **Evidence:** C14 Sec. 2.1-2.2, Table 8 (method-level external validation; VQC 0.983 vs RBF 0.986 externally). C12 Table 2 lists other public UCI candidates (Pima diabetes, ILPD-like cohorts).
- **Design:** add a dataset to `data.py` with the same 5-fold, 200-row protocol and the E10 harness. Label it "method-level replication, not external validation of a frozen model".
- **Metrics / test:** pooled-OOF AUC and E1 tests.
- **Files:** `data.py` (new loader + `DATASETS` entry with licence), `benchmark.py`.
- **Cost:** about 15 min. **Needs your approval** to download the UCI file (as `data.py` already does for heart disease).
- **Success:** the table is produced. The ranking is reported, whatever it is.
- **Stopping rule:** one extra dataset this round.
- **Pitfalls:** no feature overlap with WDBC, so no frozen-model transfer. Check the licence (UCI CC BY 4.0) before adding.

### E10. Equal-budget nested CV of all 7 models (harness)
- **Hypothesis:** With equal 6-configuration inner tuning, the classical-quantum gap on breast cancer stays non-significant, and the heart-disease ranking may change.
- **Evidence:** C13 Sec. IV; C12 Sec. 4.6; T3-1; INFERENCES 3.3.
- **Design:** per-model 6-configuration grids, inner 3-fold:

  | Model | Grid |
  |---|---|
  | LogReg | C ∈ {0.01, 0.1, 1, 10, 100, 1000} |
  | RBF-SVM | C {0.1, 1, 10} × γ {scale, 0.1} |
  | RF | depth {3, 6} × trees {100, 300} × max_features {sqrt, None}, trimmed to 6 |
  | MLP | hidden {8, 16, 32} × alpha {1e-4, 1e-2} |
  | QSVM | E3 grid |
  | VQC | lr {0.01, 0.05, 0.1} × epochs {20, 40} |
  | Hybrid | same as VQC |

  Non-nested best-of-grid is also recorded, to measure the T3-1 optimism.
- **Metrics / test:** pooled-OOF AUC per model; E1 tests; optimism (non-nested minus nested).
- **Files:** `evaluate.py` (`fit_and_score` wraps `Pipeline(pre, model)` in `GridSearchCV`, see INFERENCES Q1); `baselines.py` (grids); `benchmark.py` (`--tune` flag, default off so old results reproduce).
- **Cost:** about 35 min for both datasets (quantum NN models dominate).
- **Success:** the nested table plus the optimism column.
- **Stopping rule:** grids frozen before running. No second round of grid edits this cycle.
- **Pitfalls:** the preprocessor goes inside the inner loop. Same inner folds for every model. Don't let any model's grid grow beyond 6.

### E11. Feature selection and qubit-count sweep
- **Hypothesis:** The best k (4, 6 or 8) and method (MI, PCA, RFECV-LR) differ between classical and quantum models. The current k = 6 MI choice is not optimal for the heart-disease VQC.
- **Evidence:** C12 Sec. 6.2 (k has epsilon² 0.278, larger than kernel family); C14 Table 13 (RFECV + stability, Jaccard 0.83); C10; R1 II-B; A4.
- **Design:** k ∈ {4, 6, 8} × {MI, PCA}, selected inside the inner CV (6 configs, so it shares the equal budget). Record selected features per fold, plus a Jaccard stability index. Optional: one-hot vs ordinal coding for heart disease's `cp`, `thal`, `slope` (C9 one-hot encoded).
- **Metrics / test:** pooled-OOF AUC at the chosen k vs fixed k = 6; bootstrap CI.
- **Files:** `preprocess.py` (`rfecv` method); `benchmark.py` (k in the grid; `--n-qubits` already allows 4-8, `benchmark.py:183`).
- **Cost:** about 25 min (8-qubit statevector circuits ~0.07 s per 200-row forward pass).
- **Success:** the chosen k and stability reported per model.
- **Stopping rule:** if the chosen k equals 6 in at least 4 of 5 folds for every model, keep 6 and stop.
- **Pitfalls:** one qubit per feature must hold, so k changes circuit width. Report depth and gate count per k. MI selection must stay inside the training fold.

## What is deliberately not in this round
Full kernel-target-alignment training (≈2,000× cost, C12), QuantumNAS search (B7), TorchQuantum (B6; Python range), stacked kernel ensembles (R2), QCCNN imaging layers (C11), and any real-hardware run (needs an IBM account and approval).

---

## Extension for master prompt v2 (P1): experiments E12-E19

Same shared protocol, upgraded for the multi-dataset round (docs/PREREGISTRATION.md governs where it conflicts):
- **Repeats.** Repeated stratified 5-fold, with the repeat count fixed for every model in PREREGISTRATION.
- **Development and confirmation.** Design decisions are made on the 4 development datasets only (Cleveland, WDBC, Pima, ILPD); confirmation datasets are run once, unchanged.
- **Tests.** Per dataset: corrected resampled t-test (Nadeau-Bengio) with Holm. Across datasets: Friedman, then Wilcoxon-Holm and a CD diagram.
- **Budget.** At most two design iterations per experiment.

| ID | Experiment | Source | Hypothesis (direction) | Design | Metric / test | Cost | Stopping rule |
|---|---|---|---|---|---|---|---|
| E12 | Kernel effective-rank control | G1, G7, H6 | The tuned QSVM does **not** beat an RBF SVM whose gamma matches the QSVM kernel's effective rank | Per outer fold: compute the tuned QSVM kernel's effective rank on training rows; binary-search RBF gamma to match it; same C grid as qsvm_c | Pooled AUC difference, corrected t per dataset; Wilcoxon across dev datasets | < 5 min | If rank-matched RBF >= QSVM on all dev datasets, report "explained by kernel rank" and stop |
| E13 | Bandwidth by KTA vs by inner CV | G2, H7, H13 | Choosing s by maximal centred KTA on training rows gives AUC within 0.01 of inner-CV selection | Same s grid; selection criterion differs; also time-boxed (<= 60 s/fold) gradient KTA on a 150-row subsample | AUC difference + wall time | < 10 min | Keep KTA selection only if within 0.01 and > 3x cheaper |
| E14 | SHAP top-k feature subsets (k = 5, 6, 7) | G4, C12 | SHAP-ranked selection (inside training folds) >= MI selection at k = 6 for LogReg and the VQC | SHAP of a tuned LogReg on inner folds ranks raw features; qubits = k | AUC, corrected t | ~30 min | Keep only if it improves the dev set mean AUC by >= 0.005 for the VQC without hurting LogReg |
| E15 | Residual head [x, q(x)] vs equal classical head [x, tanh(Wx)] | G10 | The residual quantum head does **not** beat the equal classical head | Same head size; parameter counts reported; tuned with the VQC grid | AUC, corrected t | ~25 min | Single run on dev; confirm once |
| E16 | Classical trig twin of the re-uploading VQC + surrogate fidelity | G11, H9, H10 | The twin matches the re-uploading VQC (CI of difference includes 0); a trig surrogate fitted to the trained VQC reaches R² > 0.9 on validation rows | Twin: scaled sin/cos features per layer, small head, ~38 params; surrogate: ridge on trig features of degree <= L per feature plus pairwise products | AUC; surrogate R² | ~20 min | Report either way |
| E17 | Learning curves N = 10, 20, 50, 100, 200 | G3, G9 | Quantum curves lie on or below the tuned LogReg and the parameter-matched MLP at every N | 10 repeated stratified draws per N; fixed validation split per repeat; dev datasets | Mean AUC +- CI per N | ~40 min | No early stop (descriptive) |
| E18 | Noise-aware circuit choice | G5 | With p2 = 0.01 two-qubit noise, the no-CNOT circuit degrades less (Brier) than the ring circuit | Trained weights re-run on default.mixed; 3-dataset subset | Δ Brier, Δ AUC vs exact with bootstrap CI | ~15 min | Descriptive; never presented as robustness |
| E19 | Data-complexity diagnostics vs quantum gap | G8, H6, H8 | No single diagnostic correlates significantly with the quantum-minus-best-classical AUC gap | Per dataset: n, d, class balance, covariance effective dimension, kernel effective dimension and off-diagonal mean (tuned QSVM kernel), compression ratio | Spearman ρ with bootstrap CI across 12+ datasets | minutes | Descriptive |

The D4 model list for the multi-dataset round: LogReg, RBF-SVM, RandomForest, MLP, **HistGradientBoosting**, tuned-bandwidth QSVM, VQC and the best development-set VQC variant, hybrid QNN, **residual head (E15)**, and controls: **parameter-matched MLP**, **classical twin (E16)**, VQC without the CNOT ring, hybrid with a classical layer.
