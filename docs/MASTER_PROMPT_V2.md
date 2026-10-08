# Master prompt v2: multi-dataset benchmark, platform upgrade and SIH26139 deliverables (autonomous, long-running)

Launch from the repo root in `claude` with this single line:

    Read docs/MASTER_PROMPT_V2.md in full and execute it exactly. Re-read it whenever you are unsure or after any context compaction.

Everything below the line is the prompt.

---

MISSION
Make this hybrid quantum-classical early-disease-detection platform (SIH26139) significantly better than the version tagged `v1-baseline`, and finish every SIH deliverable end to end. Work autonomously for as many hours as it takes. Ask no questions and request no approvals: everything this prompt needs is authorised here. "Better" means more rigorous, broader, more usable and more honest. It does NOT mean claiming quantum advantage. Real results only.

PRE-AUTHORISED (do these without asking)
- Install Python packages into the repo's .venv and npm packages into the repo (only what a phase needs; record each in docs/DECISIONS.md).
- Download the datasets listed in docs/KAGGLE_DATASETS.md (Kaggle via the user's existing credentials, otherwise the UCI / OpenML fallbacks) into the git-ignored data/ folder, and read the papers in docs/LEARN_FROM_ADDENDUM.md.
- Create the files and modules this prompt names, run long background jobs, and make small local commits.

NEVER, even though no approvals are asked (if blocked, log it in docs/PROGRESS.md and route around it)
- Push to `origin` (push only to a remote named `mine`, and only if the user asks later). No force-pushes.
- Read, type, print, log or commit credentials, keys or tokens. If Kaggle credentials are missing, use the fallbacks.
- Publish or deploy anything publicly (Vercel, GitHub Pages, remote Supabase migrations), submit jobs to real quantum hardware or any paid service, send messages or e-mails.
- Delete anything outside this repo, change system, power, security or network settings, bypass CAPTCHAs or paywalls, or work around a tool permission refusal.
- Commit raw dataset files. Copy code from any source, or clone repos with no licence (docs/LEARN_FROM.md section A).
- Quote any number that did not come from results/*.json produced by our committed code. Nothing from scratch/ is ever quoted.

NEW ASSUMPTIONS (these replace the earlier ones where they conflict)
A1. On small tabular medical data the most likely outcome is quantum parity with tuned classical models, and a tuned QSVM already ties LogReg. Plan for parity; report any win or loss exactly as it comes.
A2. Everything runs on CPU simulators on this laptop. First measure cores and RAM; set job counts and run budgets from the measurements. Never change power settings; make every long job resumable (checkpoint per dataset x model x fold) so sleep or restart loses nothing.
A3. Evidence needs breadth: 12 or more datasets, a pre-registered dev/confirmation split, repeated CV, equal tuning for every model, and multi-dataset statistics (Friedman, Wilcoxon-Holm, critical-difference diagram, corrected resampled t-tests per dataset).
A4. The platform must be usable by a clinician-style demo user: upload a CSV, get a tuned comparison, calibrated risk, threshold control, explanation, and a downloadable report.
A5. Judges value honest, reproducible, well-documented work over inflated claims. Each claim carries its evidence file.
A6. Windows + PowerShell host. Use UTF-8 explicitly in all file I/O (PYTHONUTF8=1, encoding="utf-8"); a mojibake bug already occurred once.
A7. Earlier "no new abstractions" is relaxed to: add only the modules named below, keep routers delegation-only, and justify each new module in docs/DECISIONS.md.

DEFINITION OF DONE (all must be green; track in docs/PROGRESS.md as a checklist with the evidence file for each)
D1  `v1-baseline` git tag exists at commit 0d9b07c (or the last commit before the development round) and a scorecard compares it with HEAD.
D2  At least 12 datasets pass the acceptance rules in docs/KAGGLE_DATASETS.md and are benchmarked (the 2 built-in ones plus at least 10 others), each with a registry entry, checksum, licence, provenance and leakage notes.
D3  docs/PREREGISTRATION.md was committed BEFORE any multi-dataset result was viewed (dev set, confirmation set, primary metric AUC, secondary metrics, hypotheses, tests, stopping rules).
D4  Every model is tuned by nested CV with the same budget: LogReg, RBF-SVM, RandomForest, MLP, HistGradientBoosting (new strong baseline), tuned-bandwidth QSVM, the best VQC variant(s), hybrid QNN, raw+quantum residual head, and the controls (parameter-matched classical MLP, classical twin of the re-uploading circuit, VQC without CNOT ring, hybrid QNN with classical layer).
D5  Multi-dataset statistics produced: per-dataset corrected resampled t-tests with Holm correction, Friedman + Wilcoxon-Holm across datasets, critical-difference diagram, win/tie/loss table, effect sizes with confidence intervals.
D6  Data-complexity analysis: kernel effective rank, intrinsic dimension, class balance, n, d versus the quantum-minus-classical AUC gap across datasets, with an honest reading (docs/INFERENCES.md).
D7  Calibration (Brier, ECE, slope/intercept, reliability plots), sensitivity at 90% and 95% specificity, and decision curves for every dataset.
D8  Simulator layer per docs/SIMULATOR_PLAN.md: backend selection by config (default.qubit, lightning if installed, default.mixed for noise), two-qubit-gate depolarising noise, finite shots, qubit-scaling timings for 4, 6, 8, 10 qubits, a Qiskit transpile with gate counts via the qiskit MCP. Noise results are reported as degradation curves, not as "robustness".
D9  Explainability validated by feature ablation (top-k removal vs random removal) on at least 5 datasets; per-patient explanation with plain-language text.
D10 Platform features working and tested: dataset registry endpoint and picker for all datasets; CSV upload with schema checks, size limits, target selection and no-PHI warning; automatic feature selection to the qubit budget; background benchmark run; cross-dataset results page (rank table, CD diagram, win/tie/loss); threshold slider with risk bands from saved predictions; calibration view; backend and noise selector; model cards; PDF and JSON report export; a generated "Findings and limits" page that lists claims allowed and not allowed from the JSON.
D11 Reproducibility: `scripts/reproduce.(sh|ps1)` rebuilds every table and figure from raw data checksums; versions pinned; result schema documented; Dockerfile and compose written and, if Docker exists locally, built (never pushed).
D12 Quality gates green on HEAD: pytest with coverage >= 80% on backend/ml/quantum (target the earlier 97%), type-check, build, vitest, CI workflow valid, secrets scan clean, /code-review run on each phase with high/critical findings fixed.
D13 SIH deliverables regenerated from the final JSON only and script-checked: README, Delivery Table, docs/DEMO_SCRIPT.md, architecture diagram, idea deck (.pptx), technical report in TRIPOD+AI style (docs/TECHNICAL_REPORT.md), one-page abstract, 3-minute pitch script, judge Q&A (at least 25 hard questions with evidence-backed answers), model card, limitations section, and a numbers-consistency script (`scripts/check_numbers.py`) that fails if any quoted number differs from the JSON.
D14 Scorecard in docs/SCORECARD.md: v1-baseline vs final on dataset count, tuned models, statistical tests, calibration, noise, upload, explainability validation, tests, docs, plus the measured metric differences. "Significantly better" is judged by this scorecard.

STATE AND RESUMABILITY
Create docs/PROGRESS.md first. After every step update it: checklist D1-D14, current phase, last commit, running jobs with their log paths, decisions, blockers. If your context is compacted or a session restarts, re-read this prompt, docs/PROGRESS.md, docs/OPTIMIZATION_PLAN.md and docs/PREREGISTRATION.md before doing anything. Long jobs run in the background, write logs, and skip finished checkpoints when relaunched.

PHASES (run in order; do not stop between phases)

P0 Housekeeping (about 20 min)
Commit docs/LEARN_FROM_ADDENDUM.md, docs/KAGGLE_DATASETS.md, docs/MASTER_PROMPT_V2.md and any uncommitted work from the previous round in small atomic commits, running the quality gates first. Tag `v1-baseline`. Record machine cores/RAM, versions and baseline numbers in docs/PROGRESS.md.

P1 Study (time-box 60 min)
Study every source in docs/LEARN_FROM_ADDENDUM.md (G1-G14 and H1-H15) with the connectors available (alphaxiv, PubMed, Hugging Face, Context7, web) and the PennyLane skill. Append to docs/LEARNING_LOG.md in the five-part template, mark UNVERIFIED anything you could not open, and fix any identifier marked [verify] that does not resolve. Update docs/INFERENCES.md with cross-source inferences and conflicts (wins in G1/G2 vs skepticism in G6/G7), and extend docs/OPTIMIZATION_PLAN.md with new experiments: kernel effective-rank control (G1), RZ-scale and alignment training (G2, H7), top-k SHAP feature subsets of 5-7 (G4), raw+quantum residual head vs equal classical head (G10), classical twin and frequency-limited surrogate (G11, H9, H10), learning curves at N = 10, 20, 50, 100, 200 with parameter-matched controls (G9), noise-aware circuit choice (G5), data-complexity diagnostics (G8, H6). Cite clinical need for early detection with 5 or more PubMed citations (PubMed connector) for the deck and report.

P2 Pre-registration (about 30 min)
Write docs/PREREGISTRATION.md: dev and confirmation sets as defined in docs/KAGGLE_DATASETS.md, the protocol (seed 42; repeated stratified 5-fold with the same number of repeats for every model, set from measured cost; at most 200 training rows per fold; 6 qubits by default, qubit-count sweep as a separate experiment), metrics (primary AUC; secondary balanced accuracy, sensitivity at 95% specificity, Brier, ECE, MCC, train and predict time), tests (corrected resampled t-test with Holm per dataset; Friedman then Wilcoxon-Holm across datasets), hypotheses with direction and stopping rules, and the rule that a method change is kept only if it helps on the development set and is then reported unchanged on the confirmation set. Commit it before running anything on the confirmation datasets.

P3 Dataset layer (parallelisable)
Add the dataset registry (backend/ml/quantum/registry.py plus a data/ layout): declarative entries with name, source, licence, provenance, target rule, dropped columns with reasons, checksum, and a loader returning features and a binary label. Splitters, imputers, encoders, scalers and feature selection are fitted inside training folds only. Use parallel subagents, one per dataset, each returning a registry entry and a test; you integrate. Download each dataset, verify checksum, run schema and leakage checks, and record rows, features, class balance and missingness. Reject datasets that fail the acceptance rules and replace them from the candidate list until D2 holds. Unit-test every loader on a tiny fixture, not on the raw data.

P4 Multi-dataset benchmark
Extend the nested-CV harness to run all datasets and all D4 models with checkpointing and an equal budget per model (same number of configurations and inner folds). Run the development datasets first and write results/*.json per dataset and model. Make the design decisions allowed by the plan using development results only, then run the confirmation datasets once, unchanged. Produce all D5, D6 and D7 artefacts. Repeat any step that fails a leakage audit (outer test folds must never touch tuning, selection, scaling, imputation or encoding).

P5 Improvement loop (hours)
For each experiment in docs/OPTIMIZATION_PLAN.md in ranked order: state the hypothesis and stopping rule, run it on the development set, keep it only if it meets the criterion, then run the confirmation set once. At most two design iterations per experiment. Cover: VQC input scaling vs a 3-layer control with equal parameters, re-uploading, dressed circuit, entanglement and quantum-layer ablations, QSVM bandwidth plus time-boxed alignment training, effective-rank control, residual head, classical twin, feature-selection and qubit-count sweep, learning curves, data-complexity diagnostics. Record negative results with the same care as positive ones.

P6 Simulator and noise (D8)
Implement docs/SIMULATOR_PLAN.md: config-selected backend, two-qubit-gate depolarising noise on a 3-dataset subset (not a flat single-qubit channel presented as robustness), shot sweeps, qubit scaling timings, Qiskit transpile gate counts and depth via the qiskit MCP, reproducibility metadata (seeds, versions, backend) in the result schema. Do not submit anything to hardware.

P7 Explainability validation (D9)
Run top-k feature ablation versus random ablation on at least 5 datasets, with SHAP and the model-native importance, and report the AUC drop with intervals. Add plain-language per-patient explanations that name the top contributing features and direction, with a clear "not medical advice" notice.

P8 Platform (D10)
Build the listed API endpoints (delegation-only routers) and UI pages with tests: dataset picker, CSV upload (validate columns and types, cap file size and rows, reject obvious identifiers, show a no-PHI notice, never persist uploads unless the user opts in), run configuration, progress, cross-dataset results (rank table, CD diagram, win/tie/loss), calibration view, threshold slider with low/medium/high risk bands from saved predictions, backend and noise selector, model cards, PDF/JSON report export, and the generated "Findings and limits" page. Run vitest, type-check and build after each page. Check keyboard access and readable contrast on every new page.

P9 Hardening and reproducibility (D11, D12)
Write the reproduce script, pin versions, document the result schema, write the Dockerfile and compose (build if Docker exists), add a secrets scan, make CI pass, raise coverage, and run /code-review on every phase diff. Fix high and critical findings.

P10 Deliverables (D13, D14)
Regenerate the full tuned benchmark once from clean (all datasets and models), then generate every artefact from the final JSON: README results, Delivery Table, docs/DEMO_SCRIPT.md (with a timed 5-minute script and a fallback if the live demo fails), refreshed architecture.svg, the idea deck via a script (python-pptx or the pptx skill), docs/TECHNICAL_REPORT.md (TRIPOD+AI items mapped, limitations, ethics, data governance), one-page abstract, 3-minute pitch script, judge Q&A, model card, and docs/SCORECARD.md. Run scripts/check_numbers.py until clean. Make a docs/SUBMISSION_PACK/ folder collecting the final deck, report, abstract, pitch, Q&A, Delivery Table text and screenshots of the working UI taken from the local build.

LOOP RULE (this is what keeps you running for hours)
After P10, re-evaluate D1-D14. If any item is red or amber, create work items, fix them, re-run the affected gates and regenerate the affected artefacts, then re-evaluate. Stop only when every item is green, or when each remaining red item has three documented distinct attempts and is marked BLOCKED with evidence. Do not stop for questions, summaries or confirmations. Do not ask whether to continue.

IF STUCK
Re-read this prompt, then docs/LEARN_FROM.md, docs/LEARN_FROM_ADDENDUM.md, docs/INFERENCES.md and the PennyLane skill. Search with alphaxiv, PubMed, Hugging Face, Context7 and the web. Try three different approaches, record them in docs/DECISIONS.md, shrink the scope using the pre-registered fallback (fewer repeats, fewer epochs, fewer datasets above the minimum of 12), and move on. A tool permission refusal is a hard boundary: log it and continue with other work.

CLAIM POLICY (enforced by scripts/check_numbers.py and by reading every sentence you write)
Allowed only if our own pre-registered, significance-tested results support it: a specific model beats, ties or trails another on named datasets; improvement from tuning; calibration findings; noise degradation curves; accuracy per parameter versus matched controls; learning-curve findings.
Not allowed unless our results show it: quantum advantage in general, low-data advantage, hardware or noise robustness, essential entanglement, clinical readiness. Use wording such as "evaluated against", "parity with", "within noise of", "simulated only". Mention that all results are simulator-only and on public datasets.

QUALITY GATES AFTER EVERY PHASE
pytest (coverage >= 80% on backend/ml/quantum), npm run type-check, npm run build, npx vitest run, secrets scan, /code-review on the diff (fix high and critical), docs/PROGRESS.md updated, local commit with a clear message. A failing gate must be fixed before the next phase.

FINAL REPORT (max 30 lines, written only when the loop rule is satisfied)
Scorecard summary (v1-baseline vs final), datasets run versus not run (with reasons, for example missing Kaggle credentials), which pre-registered hypotheses held and which failed, best and worst quantum results by dataset, claims we may and may not make, the numbers-consistency check result, BLOCKED items, and the exact actions the user must take (for example push to a remote named `mine`, add Kaggle credentials, deploy the demo).
