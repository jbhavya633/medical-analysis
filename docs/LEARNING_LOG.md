# Learning log (SIH26139): what each curated source teaches us

Written 2026-10-08 by Claude Code following `docs/LEARNING_PROMPT.md`. Every entry paraphrases the source in our own words; no code was copied, no repo was cloned, nothing was downloaded. Other papers' numbers are **not comparable** with ours; only numbers from running our own code count as evidence for us (see `docs/INFERENCES.md`).

Format per source: **(a)** technique, **(b)** claim and evidence, **(c)** strength of evidence, **(d)** transfer to our setting (6 qubits, <= 200 training rows, two small tabular medical datasets), **(e)** one testable hypothesis with metric, folds and expected cost.

Reading depth key: FULL = main text read; PARTIAL = page truncated, part read (section noted); ABSTRACT = abstract only; README = repo page read online, no code inspected; BLOCKED = could not open; UNVERIFIED = claim not checked against an opened source.

## Our baseline (verified)

Verified against `README.md` and `backend/ml/quantum/results/summary.json` / `summary.md` (run at commit 0413f33, config `seed 42, n_qubits 6, folds 5, max_train 200, epochs 40, mutual_info, default.qubit`).

| Dataset | Model | Accuracy | AUC |
|---|---|---|---|
| Breast cancer (n=569) | LogReg / RBF-SVM / RF / MLP | 0.926 / 0.921 / 0.921 / 0.926 | 0.979 / 0.978 / 0.977 / 0.981 |
| Breast cancer | QSVM / VQC / Hybrid QNN | 0.886 / 0.923 / 0.923 | 0.955 / 0.980 / 0.980 |
| Heart (n=303) | LogReg / RBF-SVM / RF / MLP | 0.815 / 0.805 / 0.841 / 0.818 | 0.901 / 0.902 / 0.900 / 0.888 |
| Heart | QSVM / VQC / Hybrid QNN | 0.762 / 0.667 / 0.792 | 0.836 / 0.755 / 0.861 |

Corrections to the prompt's description of our project (checked in code):
- The QSVM also trails on breast cancer (accuracy 0.886 vs 0.921-0.926; AUC 0.955 vs 0.977-0.981), not only on heart disease.
- The VQC reads out only `<Z0>` and passes it through a trainable scale and bias (`backend/ml/quantum/vqc.py:39`, `:118-122`); learning rate 0.05, batch 32.
- The hybrid QNN maps a Linear layer through `pi * sigmoid` into the circuit and reads `<Z>` on all qubits (`hybrid_qnn.py:20-21`); learning rate 0.03.
- The QSVM uses C = 1 and no bandwidth parameter (`qkernel.py:57`, `:70`). Its pair phase `2(pi-x_i)(pi-x_j)` reaches about 2*pi^2 ~ 19.7 rad (`qkernel.py:23`).
- **All models, classical included, see the same 6 mutual-information features scaled to [0, pi]** (`evaluate.py:50-51`). On heart disease the selected features are mostly categorical or ordinal codes (`sex, cp, oldpeak, slope, ca, thal` on scratch folds 0-1).

---

## T1 Quantum neural networks

### C9 Ghisoni et al., Sci Rep 2026, heart disease VQC vs NN - FULL (main text; supplement truncated)
https://pmc.ncbi.nlm.nih.gov/articles/PMC12852685/ (DOI 10.1038/s41598-025-33825-7; via PubMed/PMC)
- (a) They trained hundreds of VQC configurations (angle vs amplitude encoding, with or without data re-uploading, 1-10 layers, quantum dropout) and thousands of classical NNs on one heart-disease table, then compared the best of each. Angle encoding uses one qubit per input after rescaling to [0, 2pi].
- (b) 914 records, 11 features, 11 qubits (angle) or 13 (amplitude), 70/30 split, 10 seeds per configuration (Results, "Dataset and pre-processing"). Accuracy: angle about 83-87% vs amplitude 80-82%; best angle+re-uploading 86.84%, angle+dropout 87.46%, best NN 86.67% (Table 6, Fig. 3). Accuracy plateaus after 2 layers (Fig. 3a). 1-layer dropout QNN leads at 10-50% of the training data by about 0.5-2 points (Table 7).
- (c) **Weak to moderate.** Model selection and NN early stopping use the test set (Experimental settings). There are no significance tests, only one split, and no noise or hardware. The text is inconsistent about the best layer count (Results says 9, Discussion says 6), and the counts don't add up (914 vs 643+275 = 918).
- (d) **Uncertain.** Same disease, but a different cohort (multi-centre, 11 features one-hot) and 11 qubits vs our 6 MI-selected codes. "Angle encoding plus re-uploading is competitive" is plausible for us. "Quantum is better at low data" is not supported strongly enough to transfer.
- (e) H-C9: adding data re-uploading with trainable input scaling raises heart-VQC AUC above 0.755 on our 5 folds (paired across folds). Cost: about 2 min per dataset at 40 epochs. Sandbox (scratch/h2) says the input scaling, not the re-uploading, carries most of the gain.

### B5 XanaduAI/qml-benchmarks (Apache-2.0) - README
https://github.com/XanaduAI/qml-benchmarks
- (a) A scikit-learn-style harness (fit / predict / predict_proba, hyperparameters as attributes, seeded) with quantum and classical models and a hyperparameter-search script that writes best settings to CSV. Models include a data re-uploading classifier.
- (b) Tooling, not a result. The README does not state the CV scheme of the search script; the paper (C13) uses 5-fold grid search.
- (c) **Strong as a template** (published, licensed, used for C13). Not evidence of performance.
- (d) **Likely.** Our classifiers already follow the same sklearn interface (`vqc.py:67`), so `GridSearchCV` can wrap them unchanged. Its dependencies are JAX-based, so we would reuse the design only, not the code.
- (e) H-B5: wrapping all 7 models in an equal-budget inner grid search (same number of configurations each) changes the ranking on heart disease. Paired bootstrap on pooled OOF AUC. Cost: about 40-50 min for both datasets with 6 configurations per model.

