# Related Work: Hybrid Quantum ML for Early Disease Detection (SIH26139)

Research notes for `docs/RELATED_WORK.md`. Written 2026-10-09 from web search plus the Hugging Face and web tools (the alphaXiv connector was not installed in this session). Findings are paraphrased; nothing here is copied code. Numbers belong to each paper's own splits and must NOT be compared with ours. Treat every idea as a hypothesis and keep it only if our own 5-fold benchmark improves.

Reading depth: arXiv 2604.18837 and 2608.11373 and the Bowles et al. page were read as abstract or summary level; PMC13360165 was read in full; PMC13518982 (adaptive kernel selection) could not be opened (bot check), so only its title is used.

## 1. What the literature says

| Paper | Setup | Main finding |
|---|---|---|
| Benchmarking Quantum Kernel SVMs vs Classical Baselines on Tabular Data (arXiv 2604.18837) | 9 binary tabular datasets (incl. breast cancer), 4 quantum feature maps vs 3 classical kernels, strict nested CV, 970 experiments, noise models, IBM hardware check | None of 29 quantum-vs-classical comparisons was significant at alpha 0.05. RBF was the best classical kernel. Dataset choice explains about 73% of variance, kernel type about 9%. Only quantum kernel training (kernel-target alignment) was competitive (balanced accuracy 0.968 on breast cancer) at about 2,000x compute overhead. Current feature maps give kernel spectra that are too flat or too concentrated. |
| Robustness-oriented quantum-classical hybrid pipeline for breast cancer (PMC13360165) | WDBC (n=569), external check on Wisconsin Original (n=683), 8-qubit VQC (PennyLane) and ZZ-fidelity QSVM (Qiskit), classical models tuned with Optuna, stacked hybrid ensemble | VQC matched but did not beat classical (internal AUC 0.992 vs RBF-SVM 0.998; external 0.983 vs 0.986). Untuned QSVM was weak (AUC 0.727). X/Y rotation embeddings worked (AUC about 0.98-0.997); Z-rotation embedding collapsed to chance. VQC held AUC 0.992 under depolarising noise up to p = 0.10 (single-qubit channels only). VQC was poorly calibrated (ECE 0.175). Follows TRIPOD+AI reporting. |
| Better than classical? The subtle art of benchmarking QML (Bowles, Ahmed, Schuld, 2024) | 12 QML models, 160 datasets, grid search + 5-fold CV, over 200k models | Out-of-the-box classical models usually beat the quantum classifiers. Removing entanglement often gave equal or better results. Hybrid dressed circuits did best; amplitude encoding did poorly. Argues for equal tuning effort, strong baselines, and ablations. |
| Benchmarking Quantum and Classical ML on Oncological Data (arXiv 2608.11373) | WDBC, TCGA omics, MedMNIST; 4-10 qubit simulated models vs AutoML (TPOT2) neural nets | No evidence of quantum advantage; accuracy statistically indistinguishable on WDBC. Authors recommend higher-dimensional, more realistic data. |

Bottom line: the field consensus is "parity at best on small tabular medical data". Our result (VQC and hybrid QNN at parity on breast cancer, trailing on heart disease) is consistent with the literature. An honest benchmark is the contribution; a claimed quantum win would be a red flag to reviewers.

## 2. Gaps in our current pipeline, ranked by value

1. **Quantum models were not tuned like the classical ones.** Bowles et al. and 2604.18837 both stress equal tuning. Our README says kernel bandwidth was deliberately not tuned. Fix: nested CV (inner folds inside each training fold only) over kernel bandwidth / feature-map scaling, VQC learning rate, layers and epochs; give classical models the same budget (grid or Optuna).
2. **Statistical testing is missing.** 2604.18837 uses significance tests across comparisons; our table only shows mean +/- std. Add paired tests on per-fold metrics with a multiple-comparison correction, and say plainly when differences are not significant.
3. **No ablation for "is quantumness doing anything?"** Bowles et al. found entanglement removal often did not hurt. Add: VQC without the CNOT ring; hybrid QNN with the quantum layer replaced by a same-size classical layer.
4. **Embedding choice.** PMC13360165 reports Z-rotation embedding collapsing to chance while X/Y rotations work. Verify ours (RY encoding for VQC; confirm the QSVM feature map is not effectively Z-only) and add a short embedding comparison.
5. **Kernel-target alignment training** was the one approach competitive in 2604.18837, but at roughly 2,000x cost. Consider a small, time-boxed version (few parameters, a 150-row subsample) and report its cost honestly.
6. **Calibration and decision utility.** Add Brier score, expected calibration error, a reliability plot and a threshold analysis (sensitivity at fixed specificity). VQC calibration was a weakness in PMC13360165.
7. **Noise robustness.** We claim hardware compatibility without testing it. Add a noisy-simulator run (depolarising channel plus finite shots, for example p in {0.001, 0.01, 0.05, 0.1}) and report metric versus noise.
8. **External or second-cohort validation.** PMC13360165 retrains on a second cohort. We could train on one breast-cancer dataset and evaluate method-level on another, clearly labelled as such.
9. **Reporting standard.** Adopt TRIPOD+AI-style items in the README (data source, split, leakage control, calibration, limitations).

## 3. Plan for the next experiment round (hypotheses, not promises)

- H1: Tuning bandwidth by nested CV raises QSVM accuracy on both datasets. Metric: accuracy/AUC vs current untuned QSVM, same folds.
- H2: More epochs plus a data re-uploading layer lifts the heart-disease VQC above its current 0.667 accuracy. Metric: accuracy/AUC, same folds.
- H3: Entanglement ablation shows no significant drop (expected from the literature). Report either way.
- H4: Quantum metrics degrade gracefully up to p = 0.05 depolarising noise. Report the curve.

Success is not "quantum beats classical"; it is a fairer, tuned, significance-tested comparison with an honest conclusion.

## 4. Sources
- Benchmarking Quantum Kernel SVMs Against Classical Baselines on Tabular Data: https://arxiv.org/abs/2604.18837
- Robustness-Oriented Quantum-Classical Hybrid ML Pipeline for Breast Cancer Diagnosis: https://pmc.ncbi.nlm.nih.gov/articles/PMC13360165/
- Better than classical? The subtle art of benchmarking QML models (Bowles, Ahmed, Schuld): https://www.alphaxiv.org/abs/2403.07059
- Benchmarking Quantum and Classical ML Models on Oncological Data: https://arxiv.org/html/2608.11373v1
- Adaptive quantum kernel selection via leakage-free stacking (not read; page blocked): https://pmc.ncbi.nlm.nih.gov/articles/PMC13518982/
