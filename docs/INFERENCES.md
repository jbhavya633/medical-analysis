# Inferences (SIH26139): cross-source synthesis

Written 2026-10-08 from `docs/LEARNING_LOG.md` (source IDs refer to entries there). Confidence labels: HIGH = several strong sources agree and our own sandbox does not contradict them; MEDIUM = one strong source or several weak ones; LOW = suggestive only. Sandbox numbers (scratch/) come from 2 of our 5 folds at 15 epochs: **exploratory, n too small for conclusions**. They decide what to test next, not what to report.

## 1. Where sources agree

| # | Agreement | Sources | Confidence |
|---|---|---|---|
| A1 | On small tabular medical data, quantum models reach **parity at best**. No controlled study shows a significant win. | C12 Table 6 (0 of 29 significant), C13 Sec. V.1, C14 Tables 4/8, R1 Sec. III-A, R2 Table 8, A3 README, A1 README table | HIGH |
| A2 | **Dataset choice dominates model choice.** | C12 Sec. 6.2 (dataset epsilon^2 0.73 vs kernel 0.089); C13 Fig. 7 (hyperparameters swing accuracy from chance to near perfect) | HIGH |
| A3 | **Tuning effort decides rankings.** Unequal tuning invalidates comparisons, and estimates must come from nested CV. | C13 Sec. IV; C12 Sec. 4.6; T3-1 (null-data bias); C14 (Optuna for classical only, QSVM untuned: AUC 0.727) | HIGH |
| A4 | **Angle (X/Y-rotation) encoding beats amplitude encoding**, and a Z-rotation embedding read out in Z carries no information. | C9 Table 6; C13 Sec. I/II; C14 Table 10 | MEDIUM-HIGH |
| A5 | **Input scale / bandwidth matters for quantum kernels and circuits**, and fixed-scale maps give poorly shaped kernels. | C12 Sec. 4.2, 7.1, Table 7 (spectra too flat or rank-1); C13 Sec. II.3 (fixed input scaling, trainable scaling in re-uploading); our sandbox H1/H2 | MEDIUM-HIGH |
| A6 | **Entanglement is often not what helps**: separable or no-CNOT variants match. | C13 Sec. V.3, Fig. 13; our sandbox H2b | MEDIUM |
| A7 | **Quantum models are poorly calibrated** compared with classical ones. | C14 Table 6 (VQC ECE 0.175, slope 4.729); T3-3; sandbox H4 (VQC Brier worst) | MEDIUM |
| A8 | Honest reporting (admitting no advantage, admitting optimistic thresholds) is what the strongest same-problem projects do. | A1, A3, A7 READMEs; C14 Sec. 4 | HIGH (as a norm) |

## 2. Where sources conflict, and the likely reason

| Conflict | Quantum looks better in | Controlled benchmarks say | Likely reason |
|---|---|---|---|
| Heart disease | C9: best VQC 86.84-87.46% vs NN 86.67%; C10: QSVM 97.83% vs 94.02% | C12: classical wins on heart disease too (Table 5); our VQC trails at 0.755 AUC | C9 selects models and early-stops on the **test set**. C10 couples a different feature subset with the quantum model, reports one split and has internal inconsistencies. Both lack significance tests. |
| "Quantum better at low data" | C9 Table 7 (1-layer QNN leads at 10-50% of data by 0.5-2 points) | C13 Sec. V.2: no systematic scaling advantage | Margins are inside run-to-run noise. Only one dataset and no tests. |
| QCCNN on WDBC | C11: 96.2% mean vs LR 91.2% | C14: LR-family and RBF at 0.99+ AUC; our LR AUC 0.979 | C11's classical baselines are weak (LR trained with Adam at lr 0.01). It reports best iterations and no variance. |
| QSVM strength | A1 (MI-adaptive QSVM 0.767 AUC), C14 (0.727) | C12 + QKT: 0.968 BA on breast cancer | Untuned ZZ maps vs trained or tuned kernels: **bandwidth / scaling is the confounder**. |
| Noise robustness | C14 Table 11: VQC AUC flat at 0.992 up to p = 0.10; C12 hardware sometimes above simulator (Sec. 6.4) | No contrary source | Not a real conflict, but over-read: see 3.6. Single-qubit depolarising noise shrinks `<Z>` towards 0 by an almost uniform factor, which leaves the ranking (AUC) unchanged. Our sandbox reproduced this exactly (AUC 0.783 at every p). C12 itself calls "noise as regulariser" speculative at n = 60. |