### C11 QCCNN for breast cancer, Sci Rep 2024 - FULL
https://pmc.ncbi.nlm.nih.gov/articles/PMC11494181/ (DOI 10.1038/s41598-024-74778-7; via PubMed/PMC)
- (a) A quantum "convolutional" layer (Hadamard, feature angles, CRZ entanglers, trainable RY, `<Z>` per qubit) followed by a classical dense head, built in PennyLane plus PyTorch, compared with a CNN and logistic regression.
- (b) WDBC 70/30: QCCNN mean validation 96.155%, best iteration 97.661%; CNN 92.822%; LR 91.184% (Table 4, Fig. 9). No AUC, no timings, no variance (Results; Conclusion).
- (c) **Weak.** The headline is a best iteration on the validation set. The number of runs is unknown, there are no significance tests, and the qubit count isn't stated.
- (d) **Unlikely** as a performance lever. Our hybrid QNN is already this "quantum layer plus classical head" family. The paper's weak baselines (LR at 91%) differ from ours (LR AUC 0.979).
- (e) H-C11: a dressed circuit (classical layer, quantum layer, classical layer) is no better than the same network with the quantum layer replaced by a classical layer of equal width. 5 folds, paired. Cost: about 2 min. Sandbox (scratch/h2) agreed on 2 folds.

### C13 Bowles, Ahmed, Schuld, "Better than classical?" 2024 - PARTIAL (through Section VI start)
https://arxiv.org/html/2403.07059 (also https://www.alphaxiv.org/abs/2403.07059; alphaXiv connector not authenticated, read via arXiv HTML)
- (a) A large, fair benchmark of 12 QML models vs classical baselines: full grid search with 5-fold CV on 160 mostly synthetic datasets, plus "separable" (entanglement-free) ablations of each quantum model.
- (b) Classical baselines ranked first in all three model families (Sec. V.1). Removing entanglement gave no drop for the dressed quantum circuit and some drop for the data re-uploading classifier (Sec. V.3, Fig. 13). Amplitude-encoded models were worst (Sec. I, II). Inputs were scaled to [-pi/2, pi/2] (Sec. II.3). Test accuracy varies from near chance to near perfect across hyperparameters (Sec. IV, Fig. 7).
- (c) **Strong for methodology** (scale, ablations, open code). **Moderate for transfer**, since most data are synthetic and grid sizes differed between models (Sec. IV), so tuning budgets were not equal.
- (d) **Likely** for the protocol (tuning, ablations, strong baselines). **Uncertain** for model-specific findings on 6-feature medical data.
- (e) H-C13: removing the CNOT ring (with all-qubit readout, so every feature can reach the output) does not lower VQC AUC significantly on either dataset. 5 folds, paired bootstrap. Cost: about 4 min. Sandbox (scratch/h2b) showed no drop on 2 heart folds.

### A1 QuantumDx residual corrector (no licence: ideas only) - README
https://github.com/dhanasai2/QuantumDx
- (a) A classical XGBoost model plus a 4-qubit circuit (H, RY encoding of 4 PCA components, CNOT chain, `<Z>` readout). The quantum outputs act as a "residual corrector" fused with the classical prediction. One run on IBM `ibm_marrakesh` is cited. The README doesn't fully explain the correction mechanism.
- (b) Self-reported AUC: XGBoost 0.8567, residual corrector 0.8565, deployed hybrid 0.8369, VQC 0.6072 on 13,329 test patients (README table).
- (c) **Weak.** Self-reported, one split, undocumented source dataset, 4 commits, no external review. It is honest that the hybrid does not beat XGBoost.
- (d) **Uncertain.** A residual model on top of a strong classical model can at best match it (their own table shows +-0.0002). On ~300 rows the corrector would add variance.
- (e) H-A1: a VQC trained on the out-of-fold residuals of logistic regression (inner CV) adds no AUC over logistic regression alone. 5 folds, paired. Cost: about 5 min.

---

## T2 Quantum kernels

### C12 arXiv 2604.18837, quantum-kernel SVMs vs classical on tabular data - FULL through Sec. 7 (conclusion truncated)
https://arxiv.org/html/2604.18837
- (a) 970 nested-CV experiments compare four quantum feature maps with linear, polynomial and RBF kernels on 9 UCI/OpenML datasets, including breast cancer and heart disease. They add kernel-spectrum diagnostics, quantum kernel training (QKT) by kernel-target alignment, noise simulation, and IBM hardware checks.
- (b) None of 29 quantum-vs-classical Wilcoxon tests is significant at n = 5 folds, where the minimum attainable p is 0.0625 (Table 6, Sec. 7.5). Mean balanced accuracy: linear 0.830, RBF 0.825, best quantum 0.649 (Table 5). Dataset explains epsilon^2 = 0.73 of the variance vs kernel family 0.089 (Sec. 6.2, Fig. 2). Feature maps take features with no rescaling, so there is no bandwidth (Sec. 4.2). Bandwidth-aware encoding is proposed as future work (Sec. 7.1). Spectra are either near-uniform (belis) or near rank-1 (rot2dof) (Table 7). QKT is the only competitive quantum option (breast BA 0.968 vs RBF 0.976) at about 2,060x cost, with only 13.6% of runs converging (Sec. 6.2, 7.4). The inner loop tuned only C in {0.01 ... 100} (Sec. 4.6).
- (c) **Strong.** Nested CV, many datasets, multiple tests, honest statistical-power caveats, a hardware cross-check. Limitations: hardware at 3-5 qubits only, n = 5 folds, and no bandwidth tuning.
- (d) **Likely.** Same datasets family, similar qubit counts, same feature-map family (ZZ). Their "no bandwidth" gap is exactly our gap.
- (e) H-C12: a single bandwidth factor s (inner CV over s and C, training fold only) raises QSVM AUC on both datasets. Pooled OOF paired bootstrap. Cost: under 1 min per dataset (scratch/h1 ran in 0.4 s per fold).

### C14 PMC13360165, robustness-oriented hybrid pipeline for breast cancer (Diagnostics 2026) - FULL (main text)
https://pmc.ncbi.nlm.nih.gov/articles/PMC13360165/
- (a) Uses WDBC plus an external WBC cohort, re-running the pipeline from scratch on the second cohort ("method-level" validation). RFECV is capped at 8 features, giving an 8-qubit VQC (RY embedding, 4 strongly entangling layers) and an untuned ZZ QSVM. Classical models are Optuna-tuned. Reporting covers calibration, decision curves, depolarising-noise tests and a surrogate explainer.
- (b) Internal AUC: VQC 0.992 vs RBF-SVM 0.998; QSVM 0.727 (Table 4). External AUC: VQC 0.983 vs RBF-SVM 0.986 (Table 8). X/Y embeddings gave 0.979-0.997, Z embedding 0.468-0.562 (Table 10). VQC AUC stayed 0.992 for single-qubit depolarising p = 0 to 0.10 (Table 11). VQC ECE 0.175, calibration slope 4.729, HL p < 0.001 (Table 6). Feature selection, scaling and Optuna ran on training data only (Sec. 2.7).
- (c) **Moderate.** Careful leakage control and calibration reporting. But one split, the QSVM untuned and subsampled, single-qubit noise only, and an external cohort of shared lineage.
- (d) **Likely** for practice: calibration reporting, the leakage checklist, an embedding sanity check, method-level external validation. Its flat noise-AUC curve is expected by construction for depolarising noise on a `<Z>` readout (see INFERENCES), so it is not evidence of hardware robustness.
- (e) H-C14: VQC Brier and ECE on pooled OOF predictions are worse than logistic regression's on both datasets, and Platt scaling in an inner CV narrows the gap. Cost: about 3 min. Sandbox (scratch/h4): Platt barely changed Brier (0.189 to 0.196 and 0.220 to 0.219).

