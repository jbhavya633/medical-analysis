# Learn From: Reference Projects, Papers and Architectures (SIH26139)

Compiled 2026-10-09 by web search; each repo and paper below was opened and read (Kaggle notebooks: titles only, not verified). Self-reported results are the authors' own and are not comparable with ours.

## Rules for using these sources
- Learn ideas and methods. Do NOT copy code. Repos A1-A4 are other teams' projects for the SAME problem statement (competitors) and show no licence, so all rights are reserved by default.
- Only B5, B6, B8 have open licences (Apache-2.0, MIT, MIT); even so, credit anything reused.
- Never compare another paper's numbers with ours; compare only what we ran on our own folds.
- Keep an idea only if our own 5-fold benchmark (seed 42) improves.

## A. Projects solving the same problem statement
| # | Source | Learn | Caveat |
|---|---|---|---|
| A1 | https://github.com/dhanasai2/QuantumDx (FastAPI, Next.js, Qiskit, XGBoost) | 4-qubit circuit run on real IBM hardware (ibm_marrakesh); quantum residual corrector on XGBoost; TreeSHAP; FHIR input parsing; PDF reports | Own table: hybrid AUC 0.837 vs XGBoost 0.857; pure VQC 0.607. No licence. |
| A2 | https://github.com/abcreativeakshay/hybrid-qml-disease-detection (Streamlit, PennyLane) | Live threshold slider (sensitivity/specificity update), risk bands, precomputed "quick demo" plus live-training modes | No numbers reported. No licence. |
| A3 | https://github.com/ushakiran45/SIH26139-Hybrid-QML | Retinal images -> EfficientNet-B3 -> PCA(4) -> VQC vs SVM; Grad-CAM; Docker deploy; honest "VQC does not beat SVM" | README admits its threshold was tuned on the sample, so numbers are optimistic. No licence. |
| A4 | https://github.com/sharvilmesh/QuantumDiseaseAI | Five-stage preprocessing pipeline; plain-language per-patient explanations | 2 commits, no results shown. No licence. |

Unverified extras found in search (not opened): https://github.com/sritharanvenkatesan-lab/sih-hybrid-qml, https://github.com/7pavana/SIH-AlgoX, https://github.com/prasanna01-hub/hybrid-quantum-machine-learning-platform

## B. Quantum, ML and simulator tooling
| # | Source | Learn |
|---|---|---|
| B5 | https://github.com/XanaduAI/qml-benchmarks (Apache-2.0) | scikit-learn-style harness, grid hyperparameter search, data re-uploading classifier; template for fair tuning |
| B6 | https://github.com/mit-han-lab/torchquantum (MIT) | GPU statevector simulator in PyTorch (30+ qubits multi-GPU), quantum kernel / quanvolution examples, parameter-shift training. Docs list Python 3.7-3.9: check compatibility with our Python before adopting |
| B7 | https://arxiv.org/abs/2107.10845 (QuantumNAS) | Noise-adaptive circuit + qubit-mapping search; iterative gate pruning |
| B8 | https://github.com/fatimasood/XAI-Hybrid-Quantum-Liver-Disease-Detection (MIT) | Kernel SHAP, Integrated Gradients, permutation importance, and a feature-ablation check that removes top-ranked features |

## C. Papers
| # | Source | Learn | Caveat |
|---|---|---|---|
| C9 | https://www.nature.com/articles/s41598-025-33825-7 (Ghisoni et al., Sci Rep 2026) | 460 VQCs vs 4,480 NNs on heart disease: angle > amplitude encoding (about 83-87% vs 80-82%); data re-uploading and higher learning rate helped; best VQC 86.84% vs best NN 86.67%; quantum better with 10-50% of the data | Noiseless; no hardware; no formal significance tests; internal inconsistency on best layer count |
| C10 | https://www.nature.com/articles/s41598-025-09957-1 (Kumar et al., Sci Rep 2025) | Quantum-inspired feature selection/tuning + QSVM: 97.83% vs 94.02% with 7 vs 9 features | Classical side uses GA+PSO; simulator; no code link |
| C11 | https://www.nature.com/articles/s41598-024-74778-7 (QCCNN breast cancer, Sci Rep 2024) | Quantum convolutional layer + classical head (PennyLane+PyTorch); WDBC up to 97.7% | Reports per-run highs; no AUC or timing |
| C12 | https://arxiv.org/abs/2604.18837 | Nested CV on 9 datasets; no significant quantum win; kernel-target-alignment training only competitive, ~2000x cost | Abstract-level read |
| C13 | https://www.alphaxiv.org/abs/2403.07059 (Bowles, Ahmed, Schuld) | Fair-benchmark method; entanglement ablations; classical usually wins | |
| C14 | https://pmc.ncbi.nlm.nih.gov/articles/PMC13360165/ | External validation, calibration, depolarising-noise tests, explainability surrogate; X/Y rotation embeddings work, Z collapses | |

## D. Kaggle notebooks (titles only; verify licence and quality)
- https://www.kaggle.com/code/dev523/quantum-kernel-machine-learning
- https://www.kaggle.com/code/georgiosgiapitzakis/quantum-variational-classifier
- https://www.kaggle.com/code/prakharsinghchouhan/quantum-transfer-learning-via-pennylane-and-resnet/notebook

## E. Network designs to implement (own implementation)
1. Data re-uploading VQC with angle encoding (B5, C9).
2. Dressed quantum circuit: classical layer -> quantum layer -> classical layer (C13).
3. Quantum residual corrector on a strong classical model (A1).
4. Quantum convolutional feature layer, only if imaging is added (C11).

## F. Gaps vs strongest rivals
Real-hardware run (A1); live threshold slider and risk bands (A2); interoperability and report export (A1); deployed live demo (A3).
