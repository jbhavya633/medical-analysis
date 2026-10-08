# SIH26139 demo script (3 minutes)

Before you start: run `bash scripts/run_demo.sh` (or `SKIP_BENCHMARK=1 bash scripts/run_demo.sh` to use
the committed results), log in to the app, and keep a terminal plus `http://localhost:8000/docs` open
in background tabs.

| Time | Show | Say |
|---|---|---|
| 0:00-0:20 | Quantum Lab page, the amber banner | "This is a research prototype for SIH26139: hybrid quantum-classical ML for early disease detection. It is not a diagnostic tool - everything runs on a quantum simulator using public benchmark data." |
| 0:20-0:50 | `docs/architecture.svg` (README) | "Classical preprocessing imputes, standardises and picks one feature per qubit with mutual information, then scales them to rotation angles. Three quantum models sit next to four classical baselines and see exactly the same folds and rows." |
| 0:50-1:30 | Comparison table, Breast cancer then Heart | "Stratified 5-fold CV, seed 42. Read the accuracy, sensitivity, specificity and AUC columns: on breast cancer the VQC and hybrid QNN match the classical models; on heart disease every quantum model trails. Training cost is about 10 seconds per fold versus milliseconds." |
| 1:30-1:55 | ROC chart (toggle Quantum / Classical), learning curve | "ROC uses pooled out-of-fold predictions. The learning curve shows how validation accuracy grows with data - our measure of generalisation, together with the train-validation gap." |
| 1:55-2:20 | Model = Quantum-kernel SVM, importance chart | "Explainability: permutation importance on the held-out split, SHAP for every model, and for the quantum kernel its kernel-target alignment and how sensitive the feature map is to each input." |
| 2:20-2:45 | Click Train, watch the job finish; fill 2-3 fields and click Predict | "Training runs as a background job through the API. A prediction returns P(disease) plus per-feature SHAP contributions - and the disclaimer again." |
| 2:45-3:00 | `/docs` Swagger and the terminal running `pytest` | "Everything is reproducible from one command, covered by tests and CI, and every number in the README and deck comes from the logged run in `results/`." |