### C10 Kumar et al., Sci Rep 2025, quantum-inspired feature selection + QSVM - FULL (main text)
https://pmc.ncbi.nlm.nih.gov/articles/PMC12254482/ (DOI 10.1038/s41598-025-09957-1; via PubMed/PMC)
- (a) A quantum-inspired genetic algorithm picks features, quantum-inspired PSO tunes hyperparameters, and a 7-qubit QSVM trained with SPSA classifies. The classical comparator is GA plus PSO plus SVM.
- (b) Merged 5-cohort heart data, 918 rows, 80/20 split. QSVM 97.83% vs classical 94.02% accuracy, with 7 vs 9 features (Experiments 1-2, Table 10). No significance tests. Table 10 metrics contradict the text. The quantum model was slower (413.57 s vs 362.92 s).
- (c) **Weak.** Single test split, possible CV leakage (unclear whether selection was nested), internal inconsistencies, simulator only, no code found.
- (d) **Unlikely.** The gain can't be separated from the feature-selection difference. The method is heavy for our budget.
- (e) H-C10: on our heart folds, mutual-information selection at k = 6 vs RFECV (logistic regression) at k = 6, both fitted inside training folds, changes QSVM AUC by less than its fold standard deviation. Cost: about 2 min.

### R2 PMC13518982, adaptive quantum kernel selection via leakage-free stacking - PARTIAL (to Table 10; ablation, noise and limitations not visible)
https://pmc.ncbi.nlm.nih.gov/articles/PMC13518982/ (blocked when RELATED_WORK.md was written; opened in this session)
- (a) Several fidelity kernels (angle, ZZ, amplitude) feed QSVM and QKNN base models. Their out-of-fold predictions from an inner 5-fold loop are stacked with a balanced logistic-regression meta-learner, whose weights decide which kernel to trust.
- (b) On breast cancer, stacking accuracy is 0.964 vs RBF 0.970, with all ensemble p > 0.05 (Table 8). On Parkinson's, specificity rises to 0.813 from 0.585 (p < 0.001) but accuracy doesn't differ significantly (p = 0.312) (Table 7). Pure VQC accuracy is 0.41-0.54 (Tables 7-9). PCA was fitted globally, before CV (Stage 1).
- (c) **Moderate.** Bootstrap and paired tests, honest parity on breast cancer. Global PCA is a mild leak, and some results weren't visible.
- (d) **Uncertain.** Stacking adds inner-CV cost and complexity for a likely parity result. Its out-of-fold stacking discipline is the useful part.
- (e) H-R2: a 2-model OOF stack (logistic regression plus tuned QSVM) is no better than logistic regression alone on pooled OOF AUC. Cost: about 3 min.

---

## T3 ML and training practice

### T3-1 Varma & Simon 2006, CV bias in model selection - ABSTRACT
https://doi.org/10.1186/1471-2105-7-91 (PMC1397873; via PubMed)
- (a) If hyperparameters are chosen to minimise a CV error and that same CV error is reported, the estimate is optimistically biased. Nested CV (tune in an inner loop, estimate in an outer loop) removes most of the bias.
- (b) On null data, tuned-classifier CV error was below 30% on 18.5% (shrunken centroids) and 38% (SVM) of datasets, while true error was chance. Nested CV was close to independent-test error (abstract).
- (c) **Strong.** A simulation with a known ground truth, and widely replicated.
- (d) **Likely.** We have about 240 heart rows per training fold. Choosing a VQC variant after looking at our own 5-fold table would bias it exactly this way.
- (e) H-T3-1: the best-of-grid outer-CV AUC (non-nested) exceeds the nested estimate by more than 0.01 for the VQC on heart disease. Cost: comes free with the nested-CV run.

### T3-2 TRIPOD+AI (Collins et al., BMJ 2024) - ABSTRACT
https://doi.org/10.1136/bmj-2023-078378 (PMC11019967; via PubMed). Used by C14.
- (a) A 27-item reporting checklist for prediction-model studies, whether built with regression or machine learning, plus an abstracts checklist.
- (b) A reporting standard, not an empirical claim. Item-level content was not read (abstract only).
- (c) **Strong as a standard** (EQUATOR consensus).
- (d) **Likely.** Our README already reports data source, splits and limits. Calibration and a completed checklist are missing.
- (e) H-T3-2 (process, no metric): a completed TRIPOD+AI checklist in `docs/` flags at least two missing items (expected: calibration and sample-size justification). Cost: about 30 min of reading, no compute.

### T3-3 Van Calster et al. 2019, "Calibration: the Achilles heel" - ABSTRACT
https://doi.org/10.1186/s12916-019-1466-7 (PMC6912996; via PubMed)
- (a) Discrimination (AUC) alone is not enough for risk models. Poor calibration misleads decisions, so calibration should be assessed (with curves when samples allow), with model complexity balanced against sample size.
- (b) A position paper with argument plus examples (abstract).
- (c) **Moderate to strong** (expert consensus, widely cited).
- (d) **Likely.** We report no calibration at all. Per-fold ECE at about 61 validation rows is noisy, so metrics should be pooled over out-of-fold predictions.
- (e) Same as H-C14.

### Feature selection under a qubit budget (RFECV, mutual information, PCA) - synthesised from C14, R1, C12, A4
Our code supports `mutual_info` and `pca` (`preprocess.py:15-20`); `--n-qubits` allows 4-8 (`benchmark.py:183`). C14 used RFECV around logistic regression with a bootstrap stability check (Jaccard 0.83, Table 13). C12 found feature count k had a larger effect (epsilon^2 0.278) than kernel family (0.089) (Sec. 6.2). R1 used random-forest selection (II-B).
- (e) H-FS: for each model, k in {4, 6, 8} x {MI, PCA}, nested, gives a model-specific best k. The best quantum k is not larger than the best classical k. Cost: about 25 min.