## 3. Implications for our weak points

### 3.1 Heart-disease VQC (AUC 0.755, accuracy 0.667)
- **Inference:** The weakness is mainly an **input-scaling / encoding problem**, not a lack of depth or entanglement. Our MI selection picks categorical and ordinal codes on heart disease (`sex, cp, oldpeak, slope, ca, thal`), and `preprocess.py:29` min-max maps them onto [0, pi]. A binary `sex` then becomes RY(0) or RY(pi), a full bit flip. With `<Z0>` readout, one learned scalar per model (`vqc.py:118`) cannot rescale per-feature angles.
- **Evidence:** C13 Sec. II.3 (trainable input scaling in re-uploading models), C12 Sec. 7.1, C9 (re-uploading helps a little). Sandbox H2 on 2 heart folds: base AUC 0.783 / 0.653; trainable input scale with no re-uploading 0.940 / 0.847; re-uploading 0.948 / 0.832. So the scale carries the gain.
- **Uncertainty:** 2 folds × 61 rows, 15 epochs, no tuning, and the variant adds 12 parameters (38 vs 26).
- **What would change it:** if, on all 5 folds with nested tuning of learning rate and epochs, the base VQC catches up with the scaled one (the gap would then be under-training), or if a parameter-matched control (base with 2 extra layers) closes the gap.

### 3.2 QSVM bandwidth
- **Inference:** Our ZZ map is over-rotated. The pair phase reaches ~19.7 rad, so the kernel is close to diagonal: mean off-diagonal 0.04-0.10 at s = 1 (sandbox H1), the "too concentrated" regime of C12 Table 7. A single bandwidth factor s, tuned in an inner CV, is the cheapest fix.
- **Evidence:** C12 Sec. 4.2, 7.1, Table 7; C14 (untuned ZZ 0.727 AUC); R2/A1 (untuned or adaptive maps weak). Sandbox H1 (4 folds across the two datasets): tuned AUC minus untuned AUC = +0.084, −0.013 (heart); +0.009, +0.065 (breast). The chosen s was always 0.1-0.2, and the inner loop took 0.4 s per fold.
- **Uncertainty:** 1 of 4 folds got worse. C also changed (C = 10 in two folds), so part of the gain may be C, not s.
- **What would change it:** if, over 5 folds, tuning C alone at s = 1 recovers most of the gain (then the cause is regularisation, not bandwidth), or if the paired test shows no difference.

### 3.3 Equal tuning
- **Inference:** Right now **no** model is tuned (classical defaults at `baselines.py:13-22`; quantum defaults at `evaluate.py:22-29`). So the comparison is fair in budget (zero for all) but uninformative. Tuning only the quantum side would be unfair in the other direction.
- **Evidence:** C13 Sec. IV, C12 Sec. 4.6, T3-1, C14 (unequal Optuna budget).
- **Uncertainty:** what "equal budget" means across model families. The defensible choice is the same number of inner configurations and the same inner folds for every model, with wall-clock time reported.
- **What would change it:** none of the sources argues against equal budgets. It is a design requirement.

### 3.4 Ablation (is "quantumness" doing anything?)
- **Inference:** Expect the hybrid QNN's quantum layer to be replaceable by a classical layer of the same width, and the CNOT ring to be removable, both at no significant cost. Report this honestly. Our current `noent` sandbox variant with `<Z0>` readout is a **light-cone artefact** (only feature 0 can reach the output), not an ablation. A fair ablation needs all-qubit readout.
- **Evidence:** C13 Sec. V.3, Fig. 13. Sandbox: hybrid 0.953 / 0.808 vs classical replacement 0.951 / 0.869; re-uploading with all-Z 0.895 / 0.843 vs the same without CNOTs 0.921 / 0.885.
- **Uncertainty:** 2 folds. Hybrid fold 1 shows a 0.06 gap, which is within noise at n = 61.
- **What would change it:** a significant drop when removing entanglement over 5 folds and both datasets.

### 3.5 Calibration
- **Inference:** Report Brier and ECE on **pooled out-of-fold** predictions (per-fold ECE at about 61 rows is unstable), plus sensitivity at fixed specificity. Post-hoc Platt scaling is unlikely to fix the VQC, because its problem is discrimination, not miscalibration.
- **Evidence:** C14 Table 6; T3-3. Sandbox H4 (heart): VQC Brier 0.189 / 0.220 vs LR 0.092 / 0.140; Platt via inner 3-fold gave 0.196 / 0.219 (no gain) at 2-3x training cost. Classical per-fold ECE was also 0.11-0.15, which shows how noisy small-n ECE is.
- **Uncertainty:** Platt scaling might help the better-discriminating, re-scaled VQC. Isotonic calibration was not tried (too few rows).
- **What would change it:** pooled-OOF reliability curves showing systematic over-confidence that Platt scaling fixes.

