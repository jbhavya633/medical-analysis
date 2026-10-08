"""H5 + simulator plan: (a) does a trained VQC degrade gracefully under depolarising noise / finite shots,
and what does noisy inference cost? (b) qubit-scaling timings per device on this laptop; (c) gate counts.
Exploratory, n too small for conclusions."""

import json
import platform
import time

import numpy as np
import pennylane as qml
import torch

from common import LABEL, SEED, folds, score
from backend.ml.quantum.vqc import VQCClassifier, angle_encoding, hardware_efficient_ansatz
from backend.ml.quantum.qkernel import zz_feature_map

N, L = 6, 2
out = {"label": LABEL, "python": platform.python_version(), "pennylane": qml.__version__,
       "torch": torch.__version__}

# (a) noise robustness of a trained VQC (heart, fold 0, 15 epochs)
k, Atr, ytr, Ava, yva, _ = next(folds("heart", 1))
vqc = VQCClassifier(epochs=15, seed=SEED).fit(Atr, ytr)
W = vqc.module_.q.weights.detach().numpy()
a, b = float(vqc.module_.scale), float(vqc.module_.bias)


def noisy_qnode(p, shots=None):
    dev = qml.device("default.mixed", wires=N)

    @qml.qnode(dev)
    def c(x):
        angle_encoding(x, N)
        for layer in range(L):
            hardware_efficient_ansatz(W[layer:layer + 1], N)
            if p > 0:
                for i in range(N):
                    qml.DepolarizingChannel(p, wires=i)
        return qml.expval(qml.PauliZ(0))
    return qml.set_shots(c, shots) if shots else c


noise = {}
for p, shots in [(0.0, None), (0.001, None), (0.01, None), (0.05, None), (0.1, None), (0.0, 1000), (0.01, 1000)]:
    qn = noisy_qnode(p, shots)
    t0 = time.perf_counter()
    z = np.array([float(qn(x)) for x in Ava])
    dt = time.perf_counter() - t0
    prob = 1 / (1 + np.exp(-(a * z + b)))
    noise[f"p={p},shots={shots}"] = {**score(yva, prob), "ms_per_sample": round(1000 * dt / len(Ava), 2)}
    print("noise", p, shots, noise[f"p={p},shots={shots}"], flush=True)
out["noise_vqc_heart_fold0"] = noise
out["noiseless_reference_backend_predict"] = score(yva, vqc.predict_proba(Ava)[:, 1])

# (b) qubit scaling: forward on a 200-row batch, and forward+backward (backprop / adjoint)
scaling = {}
rng = np.random.default_rng(SEED)
for n in [4, 6, 8, 10]:
    X = torch.tensor(rng.uniform(0, np.pi, (200, n)))
    for devname, diff in [("default.qubit", "backprop"), ("lightning.qubit", "adjoint"), ("default.mixed", "backprop")]:
        if devname == "default.mixed" and n > 8:
            scaling[f"{devname}/{n}q"] = "skipped (density matrix 4^n; >8 qubits too slow for budget)"
            continue
        dev = qml.device(devname, wires=n)

        @qml.qnode(dev, interface="torch", diff_method=diff)
        def c(x, w):
            angle_encoding(x, n)
            hardware_efficient_ansatz(w, n)
            return qml.expval(qml.PauliZ(0))
        w = torch.tensor(rng.normal(size=(L, n, 2)), requires_grad=True)
        try:
            t0 = time.perf_counter()
            if devname == "lightning.qubit":
                y = torch.stack([c(x, w) for x in X])  # lightning: per-sample loop
            else:
                y = c(X, w)
            t_fwd = time.perf_counter() - t0
            t0 = time.perf_counter()
            y.sum().backward()
            t_bwd = time.perf_counter() - t0
            scaling[f"{devname}/{n}q"] = {"fwd_200_s": round(t_fwd, 3), "bwd_s": round(t_bwd, 3)}
        except Exception as e:  # record, do not hide
            scaling[f"{devname}/{n}q"] = f"FAILED: {type(e).__name__}: {e}"[:200]
        print("scale", devname, n, scaling[f"{devname}/{n}q"], flush=True)
out["scaling"] = scaling

# (c) gate counts / depth via qml.specs (no Qiskit available in this venv)
dev = qml.device("default.qubit", wires=N)


@qml.qnode(dev)
def vqc_c(x, w):
    angle_encoding(x, N)
    hardware_efficient_ansatz(w, N)
    return qml.expval(qml.PauliZ(0))


@qml.qnode(dev)
def zz_c(x):
    zz_feature_map(x, N, 2)
    return qml.state()


x0 = np.full(N, 0.5)
for name, qn, args in [("vqc", vqc_c, (x0, np.zeros((L, N, 2)))), ("qsvm_zz_map", zz_c, (x0,))]:
    r = qml.specs(qn)(*args)["resources"]
    out.setdefault("gate_counts", {})[name] = {"gates": dict(r.gate_types), "depth": r.depth,
                                               "num_gates": r.num_gates}
print(json.dumps(out, indent=1, default=str))