---

## T4 Simulators and noise

### B6 TorchQuantum (MIT) - README
https://github.com/mit-han-lab/torchquantum
- (a) A PyTorch-native statevector simulator with batching, autograd, GPU support and Qiskit converters; claims 30+ qubits on multiple GPUs.
- (b) The README lists **Python 3.7-3.9** and PyTorch >= 1.8; the latest news item is v0.1.8. There are no benchmarks for the scaling claim, and the README doesn't document noise simulation.
- (c) **Weak for us.** Unverified scaling, and the stated Python range excludes our 3.13.3.
- (d) **Unlikely.** Our circuits are 6-10 qubits, where `default.qubit` with backprop already runs a 200-row batch in 0.01-0.24 s (scratch/h5). It would be a new dependency, and installing it would need approval.
- (e) H-B6 (feasibility only): TorchQuantum installs and imports on Python 3.13 / torch 2.14. **Not tested** (no downloads allowed). Expected cost: 10 min after approval.

### B7 QuantumNAS (arXiv 2107.10845) - ABSTRACT
https://arxiv.org/abs/2107.10845
- (a) Trains a "SuperCircuit" once, then searches sub-circuits and qubit mappings under real device-noise models, and finally prunes redundant gates.
- (b) Self-reported: over 95% (2-class) and 85% (4-class) QML accuracy on real hardware across 12 benchmarks and 14 devices (abstract). Baselines aren't named in the abstract.
- (c) **Moderate** (peer-reviewed lineage, but only the abstract was read).
- (d) **Unlikely** at our scale. The search budget dwarfs our 60-minute limit. Gate pruning is the cheap idea: our VQC has 42 gates (12 CNOT) and the QSVM map has 54 (20 CNOT) (scratch/h5, `qml.specs`).
- (e) H-B7: pruning the last CNOT ring of the VQC (12 to 6 CNOTs) keeps AUC within fold standard deviation. Cost: about 2 min.

### T4-1 PennyLane devices, noise channels, shots - docs via Context7
Context7 `/pennylaneai/pennylane` (release-note snippets for `default.mixed` with channels, `qml.add_noise` / `NoiseModel`, `lightning.qubit`, shot lists)
- (a) `default.mixed` simulates density matrices and supports channels such as DepolarizingChannel and AmplitudeDamping. `qml.add_noise` attaches a noise model to an existing circuit. Shots are set per device or with `qml.set_shots` (present in our 0.45.1).
- (b) Verified locally: `default.qubit`, `default.mixed` and `lightning.qubit` 0.45.0 all instantiate in `.venv` with no new dependency (scratch check, 2026-10-08).
- (c) **Strong** (official docs plus a local check).
- (d) **Likely.** Noisy simulation is possible today. At 8 qubits, though, `default.mixed` took 28 s to run forward on 200 rows (scratch/h5), so noisy training beyond 6-8 qubits is out of budget.
- (e) H-T4: a VQC trained noiselessly keeps its AUC under single-qubit depolarising noise up to p = 0.1 (expected by construction); Brier rises. Cost: about 1 min per fold. Sandbox: AUC 0.783 at every p, Brier 0.189 to 0.205.

### T4-2 Qiskit Aer noise models - BLOCKED / UNVERIFIED
Qiskit and qiskit-aer are not installed in `.venv` (installing would be a download). The qiskit MCP server was disconnected during this run. Earlier in this session the qiskit MCP transpiled a 2-qubit H+CX+RZ circuit to `ibm_heron` (rz 4, sx 3, cz 1, x 1, depth 6), so the tool works when connected. No claims about Aer noise models are made here.

---

## T5 End-to-end early-detection platforms (ideas only; A1-A7 have no open licence unless stated)

### A2 abcreativeakshay/hybrid-qml-disease-detection - README (no licence found)
https://github.com/abcreativeakshay/hybrid-qml-disease-detection
- (a) A Streamlit benchmark app: PCA to 4-8 qubits, VQC and fidelity-kernel QSVM vs LR/RF/RBF-SVM, a threshold slider that live-updates sensitivity, specificity and the confusion matrix, Low/Medium/High risk bands, and "quick demo" (precomputed) vs "live training" modes.
- (b) No numbers reported. Band cut-offs and slider range aren't stated.
- (c) **Weak** (UI ideas only).
- (d) **Likely** for UI. A threshold slider computed on stored OOF scores costs nothing at runtime.
- (e) H-A2 (UX): the Quantum Lab can show sensitivity and specificity at any threshold from the stored pooled OOF ROC points (`summary.json` `roc`) with no retraining. Cost: UI work only, no compute.

### A3 ushakiran45/SIH26139-Hybrid-QML - README (no licence found)
https://github.com/ushakiran45/SIH26139-Hybrid-QML
- (a) Retinal images go through EfficientNet-B3 features and PCA(4) into a 4-qubit VQC vs RBF-SVM, with Grad-CAM and Docker deployment.
- (b) N = 400 images, 5-fold: SVM 90.0 +- 1.8% vs VQC 88.0 +- 3.8% accuracy. The authors admit the VQC threshold (0.35) and class weights were tuned on the same sample (README).
- (c) **Weak to moderate.** Small, and optimistic by their own admission. The honesty is exemplary.
- (d) **Uncertain.** Imaging is out of our scope. The lesson is about thresholds: never pick the threshold on evaluation data.
- (e) H-A3: a threshold chosen on inner folds for 90% specificity gives lower OOF sensitivity than one chosen on the outer fold. Cost: about 1 min, using existing scores.

### A4 sharvilmesh/QuantumDiseaseAI - README (no licence found)
https://github.com/sharvilmesh/QuantumDiseaseAI
- (a) A five-stage preprocessing pipeline (audit, clean, standardise, ANOVA SelectKBest, PCA to qubits), an RY/RZ + CNOT-ring VQC like ours, and plain-language per-patient SHAP explanations.
- (b) No results. 2 commits.
- (c) **Weak.**
- (d) **Uncertain.** Running PCA after SelectKBest is a variant of our feature-selection experiment. Plain-language explanations are a UX idea.
- (e) Covered by H-FS.

