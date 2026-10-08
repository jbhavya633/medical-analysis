"""H2/H3: VQC variants on heart-disease folds. Exploratory, n too small for conclusions.

Variants (own implementations, same 6 features in [0, pi], same Adam/BCE trainer as backend):
  base        - our VQCClassifier (RY encoding once, 2x [RY,RZ + CNOT ring], <Z0>)
  reupload    - encoding repeated before every layer with trainable per-feature input scale, <Z0>
  reup_allz   - reupload + mean of <Z_i> over all qubits as readout
  noent       - base circuit with the CNOT ring removed (entanglement ablation)
  hybrid      - our HybridQNNClassifier
  hybrid_cls  - hybrid with the quantum layer replaced by a classical Linear(6,6)+tanh (quantum-layer ablation)
  scale_only  - base circuit + trainable input scale, no re-uploading (separates the two effects)
  noent_reup_allz - reup_allz without CNOTs (fair entanglement ablation; compare with reup_allz)
NOTE: "noent" with <Z0> readout is a light-cone artefact (only feature 0 can reach Z0); do not read it as an
entanglement ablation.
Usage: python h2_vqc_variants.py EPOCHS DATASET [comma-separated variants]
"""

import json
import sys

import numpy as np
import pennylane as qml
import torch

from common import LABEL, SEED, Timer, folds, score
from backend.ml.quantum.hybrid_qnn import HybridQNNClassifier
from backend.ml.quantum.vqc import VQCClassifier, fit_torch

N, L = 6, 2
EPOCHS = int(sys.argv[1]) if len(sys.argv) > 1 else 15
DATASET = sys.argv[2] if len(sys.argv) > 2 else "heart"
dev = qml.device("default.qubit", wires=N)


def make_circuit(reupload, entangle, all_z):
    @qml.qnode(dev, interface="torch", diff_method="backprop")
    def circuit(inputs, weights, in_scale):
        for layer in range(L):
            if layer == 0 or reupload:
                for i in range(N):
                    qml.RY(in_scale[layer, i] * inputs[..., i], wires=i)
            for i in range(N):
                qml.RY(weights[layer, i, 0], wires=i)
                qml.RZ(weights[layer, i, 1], wires=i)
            if entangle:
                for i in range(N):
                    qml.CNOT(wires=[i, (i + 1) % N])
        if all_z:
            return [qml.expval(qml.PauliZ(i)) for i in range(N)]
        return qml.expval(qml.PauliZ(0))
    return circuit


class Module(torch.nn.Module):
    def __init__(self, reupload, entangle, all_z, train_scale):
        super().__init__()
        self.all_z = all_z
        self.q = qml.qnn.TorchLayer(make_circuit(reupload, entangle, all_z),
                                    {"weights": (L, N, 2), "in_scale": (L, N)},
                                    init_method={"weights": torch.nn.init.normal_,
                                                 "in_scale": torch.nn.init.ones_})
        if not train_scale:
            self.q.in_scale.requires_grad_(False)
        self.scale = torch.nn.Parameter(torch.tensor(3.0))
        self.bias = torch.nn.Parameter(torch.tensor(0.0))

    def forward(self, x):
        out = self.q(x)
        if self.all_z:
            out = out.mean(dim=-1)
        return self.scale * out + self.bias


class ClassicalDressed(torch.nn.Module):
    def __init__(self):
        super().__init__()
        self.pre, self.mid, self.head = torch.nn.Linear(N, N), torch.nn.Linear(N, N), torch.nn.Linear(N, 1)

    def forward(self, x):
        return self.head(torch.tanh(self.mid(np.pi * torch.sigmoid(self.pre(x)))))


def run_module(module, Atr, ytr, Ava, lr):
    torch.manual_seed(SEED)
    module = module.double()
    fit_torch(module, Atr, ytr, EPOCHS, lr, 32, SEED)
    with torch.no_grad():
        return torch.sigmoid(module(torch.tensor(Ava)).reshape(-1)).numpy(), sum(p.numel() for p in module.parameters() if p.requires_grad)


VARIANTS = {
    "base": lambda: ("sk", VQCClassifier(epochs=EPOCHS, seed=SEED)),
    "reupload": lambda: ("mod", Module(True, True, False, True), 0.05),
    "reup_allz": lambda: ("mod", Module(True, True, True, True), 0.05),
    "noent": lambda: ("mod", Module(False, False, False, False), 0.05),
    "hybrid": lambda: ("sk", HybridQNNClassifier(epochs=EPOCHS, seed=SEED)),
    "hybrid_cls": lambda: ("mod", ClassicalDressed(), 0.03),
    # second pass: fair entanglement ablation (all-Z readout so every feature reaches the output) and
    # separating "trainable input scale" from "re-uploading"
    "scale_only": lambda: ("mod", Module(False, True, False, True), 0.05),
    "noent_reup_allz": lambda: ("mod", Module(True, False, True, True), 0.05),
}
if len(sys.argv) > 3:
    VARIANTS = {k: VARIANTS[k] for k in sys.argv[3].split(",")}
out = {"label": LABEL, "dataset": DATASET, "epochs": EPOCHS, "folds": []}
for k, Atr, ytr, Ava, yva, sel in folds(DATASET, 2):
    row = {"fold": k}
    for name, make in VARIANTS.items():
        torch.manual_seed(SEED)
        spec = make()
        with Timer() as t:
            if spec[0] == "sk":
                m = spec[1].fit(Atr, ytr)
                p, n_params = m.predict_proba(Ava)[:, 1], m.n_params_
            else:
                p, n_params = run_module(spec[1], Atr, ytr, Ava, spec[2])
        row[name] = {**score(yva, p), "params": int(n_params), "train_s": round(t.s, 1)}
        print(k, name, row[name], flush=True)
    out["folds"].append(row)
print(json.dumps(out, indent=1))
