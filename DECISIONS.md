# DECISIONS

Log of autonomous decisions taken during the SIH26139 build (one line each).

- 22:07 Unfinished Phase-1 Fix 4 (Synthea mortality rewrite) stashed as `stash@{0}` because the SIH26139 spec puts Synthea out of scope; not committed.
- 22:07 `origin` is jbhavya633/medical-analysis (not SoubhagyaTripathi) -> no push, no issues/PRs; plan written to docs/ISSUES.md instead.
- 22:07 `/idd:*`, `/ci-optimizer:*`, `/code-review-plugin:*` are not installed -> equivalent steps done directly; built-in /code-review used for review.
- 22:07 Hadamard in the ZZ feature map replaced by RY(pi/2) so every circuit uses only RX/RY/RZ/CNOT (hardware-native set stated in the spec).
- 22:14 Every training fold is stratified-subsampled to 200 rows for ALL models (classical too), and classical baselines get the same 6 selected features, so the comparison is like-for-like.
- 22:15 QSVM trails classical (low kernel alignment). Kept the a-priori ZZ map without bandwidth tuning to avoid tuning on validation folds; analysis in README Limitations.
- 22:16 SHAP is noisy at INFO level -> shap logger set to WARNING in the benchmark.
- 22:24 Benchmark re-run on committed code (commit 9409691) so summary.json records the code that produced it; numbers identical to the first run (timings differ slightly, as expected).
- 22:27 GitHub Actions SHAs pinned from known release tags (checkout v4.2.2, setup-node v4.1.0, setup-python v5.3.0); verify on first CI run since CI cannot run here (repo not owned).
- 22:28 No LibreOffice/pdftoppm and the browser pane cannot open local files -> no rendered visual QA of docs/architecture.svg or the deck; deck passes the pptx skill's structural validator.
- 22:28 No Playwright -> no UI screenshots in the deck; ROC plot from the logged run used instead.
- 22:33 README results tables generated from results/summary.json by a script and re-checked for an exact match.
- 22:35 Saved model artifacts embed 20 background rows of the public UCI datasets (needed for SHAP at predict time); these are de-identified public benchmark rows, not private patient data.
- 22:39 Code review (built-in /code-review, 9 findings): fixed gen-gap decision-rule mismatch, demo-data banner shown above real Quantum Lab results, stale job model in the prediction panel, size-limit bypass without Content-Length (now 411), stale artifact cache (mtime in cache key). Logged, not fixed: synchronous SHAP per /predict (acceptable for a demo), global RNG reseeding inside SHAP/torch (affects only concurrent-job reproducibility), unbounded in-memory job registry, Flask servers bound to 127.0.0.1 (kept as the safer default).
- 22:44 Final benchmark at commit 0413f33 (after review fixes); accuracy/sensitivity/specificity/AUC/F1 unchanged, SVM gap values and timings moved slightly. README and deck regenerated from it.
