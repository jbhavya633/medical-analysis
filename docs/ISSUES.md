# SIH26139 plan as issues

`origin` (jbhavya633/medical-analysis) is not owned by SoubhagyaTripathi, so no GitHub issues were
filed. This list stands in for the epic and its issues.

## Epic: SIH26139 Hybrid QML platform

### Phase 1 - audit and fixes
- [x] Truthful model loading for ECG / X-ray / CT; 503 when weights are missing (`afec5d5`)
- [x] Frontend build, type-check and runnable lint; demo-data banner (`cfa95b3`)
- [x] Fix unterminated f-string and remove hardcoded `C:\Users\ASUS` paths (`2e85a8e`)
- [ ] Mortality model leakage fix (work in progress, stashed; out of scope for SIH26139)
- [x] CORS from env, generic error bodies with request ids, request size limit (`backend/main.py`)
- [ ] Supabase auth dependency on `/api/analyze/*` and RLS for the existing schema (not started)
- [x] `.env.example`, `.gitignore`, untrack `ecg.err`, project `CLAUDE.md`
- [ ] Pre-existing ESLint backlog (45 errors, 2 warnings; non-blocking in CI)

### Phase 2 - hybrid QML module
- [x] Data loaders with cache (breast cancer, heart) and preprocessing (impute, scale, MI/PCA, angles)
- [x] Classical baselines (logistic regression, RBF-SVM, random forest, MLP)
- [x] Quantum-kernel SVM with ZZ-style feature map and batched statevector kernel
- [x] Variational quantum classifier (hardware-efficient ansatz)
- [x] Hybrid QNN (TorchLayer)
- [x] Explainability (permutation, SHAP, kernel alignment, feature-map sensitivity)
- [x] Evaluation (stratified 5-fold, efficiency, generalisation gap, learning curves) and benchmark CLI
- [x] `/api/qml` router + service with background jobs
- [x] Optional migration `backend/db/migrations/001_qml.sql` (not applied)

### Phase 3 - frontend
- [x] Quantum Lab page, route and nav entry
- [x] Comparison table, ROC, learning curves, importance chart, prediction with explanation, disclaimer

### Phase 4 - tests and CI
- [x] pytest for the QML package and API contracts (97% coverage)
- [x] vitest for Quantum Lab
- [x] GitHub Actions workflow with caching, timeouts, pinned actions, coverage gate
- [ ] Run the workflow on GitHub (needs a repo you own)

### Phase 5 - docs and submission
- [x] README with architecture diagram, results, limitations, ethics, Delivery Table
- [x] SIH idea deck
- [x] 3-minute demo script