### A5-A7 extras (sritharanvenkatesan-lab/sih-hybrid-qml "All rights reserved"; 7pavana/SIH-AlgoX MIT; prasanna01-hub/hybrid-quantum-machine-learning-platform, no licence stated) - README
https://github.com/sritharanvenkatesan-lab/sih-hybrid-qml, https://github.com/7pavana/SIH-AlgoX, https://github.com/prasanna01-hub/hybrid-quantum-machine-learning-platform
- (a) Respectively: a FastAPI/React VQC/QNN platform on WBCD prognosis; a Next.js app with a 2-qubit "quantum-gated" ResNet18 (mock inference in the UI); a Streamlit Qiskit VQC (2-6 features, MI or PCA) on Pima diabetes.
- (b) None report numbers. SIH-AlgoX says its outputs are simulated. The prasanna01 README says classical often beats the VQC.
- (c) **Weak.**
- (d) **Unlikely** to change our methods. They confirm the field's typical stack and that nobody in this problem statement reports tuned, tested comparisons, which is our differentiator.
- (e) None worth the compute.

### B8 fatimasood/XAI-Hybrid-Quantum-Liver-Disease-Detection (MIT) - README
https://github.com/fatimasood/XAI-Hybrid-Quantum-Liver-Disease-Detection
- (a) A hybrid quantum-classical NN on ILPD, explained with Kernel SHAP, Integrated Gradients and permutation importance. A feature-ablation check removes the top SHAP features, retrains, and expects a performance drop.
- (b) Qualitative only ("high decrease in accuracy", in a figure). No counts or numbers in the README.
- (c) **Weak** (no numbers), but the check itself is sound and cheap.
- (d) **Likely.** We already compute permutation importance and SHAP (`explain.py:19-37`). The missing control is comparing the drop from removing top-ranked features with the drop from removing random features.
- (e) H-B8: removing the top-2 permutation-ranked features and retraining lowers AUC more than removing 2 random features (mean over 5 random draws). 5 folds. Cost: about 10 min (quantum models re-run at k = 4).

### R1 arXiv 2608.11373, QML vs AutoML on oncological data - FULL
https://arxiv.org/html/2608.11373v1
- (a) Bit-encoded QML models (4-10 qubits, warm-started) vs TPOT2 AutoML MLPs on WDBC, TCGA omics and MedMNIST, plus a resource estimate (qubits needed to fit the data perfectly).
- (b) On WDBC, quantum test accuracy is within standard error of classical at every qubit count; Mann-Whitney U at alpha 0.05 (Sec. III-A, Fig. 2). Estimated qubits for WDBC are about 15, below their 50-qubit "advantage signal" threshold (III-A).
- (c) **Moderate.** Stratified 5-fold, significance tests, but simulator only, and quantum training stops at 100% training accuracy.
- (d) **Likely**, as a reality check: parity on WDBC again.
- (e) None new (covered by H-B5).

---

## D. Kaggle notebooks - BLOCKED
https://www.kaggle.com/code/dev523/quantum-kernel-machine-learning, https://www.kaggle.com/code/georgiosgiapitzakis/quantum-variational-classifier, https://www.kaggle.com/code/prakharsinghchouhan/quantum-transfer-learning-via-pennylane-and-resnet/notebook. Only page titles loaded (the body needs JavaScript or a login). No claims are taken from them.

## Reading tally
- FULL (main text): 6. C9, C11, C10, C12, C14, R1.
- PARTIAL: 2. C13 (to Sec. VI), R2 (to Table 10).
- ABSTRACT only: 4. B7, T3-1, T3-2, T3-3.
- README (online, no code read): 10. A1-A7, B5, B6, B8.
- Docs: 1. PennyLane via Context7.
- BLOCKED: 4. D1-D3 (Kaggle) and T4-2 (Qiskit Aer, not installed; MCP disconnected). nature.com direct links redirected to a login page, so C9, C10 and C11 were read via PMC instead.

---

# Addendum study (docs/LEARN_FROM_ADDENDUM.md, master prompt v2 P1), 2026-10-08

Same five-part template. "Our setting" = 6 qubits, <= 200 training rows per fold, 12+ small public tabular medical datasets, CPU simulation only. All [verify] identifiers in the addendum resolved (H3, H5, H7-H12 on arXiv; H14, H15 on PubMed) and are now marked verified.

## G. "Quantum beats classical" claims

### G1 arXiv 2604.24597v1, QSVM on medical foundation-model embeddings - FULL (to ~86%)
https://arxiv.org/html/2604.24597v1
- (a) Frozen chest-X-ray embeddings are PCA-reduced to q dimensions and fed to a fidelity QSVM (one RY per qubit, ring CNOT, 1 rep, trace-normalised kernel). The analysis compares kernel effective ranks.
- (b) Untuned QSVM beats an untuned linear SVM on minority-class F1 in 18/18 configurations, because the linear kernel's effective rank is about q and it collapses to the majority class (Tables 2, 5). Against an RBF SVM with C tuned, the mean gain is +0.068 F1 (Table 4). A rank-matched RBF closes much of the gap: 0.304 vs 0.343 at q = 11 (Table 10). The DT9 stratum was chosen post hoc (Sec. III.1, VI.6). The task is insurance type, not disease.
- (c) **Weak to moderate.** Primary win is against an untuned baseline. Stratum chosen after seeing results. Single site. Simulation only. Text and tables disagree (Sec. VI.6 vs Table 10).
- (d) **Uncertain.** The effective-rank lens transfers directly: our sandbox and E3 showed the untuned ZZ kernel is near-diagonal and the tuned bandwidth changes its rank. The "win" itself does not transfer (we tune every baseline).
- (e) H-G1 (E12): the tuned-bandwidth QSVM does not beat an RBF SVM whose gamma is chosen so its kernel effective rank matches the QSVM's, on the development set. Cost: < 2 min (kernels only).

### G2 arXiv 2511.10831v1, quantum kernels across diverse data - FULL
https://arxiv.org/html/2511.10831v1
- (a) Amplitude and coherent-state quantum kernels with a scaled RZ(s·φ·x) layer, trained by kernel-target alignment (Adam, 500 steps, batches of 4).
- (b) Quantum kernels top Table 1 on 6 of 8 datasets (e.g., SEED 0.878 vs 0.684). But the quantum search stopped once it matched the classical baseline while classical kernels got a full grid (Sec. IV.0.3, Sec. V). Single split, one seed, no variance. MinMax vs Standard scaling mattered for quantum only (Sec. IV.0.1).
- (c) **Weak.** Asymmetric tuning, no variance, a text/table mismatch (30% vs 19 pp).
- (d) **Likely** for the mechanism (scale parameter on the encoding angle; this is our bandwidth s). **Unlikely** for the size of the win.
- (e) H-G2 (E13): choosing s by maximal centred KTA on the training fold gives the same pooled AUC as choosing s by inner-CV AUC (|Δ| < 0.01), at a fraction of the cost. Cost: < 2 min.

