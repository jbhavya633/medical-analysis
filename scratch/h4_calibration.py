"""H4: calibration and sensitivity at fixed specificity; does post-hoc Platt scaling (inner CV, training fold only)
fix VQC calibration? Exploratory, n too small for conclusions."""

import json
import sys

from sklearn.calibration import CalibratedClassifierCV

from common import LABEL, SEED, Timer, folds, score
from backend.ml.quantum.evaluate import build_model

EPOCHS = 15
DATASET = sys.argv[1] if len(sys.argv) > 1 else "heart"
out = {"label": LABEL, "dataset": DATASET, "epochs_quantum": EPOCHS, "folds": []}
for k, Atr, ytr, Ava, yva, _ in folds(DATASET, 2):
    row = {"fold": k}
    for name in ["logreg", "svm_rbf", "random_forest", "mlp", "qsvm", "vqc"]:
        with Timer() as t:
            p = build_model(name, 6, SEED, EPOCHS).fit(Atr, ytr).predict_proba(Ava)[:, 1]
        row[name] = {**score(yva, p), "train_s": round(t.s, 1)}
    with Timer() as t:
        cal = CalibratedClassifierCV(build_model("vqc", 6, SEED, EPOCHS), method="sigmoid", cv=3).fit(Atr, ytr)
        p = cal.predict_proba(Ava)[:, 1]
    row["vqc_platt"] = {**score(yva, p), "train_s": round(t.s, 1)}
    for name, r in row.items():
        if name != "fold":
            print(k, name, r, flush=True)
    out["folds"].append(row)
print(json.dumps(out, indent=1))
