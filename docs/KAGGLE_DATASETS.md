# Multi-dataset benchmark: candidate datasets (target: at least 12 usable binary tasks)

Row and feature counts are approximate and written from memory; the loader must record the true values. UCI/OpenML fallbacks let the benchmark run if Kaggle credentials are absent. Slugs marked [search-verified] appeared in search results; all others must be resolved with `kaggle datasets list -s "<name>"` and checked.

## Acceptance rules for every dataset
- Binary (or reducible to binary with a documented rule), at least 150 rows, at least 30 rows in the minority class, numeric or encodable features.
- Real clinical or survey data. Reject datasets that are synthetic or generated (several popular Kaggle health sets are); record `provenance` in the registry. A synthetic set may be included only as a labelled "synthetic sanity check" outside the main statistics.
- Licence recorded from the dataset page. Raw files are NEVER committed (data/ is git-ignored); commit only the loader, checksums and derived results.
- Drop identifiers and any column that leaks the outcome or is not available at screening time. Document each dropped column.
- All imputation, scaling, encoding and feature selection are fitted inside training folds only.
- Exclude duplicates of data already used (UCI Cleveland variants such as "Heart Attack Analysis", Kaggle copies of WDBC).

## Candidates
| # | Dataset | Kaggle (slug or search term) | UCI / OpenML fallback | Approx size | Target and pitfalls |
|---|---|---|---|---|---|
| 1 | Pima Indians Diabetes | search "Pima Indians Diabetes Database" (several copies exist, e.g. aibuzz/pima-indians-diabetes-database [search-verified]) | OpenML name "diabetes" (data_id 37) | 768 x 8 | Outcome. Zeros in glucose, BP, skin, insulin, BMI are missing values |
| 2 | Heart Failure Clinical Records | search "heart failure clinical data" (andrewmvd) | UCI 519 | 299 x 12 | DEATH_EVENT. Drop `time` (follow-up time, not known at baseline) |
| 3 | Chronic Kidney Disease | search "ckdisease" | UCI 336 | 400 x 24 | classification. Many missing values, mixed types, drop `id` |
| 4 | Indian Liver Patient (ILPD) | uciml/indian-liver-patient-records [search-verified] | UCI 225 | 583 x 10 | Dataset label (1 = disease). Encode gender, a few missing albumin ratios |
| 5 | Stroke Prediction | fedesoriano/stroke-prediction-dataset [search-verified] | none | 5110 x 10 | stroke (about 5% positive). Drop `id`, handle `N/A` bmi and `Unknown` smoking; strong imbalance, use stratified folds and report balanced metrics |
| 6 | Cervical Cancer Risk Factors | search "cervical cancer risk classification" | UCI 383 | 858 x 35 | Use `Biopsy` only; drop Hinselmann, Schiller, Citology (alternative targets leak). Many "?" missing |
| 7 | Parkinson's (voice) | search "Parkinsons disease data set" | UCI 174 | 195 x 22 | status. Drop `name`. Several recordings per subject: group-aware folds if subject can be recovered, otherwise document the leakage risk |
| 8 | Early Stage Diabetes Risk | search "early stage diabetes risk prediction" | UCI 529 | 520 x 16 | class. Almost all binary symptoms; tests quantum encoding of binary features |
| 9 | Framingham Heart Study | aasheesh200/framingham-heart-study-dataset [search-verified] | none | 4240 x 15 | TenYearCHD (about 15% positive). Missing glucose, education, cigsPerDay |
| 10 | Cardiovascular Disease (large) | sulianova/cardiovascular-disease-dataset [search-verified] | none | 70000 x 11 | cardio. Clean impossible BP outliers; subsample by the same 200-row rule; also run a learning curve up to a larger N to see if the quantum gap changes |
| 11 | Breast Cancer Coimbra | search "breast cancer Coimbra" | UCI 451 | 116 x 9 | Classification. Very small: report wide intervals |
| 12 | Hepatitis | search "hepatitis" | UCI 46 | 155 x 19 | Class. Missing values; small |
| 13 | Lung Cancer survey | search "lung cancer survey" | none | 309 x 15 | LUNG_CANCER. Symptom survey, check duplicates |
| 14 | Mammographic Mass | search "mammographic mass" | UCI 161 | 961 x 5 | Severity. "?" missing |
| 15 | Thyroid disease / Sick | search "thyroid disease" | UCI 102 | about 3000 x 25 | Pick the binary sick/negative target. Strong imbalance |
| 16 | Differentiated Thyroid Cancer Recurrence | search "thyroid cancer recurrence" | UCI 915 | 383 x 16 | Recurred. Categorical clinical variables |
| 17 | Statlog (Heart) | none needed | UCI 145 | 270 x 13 | Overlaps Cleveland: use only as an independent-cohort sanity check, not in the statistics |

Already in the platform: UCI Breast Cancer Wisconsin (Diagnostic), UCI Heart Disease (Cleveland). Together with at least 10 of the datasets above this gives 12 or more.

## Pre-registered split of datasets (write into docs/PREREGISTRATION.md BEFORE any result is viewed)
- Development set (design decisions allowed): Cleveland, WDBC, Pima, ILPD.
- Confirmation set (no design decisions, results reported as they come): every other usable dataset.
- A method change is kept only if it improves the development set AND is then reported unchanged on the confirmation set, whatever the outcome.

## Credentials
Kaggle access uses the user's existing `~/.kaggle/kaggle.json` or the KAGGLE_USERNAME / KAGGLE_KEY environment variables, if present. Never create, print, log or commit them. If absent, use the UCI/OpenML fallbacks and list the Kaggle-only datasets as "not run: credentials not present" in the final report.
