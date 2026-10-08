"""H1: QSVM bandwidth + C tuned by inner CV (training fold only) vs our untuned QSVM. Exploratory, n too small.

Bandwidth s scales every data-dependent phase of the ZZ-style map: single-qubit 2*s*x_i, pair 2*s^2*(pi-x_i)(pi-x_j).
s = 1 reproduces backend/ml/quantum/qkernel.zz_feature_map exactly (sanity check below).
"""

import json
import sys

import numpy as np
import pennylane as qml
from sklearn.metrics import roc_auc_score
from sklearn.model_selection import StratifiedKFold
from sklearn.svm import SVC

from common import LABEL, SEED, Timer, folds, score
from backend.ml.quantum.qkernel import kernel_from_states, statevectors

N = 6
dev = qml.device("default.qubit", wires=N)


@qml.qnode(dev)
def state(x, s):
    for _ in range(2):
        for i in range(N):
            qml.RY(np.pi / 2, wires=i)
            qml.RZ(2.0 * s * x[..., i], wires=i)
        for i in range(N - 1):
            qml.CNOT(wires=[i, i + 1])
            qml.RZ(2.0 * s * s * (np.pi - x[..., i]) * (np.pi - x[..., i + 1]), wires=i + 1)
            qml.CNOT(wires=[i, i + 1])
    return qml.state()


def states(X, s):
    return np.asarray(state(np.asarray(X, float), s)).reshape(len(X), -1)


def fit_eval(Ktr, ytr, Kte, C):
    svc = SVC(kernel="precomputed", C=C, probability=True, random_state=SEED).fit(Ktr, ytr)
    return svc.predict_proba(Kte)[:, 1]


S_GRID = [0.05, 0.1, 0.2, 0.35, 0.5, 0.75, 1.0]
C_GRID = [0.1, 1.0, 10.0]
dataset = sys.argv[1] if len(sys.argv) > 1 else "heart"
out = {"label": LABEL, "dataset": dataset, "folds": []}
for k, Atr, ytr, Ava, yva, sel in folds(dataset, 2):
    with Timer() as t_all:
        # sanity: s=1 equals backend kernel
        assert np.allclose(kernel_from_states(states(Atr[:5], 1.0), states(Atr[:5], 1.0)),
                           kernel_from_states(statevectors(Atr[:5], N), statevectors(Atr[:5], N)))
        conc = {}
        St = {s: states(Atr, s) for s in S_GRID}
        for s in S_GRID:
            K = kernel_from_states(St[s], St[s])
            conc[s] = round(float(K[~np.eye(len(K), dtype=bool)].mean()), 4)
        inner = StratifiedKFold(3, shuffle=True, random_state=SEED)
        best, best_auc = None, -1
        for s in S_GRID:
            K = kernel_from_states(St[s], St[s])
            for C in C_GRID:
                aucs = [roc_auc_score(ytr[iv], fit_eval(K[np.ix_(it, it)], ytr[it], K[np.ix_(iv, it)], C))
                        for it, iv in inner.split(Atr, ytr)]
                if np.mean(aucs) > best_auc:
                    best, best_auc = (s, C), float(np.mean(aucs))
        s, C = best
        Sva = states(Ava, s)
        tuned = score(yva, fit_eval(kernel_from_states(St[s], St[s]), ytr, kernel_from_states(Sva, St[s]), C))
        S1 = states(Ava, 1.0)
        untuned = score(yva, fit_eval(kernel_from_states(St[1.0], St[1.0]), ytr, kernel_from_states(S1, St[1.0]), 1.0))
    out["folds"].append({"fold": k, "features": sel, "mean_offdiag_kernel": conc, "chosen": {"s": s, "C": C},
                         "inner_auc": round(best_auc, 4), "untuned_s1_C1": untuned, "tuned": tuned,
                         "runtime_s": round(t_all.s, 1), "inner_fits": len(S_GRID) * len(C_GRID) * 3})
print(json.dumps(out, indent=1))
