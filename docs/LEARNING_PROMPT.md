# Learning prompt for Claude Code (study the curated sources, draw inferences, plan the optimisation)

Paste the block into `claude` in the repo root. It studies every source in `docs/LEARN_FROM.md` and `docs/RELATED_WORK.md`, draws cross-source inferences, validates the top ideas with small throw-away experiments, and writes an optimisation plan and a simulator plan. It does not change application code and does not implement the improvements; run `docs/IMPROVEMENT_PROMPT.md` afterwards.

```
MISSION
Learn from the curated resources, draw inferences from them, and work out how to optimise OUR project: a hybrid quantum-classical platform for early disease detection (SIH26139). Output is understanding plus a ranked, evidence-backed plan. Do NOT implement the improvements yet. Work autonomously; ask no questions. If unsure, re-read this prompt.

OUR PROJECT (verify these facts from README.md and backend/ml/quantum/results/summary.json before using them; correct me if they differ)
- 6 qubits, at most 200 training rows per fold, 5-fold stratified CV, seed 42, same rows for every model.
- Datasets: UCI Breast Cancer Wisconsin, UCI Heart Disease (Cleveland).
- Models: LogReg, RBF-SVM, RandomForest, MLP; quantum-kernel SVM (ZZ-style feature map, statevector kernel); VQC (RY angle encoding, RY/RZ + CNOT ring, 2 layers); hybrid QNN (Linear -> TorchLayer -> Linear). 40 epochs, simulator only (PennyLane default.qubit).
- Baseline (copy exact numbers from summary.json): the quantum models match classical on breast cancer but trail on heart disease; the VQC is weakest on heart disease.

RULES
- Edit or create only: docs/LEARNING_LOG.md, docs/INFERENCES.md, docs/OPTIMIZATION_PLAN.md, docs/SIMULATOR_PLAN.md, and files under scratch/ (git-ignored). Do not touch backend/ or src/.
- Never copy code from any source. Never clone or mirror repos that show no licence (docs/LEARN_FROM.md section A: read those online only and note ideas in your own words). Do not download anything; read with the web tools, the alphaxiv / PubMed / Hugging Face / Context7 connectors, and the PennyLane skill.
- Every claim needs a source URL plus the section, table or figure it came from. Mark anything you could not open as UNVERIFIED. Never invent a number, a result or a citation.
- Other papers' numbers are not comparable with ours. Only numbers produced by running OUR code count as evidence for us.
- Do not push anywhere. Commit locally in small commits only if I ask.

STEP 1 - SOURCE LIST
Read docs/LEARN_FROM.md and docs/RELATED_WORK.md. Check each source is reachable; list blocked ones.

STEP 2 - STUDY IN FIVE TRACKS (read each source properly, not just abstracts; fall back to abstract only when blocked and say so)
T1 Quantum neural networks: Ghisoni et al. (Sci Rep 2026, heart disease: encoding, data re-uploading, depth, dropout, learning rate, sample complexity), XanaduAI/qml-benchmarks (data re-uploading classifier, benchmark protocol), the quantum-convolutional breast-cancer paper, Bowles et al. (dressed circuits, ablations), QuantumDx's residual-corrector idea (read online).
T2 Quantum kernels: arXiv 2604.18837 (spectra, bandwidth, kernel-target alignment training and its cost), PMC13360165 (ZZ-fidelity QSVM was untuned and weak), Kumar et al. (quantum-inspired feature selection with QSVM).
T3 Machine learning and training practice: nested CV and equal tuning budgets, feature selection under a qubit budget (RFECV, mutual information, PCA), calibration and decision utility, statistical testing, reporting standards (TRIPOD+AI as used in PMC13360165).
T4 Simulators and noise: TorchQuantum (GPU statevector, qubit scaling, QNN examples; check its Python/PyTorch support against our environment), QuantumNAS (noise-adaptive circuit search, gate pruning), PennyLane device options (default.qubit, lightning, noisy channels, shots), Qiskit Aer noise models, circuit transpilation and gate counts via the qiskit MCP.
T5 End-to-end early-detection platforms: the four SIH26139 projects and the liver-disease XAI repo (read online): explainability methods, threshold slider and risk bands, FHIR input, report export, deployment, honest reporting.

For each source append to docs/LEARNING_LOG.md:
 (a) technique in 2 sentences, your own words; (b) the claim and its evidence (dataset, metric, n, tuning protocol); (c) strength of evidence (strong / moderate / weak, with why: tuning fairness, dataset size, significance tests, noise, hardware); (d) transfer to OUR setting (6 qubits, <=200 rows, two small tabular medical datasets): likely / uncertain / unlikely, with reasons; (e) one testable hypothesis with metric, folds and expected cost in minutes.

STEP 3 - DRAW INFERENCES (docs/INFERENCES.md)
Synthesise across sources, not source by source:
1. Where sources AGREE (for example: tuning fairness matters, dataset choice dominates, quantum parity at best on small tabular data) and the confidence in each.
2. Where they CONFLICT or are inconsistent (for example: reports of quantum gains versus controlled benchmarks) and the likely reason (baseline strength, tuning budget, simulator vs hardware, dataset).
3. What this implies for each of our weak points: heart-disease VQC, QSVM bandwidth, equal tuning, ablation, calibration, noise. For each: the inference, the strength of evidence, the uncertainty, and what result would CHANGE the inference.
4. Which techniques cost too much for our 60-minute-per-experiment budget (for example kernel-target alignment training at about 2,000x) and what cheaper variant could capture the idea.
5. A short list of "claims we should NOT make" given the evidence.

STEP 4 - SANDBOX CHECKS (scratch/ only; exploratory, never reported as results)
For the top five hypotheses, run the smallest experiment that tests feasibility and cost, importing our package read-only: one dataset, 1-2 folds, a few epochs. Record: runtime, whether it runs, rough direction of effect, and the biggest risk. Label every output "exploratory, n too small for conclusions". Delete nothing; leave scripts in scratch/.

STEP 5 - OPTIMISATION PLAN (docs/OPTIMIZATION_PLAN.md)
Rank 8-12 experiments by (expected gain x confidence) / cost. For each: hypothesis; evidence behind it (cite LEARNING_LOG entries); exact design (folds, seeds, nested-CV inner search space, what stays fixed for fairness); metrics and the statistical test; which files/modules in backend/ml/quantum/ would change; cost in minutes; success criterion; stopping rule; leakage and tuning pitfalls to avoid. Cover at least: nested-CV tuning of all models with equal budgets; data re-uploading and dressed-circuit variants; entanglement and quantum-layer ablations; QSVM bandwidth tuning; feature-selection and qubit-count sweep; calibration and sensitivity at fixed specificity; noisy simulation; a simulator backend comparison; a second dataset; an explainability validation by feature ablation.

STEP 6 - SIMULATOR PLAN (docs/SIMULATOR_PLAN.md)
Design (do not build) a simulator layer for early-disease-detection experiments in this project: backend options and trade-offs (PennyLane default.qubit / lightning, TorchQuantum, Qiskit Aer), how to select a backend by config, noise channels and shot settings, qubit-scaling limits on this laptop (measure the time for 4, 6, 8, 10 qubits with a small circuit in scratch/), reproducibility (seeds, versions), result schema, and how the Quantum Lab page would expose it. State which parts need no new dependency.

STEP 7 - CHECKPOINT QUESTIONS (answer in docs/INFERENCES.md, citing file and line in our code)
1. Where in our pipeline would nested-CV tuning go without touching outer test folds? 2. Is feature selection fitted on training folds only? 3. How are folds and the 200-row subsample kept identical across models? 4. Which two baseline results are weakest and what do the sources suggest about each? 5. Name three ways an "improvement" could be invalid in our setup.

FINAL REPORT (max 25 lines)
Number of sources read in full versus abstract-only versus blocked; the five strongest inferences with confidence; the top five experiments with expected cost; claims we should avoid; anything needing my approval (downloads, connector toggles). Stop after the report. Do not start implementing.
```