### G3 arXiv 2508.19437, data-efficient learning with quantum kernels - FULL
https://arxiv.org/html/2508.19437
- (a) Compares sample efficiency via cumulative target-alignment spectra and learning curves at small N (50 repeats), on real clinical features (WDBC, heart failure, BMT) with engineered labels.
- (b) The quantum kernel learns engineered targets with fewer samples (Fig. 3). The authors do not test natural labels and call the results "not conclusive on their own" (Sec. V).
- (c) **Weak for natural labels** (by construction).
- (d) **Unlikely** that a low-data advantage appears with natural labels. The learning-curve-with-repeats protocol transfers.
- (e) H-G3 (E17): on natural labels, quantum learning curves at N = 10, 20, 50, 100, 200 lie on or below parameter-matched classical controls. Cost: ~30 min on 4 dev datasets.

### G4 arXiv 2602.14641, quantum reservoir on 108 patients - FULL
https://arxiv.org/html/2602.14641
- (a) Top-SHAP feature subsets encoded into a neutral-atom reservoir, with nested 5 x (inner 10-fold) random search for six classical readouts.
- (b) Classical models peak at 5-7 SHAP features, above all 56 features (Sec. III.1.1, Fig. 1). Noiseless reservoir features do not beat classical (Sec. III.1.2). Hardware runs used SHAP rankings aggregated across splits including test data (leakage acknowledged, Sec. II.6).
- (c) **Moderate** for the feature-subset finding (nested, per-split SHAP for emulated runs). **Weak** for hardware results (leakage).
- (d) **Likely.** Our qubit budget forces k = 6; 5-7 is exactly our regime. Ranking must stay inside training folds.
- (e) H-G4 (E14): SHAP-ranked top-k (k in {5, 6, 7}) selection fitted inside training folds matches or beats mutual-information selection at k = 6 for LogReg and the VQC on the development set. Cost: ~25 min.

### G5 Sci Rep 2026, MedMNIST on IBM hardware - FULL via PMC
https://pmc.ncbi.nlm.nih.gov/articles/PMC12992601/ (DOI 10.1038/s41598-026-35605-3; nature.com redirected to login)
- (a) Hardware-aware circuit search, then circuit selection by a Clifford-replica noise-resilience score (discard below 0.7), then DD + twirling + M3 mitigation on IBM Cleveland, with 60-120 parameters.
- (b) Mitigation raised OCTMNIST AUC from 0.545 to 0.622 (Table 4). QML trails the best classical model on every dataset by 2.6-54 pp (Table 6). No cross-validation; repeated only on DermaMNIST (Results). The authors concede the circuits are classically simulable (Discussion).
- (c) **Moderate** for the noise-aware selection method. **Weak** for performance claims.
- (d) **Uncertain.** No hardware for us. Ranking circuits by simulated degradation under the same noise model is a cheap analogue.
- (e) H-G5 (E18): under p2 = 0.01 two-qubit noise, circuits with fewer CNOTs (no-ring) degrade less in Brier than the ring circuit, without a larger noiseless AUC loss. Cost: ~10 min.

### G6 arXiv 2408.12739, QCNNs are effectively classically simulable - ABSTRACT
https://arxiv.org/abs/2408.12739 (PRX Quantum 7, 020304)
- (a) Randomly initialised QCNNs only use low-body information, so on "locally-easy" datasets a Pauli-shadow classical algorithm simulates them (up to 1024 qubits).
- (b) Numerical evidence on phases-of-matter tasks (abstract).
- (c) **Moderate** (peer-reviewed, but heuristic, average-case).
- (d) **Likely** in spirit. Our 6-qubit circuits are trivially simulable. Any claim must be about the model class, never about a computational speed-up.
- (e) No experiment. It sets a claim boundary (INFERENCES "claims not allowed").

### G7 arXiv 2211.16551, evidence against advantage with fidelity kernels - ABSTRACT
https://arxiv.org/abs/2211.16551 (Phys. Rev. A 107, 062417)
- (a) Shows that the bandwidth tuning which restores generalisation in fidelity quantum kernels drives them towards classical kernels. Spectra flatten exponentially with qubit count.
- (b) Extensive numerics on several feature maps, synthetic and real data (abstract).
- (c) **Moderate to strong** (peer-reviewed, consistent with H6 and C12).
- (d) **Likely.** Our E3 result (tuned s = 0.1-0.35 lifts AUC to LogReg parity) is exactly this mechanism.
- (e) H-G7 (E12/E19): on datasets where the tuned QSVM gains most, the chosen bandwidth is smallest and the kernel is closest to the rank-matched RBF kernel (correlation across datasets). Cost: from E12.

### G8 arXiv 2509.16410, data complexity threshold Part I - FULL (to ~94%)
https://arxiv.org/html/2509.16410v1
- (a) Review of data-complexity metrics: covariance effective dimension (Σλ)²/Σλ² (Sec. 2.1.1), cumulant interaction order (2.1.2), compression ratio (2.1.3), kernel effective dimension Tr(K(K+λI)^-1) (2.1.4), persistent homology (2.1.5).
- (b) Conceptual. No thresholds are numerically specified or validated; validation is deferred to Part II.
- (c) **Weak** as evidence, **useful** as a menu of diagnostics.
- (d) **Likely**, for the cheap ones (effective dimension, kernel effective dimension, class balance, n, d, compression ratio).
- (e) H-G8 (E19): across 12+ datasets the quantum-minus-best-classical AUC gap does not correlate significantly (Spearman, |ρ| CI excludes 0) with any single diagnostic. Cost: minutes after P4.

### G9 arXiv 2609.24666v1, few-shot generalisation of a QCNN - FULL (to ~91%)
https://arxiv.org/html/2609.24666v1
- (a) Learning curves at N = 2..80 with 10 repeated draws. A parameter-matched classical CNN as control, plus unconstrained classical baselines and transpiled-depth scaling.
- (b) The QCNN beats the parameter-matched CNN (which stays at chance), but RBF-SVM (> 0.98 by N = 5) and LogReg (> 0.99 by N = 10) beat the QCNN's ~0.95 plateau (Sec. IV.3, Fig. 10). The authors disclaim advantage.
- (c) **Moderate** (repeats, honest baselines; digits are easy).
- (d) **Likely.** Parameter-matched controls can make a quantum model look good. Reporting must include unconstrained baselines.
- (e) Same as H-G3 (E17), with both a parameter-matched MLP and the tuned LogReg on the plot.

