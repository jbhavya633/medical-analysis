# Learn From: Addendum (sources found after docs/LEARN_FROM.md)

Compiled 2026-10-09. Read for ideas and methods; never copy code. Numbers in these papers belong to their own splits and are NOT comparable with ours. Status tags: [opened] = a summary of the page was read in the research session; [search-verified] = the URL appeared in search results but was not opened; [verify] = identifier written from memory, must be checked and marked UNVERIFIED if it does not resolve. Several papers below contain internal inconsistencies noted under "Caveat".

## G. "Quantum beats classical" claims found in the research session (study how they win, and why it is fragile)
| # | Source | Learn | Caveat |
|---|---|---|---|
| G1 | https://arxiv.org/html/2604.24597v1 (QSVM on medical foundation-model embeddings) [opened] | Linear kernel collapses to the majority class because its effective rank equals the PCA dimension; quantum kernel keeps a higher effective rank. Settings that mattered: trace-normalised kernel, one rotation per feature, one repetition, rank-matched RBF as the fair control | Main win is against an UNTUNED linear SVM; vs tuned RBF the gain is small; data stratum chosen after seeing results; simulation only; task is insurance type, not disease |
| G2 | https://arxiv.org/html/2511.10831v1 (quantum kernels across diverse data) [opened] | Scaling parameter on the RZ angle, kernel-target-alignment training, MinMax scaling sensitivity, circular CNOT ansatz, two-stage random search | Quantum kernels stopped once they matched the baseline while classical kernels got a full grid; single accuracy, no variance; subsampled and PCA-reduced data |
| G3 | https://arxiv.org/html/2508.19437 (data-efficient learning with quantum kernels) [opened] | Method to compare sample efficiency through target-alignment spectra and learning curves at N = small | Advantage only on labels engineered for the quantum kernel; no evidence for natural labels |
| G4 | https://arxiv.org/html/2602.14641 (quantum reservoir on 108 patients) [opened] | Feature subsets of 5-7 top-SHAP features beat all 56 features for classical models; nested splits with inner 10-fold search; hardware features lowered variance | Noiseless QRC did not beat classical; no matched classical baseline on hardware features; possible leakage via aggregated SHAP ranking |
| G5 | https://www.nature.com/articles/s41598-026-35605-3 (MedMNIST on IBM hardware) [opened] | Noise-resilient circuit selection (Clifford noise resilience score), error suppression and mitigation, accuracy-per-parameter framing (60-120 parameters) | Does not beat best classical; circuits classically simulable; no cross-validation; few hardware repeats |
| G6 | https://arxiv.org/pdf/2408.12739 (QCNNs are effectively classically simulable) [opened] | "Locally-easy" datasets; why shallow embeddings with local measurements are classically simulable; burden of proof sits with the quantum claim | Heuristic, average-case argument |
| G7 | https://arxiv.org/abs/2211.16551 (evidence against advantage with fidelity kernels) [opened] | Tuning that restores generalisation pushes a quantum kernel toward a classical one; spectrum flattening with qubit count | Abstract-level read |
| G8 | https://arxiv.org/pdf/2509.16410 (data complexity threshold, Part I) [opened] | Cheap dataset diagnostics: intrinsic dimension, interaction order, compressibility, kernel effective dimension | Conceptual framework; thresholds not validated |
| G9 | https://arxiv.org/html/2609.24666v1 (few-shot generalisation of a QCNN) [opened] | Learning curves at N = 2..80 with repeated draws; parameter-matched classical control; transpiled depth and qubit scaling | Plain RBF-SVM and logistic regression beat the QCNN; authors disclaim advantage |
| G10 | https://arxiv.org/pdf/2511.20922v3 (readout-side bypass) [opened] | Concatenate raw input with circuit output before the classical head | Parameter counts not matched; inconsistent tables; still below classical |
| G11 | https://arxiv.org/html/2512.20654v1 (Q-RUN, classical re-uploading) [opened] | A classical "twin" of the re-uploading idea tests whether quantumness matters | Mixed wins; some claims overstated |
| G12 | https://arxiv.org/pdf/2601.03375 (projected quantum kernels, small data) [opened] | Idea only: projected features from reduced density matrices | Conflicting numbers between abstract and body, no variance, no tuning details: do not rely on it |
| G13 | https://postquantum.com/quantum-ai/quantum-machine-learning-reality/ [opened] | Five filters for any quantum claim: primary evidence, simulator vs hardware, tuned classical baseline, data-loading cost, natural vs constructed data | Secondary review |
| G14 | https://research.ibm.com/blog/quantum-kernels [opened] | The proven kernel advantage needs discrete-log structured data | Not applicable to tabular or medical data |

