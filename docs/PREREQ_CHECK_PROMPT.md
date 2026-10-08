# Pre-requisite check and learning-readiness prompt for Claude Code

Paste the block below into `claude` in the repo root, after approving the qiskit and alphaxiv servers with `/mcp`. It checks the machine, the tools and the reference material, builds a learning log, proves understanding with small checks, and ends with a GO / NO-GO report. It changes no application code.

```
You are preparing to learn from reference material and then improve this project (SIH26139 hybrid quantum ML for early disease detection). This is a PRE-REQUISITE CHECK AND LEARNING SETUP. Work autonomously, ask no questions. If you are unsure at any point, re-read this prompt and apply its rules.

RULES
- Do not change application source code (backend/, src/). You may create or edit only: docs/LEARNING_LOG.md, docs/READINESS_REPORT.md, references/ (git-ignored), scratch/ (git-ignored).
- Never write keys or tokens anywhere. Never push to `origin`; push only to a remote named `mine` and only if I ask.
- Do not copy code from other repos into this project. Reference repos are for reading and for short experiments in scratch/ only. Repos without a stated licence (the four SIH26139 projects in docs/LEARN_FROM.md section A) must NOT be cloned or mirrored; read them online only, take notes in your own words.
- Real results only. Never invent a number, a source or a command output.
- If a step fails twice, log it in the report and continue.

PHASE 1 - MACHINE AND ENVIRONMENT (report as a table: item, version/status, OK/FIX)
1. OS, free disk space (need >= 5 GB), RAM, CPU cores, GPU if any (nvidia-smi); git, git identity, python (>= 3.10), node (>= 18), npm, uv/uvx, claude --version.
2. In the repo .venv: pennylane, torch (CPU is fine), scikit-learn, shap, qiskit, qiskit-aer, numpy, scipy, matplotlib, pandas, joblib, pytest, pytest-cov, fastapi, uvicorn. Print each version. Fix only by `pip install` inside .venv.
3. `git status`, `git remote -v` (confirm origin push is disabled), `git log --oneline -5`.
4. Run `python -m pytest backend/tests -q`, `npm run type-check`, `npm run build`. Record pass or fail and the test count. Do not fix failures; just report.

PHASE 2 - TOOLS (table: tool, how checked, status)
- Skills: list .claude/skills; confirm the PennyLane skill loads and read its SKILL.md headings.
- MCP: run `claude mcp list`. For qiskit, alphaxiv, context7, playwright, and any claude.ai connectors (PubMed, Clinical Trials, SNOMED CT, Hugging Face): make ONE real call each and record pass/fail. If a tool is not enabled, say exactly what I must enable and where.
- Plugins: confirm which of GitHub, Code Review, CI Optimizer, IDD are active.

PHASE 3 - REFERENCE MATERIAL
1. Read docs/RELATED_WORK.md, docs/LEARN_FROM.md, docs/IMPROVEMENT_PROMPT.md, docs/NEXT_STEPS.md, docs/ISSUES.md, README.md. List any broken links or missing files.
2. If the folder references/ exists, list what is in it. Open-licence repos allowed there (shallow clones, read-only use): XanaduAI/qml-benchmarks (Apache-2.0), mit-han-lab/torchquantum (MIT), fatimasood/XAI-Hybrid-Quantum-Liver-Disease-Detection (MIT). If they are missing, do NOT clone them; list them under "needs my approval to download".
3. For each source in LEARN_FROM.md sections B and C, open it with the web or connector tools and confirm it is reachable. Mark reachable / blocked / unverified.

PHASE 4 - BASELINE SNAPSHOT (so improvements can be measured)
1. Read backend/ml/quantum/results/summary.json and benchmark.log. Copy the current headline table (all models x both datasets: accuracy, sensitivity, specificity, AUC, F1, train s/fold) into docs/READINESS_REPORT.md under "Baseline before improvements", with the commit hash and seed.
2. Do NOT re-run the full benchmark (about 7 minutes). Instead run one quick smoke run: a single fold, one dataset, 3 epochs, to prove the pipeline executes. Record time.

PHASE 5 - LEARNING LOG AND UNDERSTANDING CHECKS
Create docs/LEARNING_LOG.md with this template and fill it for each of these six sources, reading each properly: B5 qml-benchmarks, B6 torchquantum, B7 QuantumNAS, C9 Ghisoni et al., C12 kernel SVM benchmark, C14 robustness pipeline.
For each source write: (a) the technique in two sentences, in your own words; (b) the exact claim and its evidence; (c) why it might or might not transfer to OUR data (6 qubits, <= 200 training rows, breast cancer and heart disease); (d) one testable hypothesis with the metric and the folds to use; (e) cost estimate in minutes.
Then answer these checks from the code and the logs (cite file and line):
1. How is the quantum kernel computed in qkernel.py, and why is it fast?
2. Which feature selection runs, and is it fitted on training folds only?
3. How are folds, seeds and training-row subsamples identical across models?
4. Where would nested-CV tuning slot in without touching the outer test folds?
5. Which two results look weakest in the baseline table and why (use the README's own explanations plus RELATED_WORK.md)?
6. What would make a claimed improvement invalid (name three leakage or tuning pitfalls)?

PHASE 6 - READINESS REPORT
Write docs/READINESS_REPORT.md: environment table, tools table, reference status, baseline table, understanding-check answers, a ranked list of the five most valuable experiments (hypothesis, metric, estimated minutes, risk), and a final line GO or NO-GO. NO-GO if any of these fail: venv packages missing, tests or build failing, baseline results unreadable, fewer than 4 of the 6 sources reachable. If NO-GO, list the exact fixes needed.

FINAL OUTPUT (max 20 lines): the GO/NO-GO verdict, the red items, the items needing my approval (downloads, connector toggles, sign-ins), and the single next command I should run. Do not start the improvements.
```

## Items that need your approval before this prompt can be fully GREEN
- Enabling the qiskit and alphaxiv MCP servers (`/mcp`), plus the alphaXiv sign-in.
- Enabling PubMed, Clinical Trials, SNOMED CT in claude.ai connector settings.
- Reconnecting the GitHub plugin in claude.ai.
- Cloning the three open-licence reference repos into the git-ignored `references/` folder (names and sources above).