### 3.6 Noise
- **Inference:** "AUC is robust to depolarising noise" is nearly **true by construction** for a `<Z>` readout followed by a monotone link, so it must not be presented as a hardware-readiness result. Meaningful noise tests need (i) **two-qubit-gate noise** and amplitude damping (not just single-qubit depolarising), (ii) **finite shots**, and (iii) **training under noise** or calibration-sensitive metrics (Brier). Our real contribution would be the gate counts (VQC 42 gates incl. 12 CNOT, depth 17; QSVM map 54 gates incl. 20 CNOT, depth 25; `qml.specs`) plus a transpiled count on a named device.
- **Evidence:** sandbox H5 (AUC 0.783 at p = 0 to 0.1, Brier 0.189 to 0.205; 1000 shots: AUC 0.777); C14 Table 11 (the same flat pattern); C12 Sec. 4.4, 6.4 (hardware at 3-5 qubits only).
- **Uncertainty:** we haven't modelled 2-qubit noise or readout error yet. Qiskit Aer isn't installed, and the qiskit MCP was disconnected during this run.
- **What would change it:** a noise model with CNOT error at realistic device rates that changes rankings or AUC materially.

## 4. Techniques too expensive for the 60-minute-per-experiment budget, and cheaper variants

| Technique | Why too costly | Cheaper variant that keeps the idea |
|---|---|---|
| Quantum kernel training by kernel-target alignment, many parameters (C12: ~2,060x overhead, 13.6% converge) | Per-fold L-BFGS over many circuit parameters | **One bandwidth parameter s (plus C) chosen by inner CV, or by maximising centred KTA on the training fold.** Sandbox: 21 kernels per fold in 0.4 s. `explain.kernel_alignment` (`explain.py:40-44`) already exists. |
| QuantumNAS super-circuit search under device noise (B7) | Evolutionary search plus SuperCircuit training | **Gate-pruning ablation** of one CNOT ring, with gate counts from `qml.specs` |
| Large grid like C9 (46 QNN configs × 10 seeds, ~9,700 CPU-hours) | Combinatorial | **6 configurations per model**, 3 inner folds, 1 seed (seed 42 rule) |
| Noisy *training* on `default.mixed` at 8+ qubits | 28 s forward per 200 rows at 8 qubits (sandbox H5) | Noiseless training, **noisy evaluation** at 6 qubits (~25 ms per sample), plus a finite-shot run |
| Repeated CV for statistical power (C12 used 16 seeds) | ×5-16 cost for quantum models | Paired **bootstrap on pooled OOF predictions** (R2 Sec. 8) for quantum models; 5×5 repeated CV for classical models only, labelled as such |
| Stacked kernel ensembles (R2) | Inner OOF loop per base model | Defer; a 2-model stack only if the tuned QSVM ever beats logistic regression |