## H. New sources to study (15)
| # | Source | Why it matters for us | Test in our project |
|---|---|---|---|
| H1 | Demsar 2006, Statistical Comparisons of Classifiers over Multiple Data Sets, https://www.jmlr.org/beta/papers/v7/demsar06a.html [search-verified] | Friedman test, Wilcoxon-Holm and critical-difference diagrams for 10+ datasets | Cross-dataset ranking and CD diagram |
| H2 | Cawley and Talbot 2010, On Over-fitting in Model Selection, https://www.jmlr.org/papers/v11/cawley10a.html [search-verified] | Why tuning on the evaluation folds inflates results | Audit that no outer test fold touches tuning |
| H3 | Varoquaux 2018, Cross-validation failure: small sample sizes lead to large error bars, arXiv 1706.07581 [verify] | Error bars on small medical sets are wide | Repeated CV, report intervals, corrected resampled t-test |
| H4 | Grinsztajn et al. 2022, Why do tree-based models still outperform deep learning on tabular data, https://arxiv.org/abs/2207.08815v1 [search-verified] | Tabular benchmark protocol with random-search budget curves | Equal-budget curves per model family |
| H5 | Bischl et al., OpenML Benchmarking Suites, arXiv 1708.03731 [verify] | How to define and document a benchmark suite | Dataset registry with checksums and licences |
| H6 | Thanasilp et al., Exponential concentration in quantum kernel methods, https://arxiv.org/pdf/2208.11060 [search-verified] | When kernels concentrate and become untrainable | Track off-diagonal mean and effective rank per dataset |
| H7 | Hubregtsen et al., Training quantum embedding kernels on near-term quantum computers, arXiv 2105.02276 [verify] | Kernel-target alignment training recipe | Time-boxed alignment training on a 150-row subsample |
| H8 | Kubler et al., The inductive bias of quantum kernels, arXiv 2106.03747 [verify] | Bandwidth and projection explain when a quantum kernel helps | Interpret the bandwidth sweep |
| H9 | Schuld, Sweke and Meyer, Effect of data encoding on the expressive power of variational quantum machine learning models, arXiv 2008.08605 [verify] | Circuit = truncated Fourier series; encoding sets the available frequencies | Explain input-scaling and re-uploading results; test frequency-limited classical twin |
| H10 | Schreiber, Eisert and Meyer, Classical surrogates for quantum learning models, arXiv 2206.11740 [verify] | Fit a classical surrogate from the trained circuit | Surrogate fidelity as a "does quantum matter" check |
| H11 | Perez-Salinas et al., Data re-uploading for a universal quantum classifier, arXiv 1907.02085 [verify] | Origin of re-uploading | Layer-wise re-uploading variant vs 3-layer control |
| H12 | Havlicek et al., Supervised learning with quantum-enhanced feature spaces, arXiv 1804.11326 [verify] | Origin of the ZZ feature map our QSVM uses | Check our map against the original and note differences |
| H13 | PennyLane demos: https://pennylane.ai/demos/tutorial_kernels_module and https://pennylane.ai/demos/tutorial_kernel_based_training [search-verified] | Reference implementations of kernel training | Read for ideas only; own implementation |
| H14 | TRIPOD+AI statement, BMJ 2024;385:e078378 [verify] | Reporting checklist | Map each item to a README/technical-report section |
| H15 | Van Calster et al. 2019, Calibration: the Achilles heel of predictive analytics, BMC Medicine [verify] | Why calibration decides clinical usefulness | Calibration slope and intercept, decision curves |

## How to use
1. Study G and H in docs/LEARNING_LOG.md using the same five-part template (technique, claim and evidence, strength of evidence, transfer to our setting, testable hypothesis with cost).
2. Add cross-source inferences to docs/INFERENCES.md; mark conflicts (for example G1/G2 wins vs G7/G6 skepticism) and what result would change each inference.
3. Convert each hypothesis into a numbered experiment in docs/OPTIMIZATION_PLAN.md with a pre-registered stopping rule.