### G10 arXiv 2511.20922v3, readout-side bypass (residual hybrid) - ABSTRACT
https://arxiv.org/abs/2511.20922
- (a) Concatenate raw inputs with quantum features before the classical classifier.
- (b) Claims up to +55% over quantum baselines (abstract), with no baseline/dataset context. Parameter counts not matched.
- (c) **Weak.**
- (d) **Likely** to "help" for a trivial reason: the raw-input path is a classical model. The fair control is the same head with a classical feature block of equal size.
- (e) H-G10 (E15): a residual head on [x, q(x)] does not beat the same head on [x, tanh(Wx)] with equal parameters. Cost: ~25 min on dev datasets.

### G11 arXiv 2512.20654v1, Q-RUN (classical re-uploading network) - FULL (to ~84%)
https://arxiv.org/html/2512.20654v1
- (a) A classical network that mimics re-uploading: per-feature sin/cos expansions plus a shared element-wise MLP (Sec. 4.2).
- (b) Mixed wins across tasks (Tables 2-7). The headline "orders of magnitude" is supported only as 5-449x on one task (Table 3). The universality claim (Claim 2) is proven for a different formulation than the tested network.
- (c) **Weak to moderate.**
- (d) **Likely** as a control design: a classical "twin" with the same input frequencies tests whether the quantum circuit adds anything beyond a trigonometric feature map.
- (e) H-G11 (E16): a classical trig twin of the re-uploading VQC (scaled sin/cos features per layer, small head, ~38 parameters) matches the re-uploading VQC's pooled AUC on the dev set (|Δ| CI includes 0). Cost: ~15 min.

### G12 arXiv 2601.03375, projected quantum kernels on small data - ABSTRACT
https://arxiv.org/abs/2601.03375
- (a) Projected kernel features (reduced density matrices) feed a CNN.
- (b) Claims CIFAR-10 at 90% vs classical CNN 12% with 1,000 samples (abstract). A CNN at 12% on CIFAR-10 is barely above chance, and the abstract's dates are inconsistent.
- (c) **Very weak.** Not used.
- (d) **Unlikely.**
- (e) None.

### G13 PostQuantum "QML reality" review - FULL
https://postquantum.com/quantum-ai/quantum-machine-learning-reality/
- (a) Five filters for any QML claim: primary evidence, hardware vs simulator, tuned classical baseline, data-loading/error-correction cost, natural vs constructed data.
- (b) Secondary review. Concludes that no fair-fight advantage on ordinary classical data is broadly accepted.
- (c) **Moderate** as a checklist.
- (d) **Likely.** We adopt the five filters as the "Findings and limits" page structure (D10).
- (e) None (process).

### G14 IBM Research blog on quantum kernels - FULL
https://research.ibm.com/blog/quantum-kernels
- (a) The rigorous kernel speed-up (Liu, Arunachalam, Temme, Nature Physics 2021) holds for discrete-log-structured classification problems.
- (b) Proven under hardness assumptions. The authors note that many real problems will not benefit.
- (c) **Strong** for its narrow scope.
- (d) **Unlikely** to apply to tabular medical data.
- (e) None (claim boundary).

## H. New sources

### H1 Demšar 2006, JMLR 7:1-30 - ABSTRACT
https://www.jmlr.org/papers/v7/demsar06a.html
- (a) Compares classifiers over many datasets: Wilcoxon signed-rank for two classifiers; Friedman then post-hoc tests for more; critical-difference diagrams.
- (b) Methodological recommendation (abstract); widely adopted.
- (c) **Strong.**
- (d) **Likely.** Exactly D5.
- (e) Process: Friedman p and Nemenyi CD for 12+ datasets x ~13 models.

### H2 Cawley & Talbot 2010, JMLR 11:2079-2107 - ABSTRACT
https://www.jmlr.org/papers/v11/cawley10a.html
- (a) Variance of the model-selection criterion lets selection over-fit, so unbiased-but-noisy criteria still bias performance estimates.
- (b) Over-fitting in selection can be comparable in size to differences between algorithms (abstract).
- (c) **Strong.**
- (d) **Likely.** Our "optimism" column measures it.
- (e) Process: leakage audit that no outer fold touches tuning, plus optimism per model.

### H3 Varoquaux 2017, arXiv 1706.07581 (verified) - ABSTRACT
https://arxiv.org/abs/1706.07581
- (a) Fold-to-fold standard error understates CV uncertainty; small samples give large error bars.
- (b) About ±10% at n ≈ 100 (abstract).
- (c) **Strong.**
- (d) **Likely.** Our datasets have 150-800 rows: report intervals, repeated CV, corrected resampled t-tests.
- (e) Process.

### H4 Grinsztajn, Oyallon, Varoquaux 2022, arXiv 2207.08815 - ABSTRACT
https://arxiv.org/abs/2207.08815
- (a) A 45-dataset tabular benchmark with hyperparameter-search budget curves (20,000 compute-hours).
- (b) Tree-based models remain state of the art on medium-sized tabular data (abstract).
- (c) **Strong.**
- (d) **Likely.** Justifies adding HistGradientBoosting as a strong baseline (D4).
- (e) Process: HGB in every comparison.

### H5 Bischl et al., OpenML Benchmarking Suites, arXiv 1708.03731 (verified) - ABSTRACT
https://arxiv.org/abs/1708.03731
- (a) Curated, documented task suites with metadata (e.g., OpenML-CC18).
- (b) Design guidance (abstract).
- (c) **Strong** as practice.
- (d) **Likely.** The registry gets checksums, licences, provenance and target rules.
- (e) Process (D2).

### H6 Thanasilp, Wang, Cerezo, Holmes 2022, arXiv 2208.11060 - ABSTRACT
https://arxiv.org/abs/2208.11060
- (a) Quantum kernel values concentrate exponentially with qubit count, from expressive embeddings, global measurements, entanglement and noise; trained (alignment) embeddings are also vulnerable.
- (b) Analytical bounds plus numerics (abstract).
- (c) **Strong** (theory).
- (d) **Likely.** At 6 qubits concentration is mild, but the untuned ZZ map already behaves like the "too concentrated" regime. Track the off-diagonal mean and effective rank per dataset.
- (e) Feeds E19 diagnostics.

