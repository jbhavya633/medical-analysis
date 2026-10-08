# Pre-registration: multi-dataset benchmark (SIH26139, master prompt v2)

Committed before any multi-dataset model result was computed or viewed. Results on the development datasets Cleveland and WDBC from the earlier two-dataset round (docs/PROGRESS.md: E3 and the running E6/E4 jobs) exist and informed this plan. Those two datasets are therefore in the development set by design. No model has been fitted on any confirmation dataset when this file is committed; the commit hash is recorded in docs/PROGRESS.md (D3).

## 1. Datasets
Rules and candidate list: docs/KAGGLE_DATASETS.md. Kaggle credentials are not present on this machine, so only the built-in, UCI and OpenML sources are used. Kaggle-only candidates (Stroke, Framingham, Cardiovascular 70k, Lung cancer survey) are "not run: credentials not present". Breast Cancer Coimbra (116 rows) fails the >= 150-row rule. Statlog (Heart) overlaps Cleveland and is a sanity check only, outside the statistics.

| Set | Datasets |
|---|---|
| Development (design decisions allowed) | Heart Disease Cleveland, Breast Cancer Wisconsin Diagnostic (WDBC), Pima Indians Diabetes, Indian Liver Patient (ILPD) |
| Confirmation (run once, unchanged, reported as they come) | Heart Failure Clinical Records, Chronic Kidney Disease, Cervical Cancer (Biopsy), Parkinson's (voice), Early Stage Diabetes Risk, Hepatitis, Mammographic Mass, Thyroid (sick), Differentiated Thyroid Cancer Recurrence |

If a confirmation dataset fails the acceptance or leakage checks in P3, it is dropped and recorded with the reason; the minimum is 12 datasets in total. No confirmation dataset may be moved into the development set.

## 2. Protocol
- **Seed and folds.** Seed 42. Repeated stratified 5-fold CV with **R = 3 repeats** for every model (repeat r uses `StratifiedKFold(5, shuffle=True, random_state=42 + r)`). Pre-registered fallback if the projected wall time exceeds 10 hours on this laptop: R = 2 for every model (never different R per model).
- **Training subsample.** Each outer training fold is stratified-subsampled to at most 200 rows (seed 42 + r), identical for every model.
- **Features and qubits.** Preprocessing (median/most-frequent imputation, one-hot or ordinal encoding as declared in the registry, standardisation, selection to k = 6 features by mutual information, scaling to [0, π]) is fitted inside training folds only. Every model in the main comparison sees the same 6 features (like-for-like, as in v1). Qubits = 6. The qubit-count and feature-selection sweep (E11, E14) is a separate experiment. As a secondary reference only (not in the main statistics), LogReg and HistGradientBoosting are also run on all features.
- **Tuning.** Nested CV: inner `StratifiedKFold(3, shuffle=True, random_state=42)` on the outer training fold only; **6 configurations per model** (equal budget); selection metric is inner mean AUC.

## 3. Models (D4)
LogReg, RBF-SVM, RandomForest, MLP, HistGradientBoosting; QSVM with tuned bandwidth; VQC (base) and the best development VQC variant (selection rule in section 6); hybrid QNN; residual head [x, q(x)]. Controls: parameter-matched MLP, classical trig twin of the re-uploading VQC, VQC without the CNOT ring, hybrid QNN with a classical layer, residual head with an equal classical block, untuned QSVM (s = 1).

## 4. Metrics
- **Primary:** ROC AUC, per outer fold (for paired tests) and on pooled out-of-fold predictions per repeat (for intervals and plots).
- **Secondary:** balanced accuracy, sensitivity at 95% specificity (and at 90%), Brier score, ECE (10 equal-width bins, pooled), calibration slope and intercept, MCC, net benefit (decision curve) at thresholds 0.05-0.5, train time per fold (including tuning) and predict time per sample.

## 5. Statistical tests
- **Per dataset:** corrected resampled t-test (Nadeau & Bengio) on the R x 5 paired fold AUC differences, variance inflation 1/(R*5) + n_test/n_train. Holm correction across the pre-specified comparisons of that dataset (section 6).
- **Across datasets:** Friedman test on per-dataset mean AUC ranks of all main models; if p < 0.05, a Nemenyi critical-difference diagram. Pre-specified pairs use Wilcoxon signed-rank across datasets with Holm correction. Effect sizes: median ΔAUC with a bootstrap 95% CI across datasets; win/tie/loss counts, where "tie" means the per-dataset corrected test is not significant.
- **Alpha:** 0.05, two-sided unless stated.

## 6. Hypotheses (direction), decision rules and stopping rules
| # | Hypothesis | Test | Expected (from A1-A13) |
|---|---|---|---|
| P-H1 (primary) | Tuned-bandwidth QSVM vs tuned LogReg: **no significant difference** across datasets | Wilcoxon-Holm, median ΔAUC CI | Parity |
| P-H2 | The best classical model's Friedman mean rank is at least as good as every quantum model's | Friedman + CD | Classical ranks first or tied |
| P-H3 | Tuned QSVM **>** untuned QSVM (s = 1) across datasets (replicates E3) | one-sided Wilcoxon | Holds |
| P-H4 | Best VQC variant **=** its parameter-matched control (3-layer VQC or parameter-matched MLP) | Wilcoxon-Holm | No significant difference |
| P-H5 | VQC without the CNOT ring **=** VQC with ring (all-qubit readout) | Wilcoxon-Holm | No significant difference |
| P-H6 | Hybrid QNN **=** hybrid with a classical layer | Wilcoxon-Holm | No significant difference |
| P-H7 | Residual quantum head **=** residual head with an equal classical block | Wilcoxon-Holm | No significant difference |
| P-H8 | Re-uploading VQC **=** its classical trig twin | Wilcoxon-Holm | No significant difference |
| P-H9 | Quantum models have **higher (worse)** pooled Brier than LogReg | Wilcoxon on Brier | Holds for the VQC |
| P-H10 | No data-complexity diagnostic correlates significantly with the quantum-minus-best-classical AUC gap | Spearman with bootstrap CI | No significant correlation |
| P-H11 | Two-qubit-gate depolarising noise degrades Brier monotonically with p2 | Descriptive curve, 3-dataset subset | Degradation (not "robustness") |

**Development-to-confirmation rule.** A method change (VQC variant, feature selection, bandwidth-selection rule, residual head) is kept only if it improves the development-set mean AUC by >= 0.005 and loses no more than 0.01 on any development dataset. It is then reported unchanged on the confirmation set, whatever the outcome. At most two design iterations per experiment.

**VQC variant selection.** Among vqc, vqc_3layer, vqc_scale and vqc_reupload_scale, the confirmation run includes the base VQC plus the variant with the highest development mean AUC, if it meets the rule above. Otherwise only the base VQC and its parameter-matched control are run.

**Compute fallbacks, in this order and only if needed:** R = 3 to 2; VQC/hybrid epochs grid {20, 40} to {20, 40} with lr {0.05, 0.1} only (still 6 configs, by adding batch size {16, 32}); drop the most expensive confirmation dataset while keeping >= 12 datasets. Each use is logged in DECISIONS.md.

## 7. Leakage audit
Outer test rows never touch tuning, feature selection, scaling, imputation or encoding: all live inside the per-fold Pipeline. A unit test asserts that permuting the outer-validation labels leaves the fitted pipeline unchanged. Any failure invalidates the affected results; they are re-run after the fix.

## 8. Reporting
Everything is simulator-only and on public datasets. Claims follow the claim policy of docs/MASTER_PROMPT_V2.md and are generated from results/*.json; `scripts/check_numbers.py` fails on any mismatch.
