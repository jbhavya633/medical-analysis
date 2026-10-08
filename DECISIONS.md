# DECISIONS

Log of autonomous decisions taken during the SIH26139 build (one line each).

- 22:07 Unfinished Phase-1 Fix 4 (Synthea mortality rewrite) stashed as `stash@{0}` because the SIH26139 spec puts Synthea out of scope; not committed.
- 22:07 `origin` is jbhavya633/medical-analysis (not SoubhagyaTripathi) -> no push, no issues/PRs; plan written to docs/ISSUES.md instead.
- 22:07 `/idd:*`, `/ci-optimizer:*`, `/code-review-plugin:*` are not installed -> equivalent steps done directly; built-in /code-review used for review.
- 22:07 Hadamard in the ZZ feature map replaced by RY(pi/2) so every circuit uses only RX/RY/RZ/CNOT (hardware-native set stated in the spec).