## 5. Claims we should NOT make
1. "Quantum advantage" or "quantum outperforms classical" on these datasets. No controlled source supports it (A1), and our own table contradicts it.
2. "Robust to hardware noise" based on depolarising-noise AUC (3.6).
3. "Hardware-compatible" without a transpiled gate count on a named device and a note that nothing ran on hardware.
4. "Quantum is better in low-data regimes" (C9's margins are untested and inside noise).
5. Any improvement found by choosing variants on our 5-fold table without nested CV (T3-1).
6. "Entanglement is essential" (C13 Sec. V.3; sandbox).
7. Comparisons of our numbers with C9, C10, C11, A1 or C14 numbers (different data, splits and protocols).
8. Anything from the sandbox runs in `scratch/` (2 folds, 15 epochs, exploratory).

## 6. The five strongest inferences
1. **Bandwidth / input scale is the main lever for both weak quantum models.** HIGH for the QSVM (C12 + sandbox, 3/4 folds up, cost ~0 s). MEDIUM for the VQC (sandbox 2/2 folds, unexplained by depth).
2. **Equal-budget nested tuning is a precondition for any claim.** HIGH (C12, C13, T3-1).
3. **Expect parity at best after tuning**, and report it as the honest result. HIGH.
4. **Entanglement and the quantum layer are probably not what drives performance**, so the ablations will likely show that. MEDIUM.
5. **Depolarising-noise AUC curves are uninformative.** Use Brier, two-qubit noise, finite shots and gate counts instead. HIGH (mathematical argument plus sandbox reproduction).

---

## 7. Checkpoint answers (citing our code)

**Q1. Where would nested-CV tuning go without touching outer test folds?**
Inside `fit_and_score`, `backend/ml/quantum/evaluate.py:48-65`. It receives only the outer training fold (`X_train`, `y_train`) and the validation fold (`X_val`) from `cross_validate` (`evaluate.py:72-74`). Replace `make_preprocessor(...).fit` and `build_model(...)` (lines 50-52) with a `GridSearchCV(Pipeline([("pre", make_preprocessor(...)), ("model", build_model(...))]), inner StratifiedKFold(3, seed 42))` fitted on `X_train, y_train` only. Then `X_val` is touched only by `predict_proba` (line 57). The preprocessor must be inside the inner pipeline, because MI selection is supervised. The same change automatically covers the hold-out path, which also calls `fit_and_score` (`benchmark.py:71`), and the learning curve (`evaluate.py:105`).

**Q2. Is feature selection fitted on training folds only?**
Yes. `make_preprocessor(n_qubits, method, seed).fit(X_train, y_train)` runs on the (subsampled) training fold (`evaluate.py:50`), and the validation fold is only transformed (`evaluate.py:51`). The pipeline is impute, scale, SelectKBest(mutual_info, random_state = seed), then MinMax to [0, pi] (`preprocess.py:23-30`), so imputation medians and scaling statistics are also training-only. The hold-out path does the same (`benchmark.py:71`, `:73`). One caveat: the SHAP background rows come from the training split (`benchmark.py:68-69`), which is correct.

**Q3. How are folds and the 200-row subsample kept identical across models?**
`StratifiedKFold(n_splits, shuffle=True, random_state=seed)` on the full `X, y` (`evaluate.py:72`) gives the same folds for every model, because the data and seed are fixed. Within each fold, `stratified_subsample(X[train_idx], y[train_idx], max_train, seed)` (`evaluate.py:73`; `data.py:73-78`) is a deterministic `train_test_split(train_size=n, stratify=y, random_state=seed)`. On breast cancer (~455 training rows) and heart disease (~242) the subsample always applies. MI selection is seeded (`preprocess.py:17`). Caveats: the learning curve uses a different 80/20 split (`evaluate.py:99`), and the hold-out models use `holdout_split` (`data.py:68-70`). Neither is comparable with the CV table.

**Q4. Which two baseline results are weakest, and what do the sources suggest?**
1. **VQC on heart disease**: accuracy 0.667 ± 0.048, AUC 0.755 ± 0.048 (`summary.md`, heart table). Sources suggest angle-encoding scale or re-uploading with trainable input scaling (C13 II.3, C9 Table 6) and possibly higher learning rates (C9). Sandbox: input scale carries most of the effect. Also worth checking how categorical codes are encoded (3.1).
2. **QSVM on heart disease**: accuracy 0.762 ± 0.040, AUC 0.836 ± 0.032 (the QSVM also trails on breast cancer, AUC 0.955). Sources suggest bandwidth-aware encoding, tuned C, and kernel-spectrum diagnostics (C12 Sec. 4.2, 7.1, Table 7). Full QKT is too costly (C12 Sec. 7.4). Sandbox: s = 0.1-0.2 chosen in all 4 folds.

**Q5. Three ways an "improvement" could be invalid in our setup**
1. **Selection on the outer folds.** Picking a variant (such as s = 0.1, or "re-uploading") because it scored best on our 5-fold table, then reporting that table. This is the Varma & Simon bias (T3-1). The sandbox findings in this document must be re-tested under nested CV, not adopted.
2. **Unequal budgets or confounded capacity.** Tuning only quantum models, or comparing a 38-parameter VQC against a 26-parameter base without a parameter-matched control, or training variants for different epochs (C13 Sec. IV). Also changing more than one thing at once (s and C in H1).
3. **Evaluation-data leakage through thresholds and preprocessing.** Choosing the decision threshold, Platt calibration or feature subset on validation rows (A3 admits this), or fitting any preprocessing outside the training fold (R2's global PCA). Reporting per-fold ECE at about 61 rows as if it were stable, or quoting a single-seed sandbox number, also counts.