### H7 Hubregtsen et al. 2021, arXiv 2105.02276 (verified; Phys. Rev. A 106, 042431) - ABSTRACT
https://arxiv.org/abs/2105.02276
- (a) Train embedding kernels by kernel-target alignment, with noise mitigation and finite-shot bounds.
- (b) Simulations plus hardware tests (abstract).
- (c) **Moderate to strong.**
- (d) **Likely**, in time-boxed form (E13).
- (e) Same as H-G2.

### H8 Kübler, Buchholz, Schölkopf 2021, arXiv 2106.03747 (verified; NeurIPS 2021) - ABSTRACT
https://arxiv.org/abs/2106.03747
- (a) Spectral analysis of quantum kernels' inductive bias.
- (b) Advantage needs a low-dimensional RKHS that contains classically hard functions; this is more plausible for quantum-generated data (abstract).
- (c) **Strong** (theory).
- (d) **Likely** as interpretation: our tuned bandwidth narrows the RKHS, but nothing suggests our labels are classically hard.
- (e) Interpretation of E3/E12 only.

### H9 Schuld, Sweke, Meyer 2021, arXiv 2008.08605 (verified; Phys. Rev. A 103, 032430) - ABSTRACT
https://arxiv.org/abs/2008.08605
- (a) Variational quantum models are partial Fourier series in the data. The encoding gates set the accessible frequencies; repeating encodings enriches the spectrum.
- (b) Theory (abstract).
- (c) **Strong.**
- (d) **Likely.** It explains why trainable input scaling (changes frequencies) helped the heart VQC more than depth.
- (e) Interpretation of E6 plus the trig twin (E16).

### H10 Schreiber, Eisert, Meyer 2023, arXiv 2206.11740 (verified; PRL 131, 100803) - ABSTRACT
https://arxiv.org/abs/2206.11740
- (a) Efficiently obtained classical surrogates reproduce trained re-uploading models.
- (b) In their experiments, quantum models showed no advantage in performance or trainability (abstract).
- (c) **Strong.**
- (d) **Likely.** A surrogate-fidelity check: fit a classical trig regression to the trained VQC's outputs on training rows; report R² on validation rows.
- (e) H-H10 (E16b): surrogate R² > 0.9 on the dev set. Cost: minutes.

### H11 Pérez-Salinas et al. 2020, arXiv 1907.02085 (verified; Quantum 4, 226) - ABSTRACT
https://arxiv.org/abs/1907.02085
- (a) Data re-uploading makes even a single-qubit classifier universal.
- (b) Constructive argument plus examples (abstract).
- (c) **Strong** (origin paper).
- (d) **Likely.** Our vqc_reupload_scale implements the layer-wise version; E6 compares it against a parameter-matched 3-layer control.
- (e) Covered by E6.

### H12 Havlíček et al. 2019, arXiv 1804.11326 (verified; Nature 567, 209-212) - ABSTRACT
https://arxiv.org/abs/1804.11326
- (a) Origin of the quantum kernel estimator and the ZZ-type feature map.
- (b) Hardware demonstration on engineered data (abstract).
- (c) **Strong** as provenance.
- (d) Our map differs: RY(π/2) replaces the Hadamard (hardware-native gate set, DECISIONS.md 22:07), pair phase (π-x_i)(π-x_j) on a linear chain, a new bandwidth s. The map definition itself was not visible on the abstract page (UNVERIFIED detail).
- (e) Documentation item for the technical report.

### H13 PennyLane demos: kernels module and kernel-based training - FULL
https://pennylane.ai/demos/tutorial_kernels_module, https://pennylane.ai/demos/tutorial_kernel_based_training
- (a) Embedding kernel = overlap circuit; alignment training with a differentiable, class-balanced KTA on 4-point batches for 500 steps. Kernel training costs ~M² circuit evaluations versus variational training ~params x steps x batch.
- (b) Tutorial example only (alignment 0.07 to 0.27).
- (c) **Moderate** (reference implementation, not evidence).
- (d) **Likely** for cost reasoning: our 200-row cap keeps kernels cheap (statevector, one broadcast per matrix).
- (e) Informs E13's time box.

### H14 TRIPOD+AI (Collins et al., BMJ 2024;385:e078378) - verified via PubMed (see T3-2)
### H15 Van Calster et al. 2019, BMC Medicine 17:230 - verified via PubMed (see T3-3)
Both resolve. They require calibration slope/intercept, decision curves and an item-mapped reporting checklist (D7, D13).

## Clinical need for early detection (for the deck and technical report; according to PubMed)
1. Bray F et al. Global cancer statistics 2022 (GLOBOCAN). CA Cancer J Clin 2024;74:229-263. https://doi.org/10.3322/caac.21834. About 20 million new cancer cases and 9.7 million deaths in 2022; female breast cancer is 11.6% of new cases.
2. Roth GA et al. Global Burden of Cardiovascular Diseases and Risk Factors, 1990-2019. J Am Coll Cardiol 2020;76:2982-3021. https://doi.org/10.1016/j.jacc.2020.11.010. CVD deaths rose to 18.6 million in 2019; the leading cause of disease burden.
3. Sun H et al. IDF Diabetes Atlas: 2021 estimates and 2045 projections. Diabetes Res Clin Pract 2022;183:109119. https://doi.org/10.1016/j.diabres.2021.109119. 536.6 million adults (10.5%) with diabetes in 2021, projected 783.2 million by 2045.
4. GBD Chronic Kidney Disease Collaboration. Global burden of CKD, 1990-2017. Lancet 2020;395:709-733. https://doi.org/10.1016/S0140-6736(20)30045-3. 697.5 million CKD cases (9.1% prevalence) and 1.2 million deaths in 2017; CKD is largely preventable and treatable.
5. Siegel RL et al. Cancer statistics, 2022. CA Cancer J Clin 2022;72:7-33. https://doi.org/10.3322/caac.21708. Calls for investment in improved early detection; links stage at diagnosis to survival trends.
6. Coleman C. Early Detection and Screening for Breast Cancer. Semin Oncol Nurs 2017;33:141-155. https://doi.org/10.1016/j.soncn.2017.02.009. Serial screening detects early-stage disease and reduces mortality.

## Addendum reading tally
- FULL or near-full: G1, G2, G3, G4, G5 (via PMC), G8, G9, G11, G13, G14, H13 = 11.
- ABSTRACT only: G6, G7, G10, G12, H1-H12 = 16.
- Verified via PubMed (previously read): H14, H15 = 2.
- BLOCKED: none. The nature.com link for G5 redirected to a login; read via PMC.
