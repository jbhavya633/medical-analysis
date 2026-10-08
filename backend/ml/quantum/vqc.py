"""Variational quantum classifier: angle encoding + hardware-efficient ansatz (RY/RZ + CNOT ring).

Trained with PyTorch (Adam, binary cross-entropy) through PennyLane's TorchLayer on default.qubit.
"""

import numpy as np
import pennylane as qml
import torch
from sklearn.base import BaseEstimator, ClassifierMixin

from backend.ml.quantum import SEED
from backend.ml.quantum.qkernel import circuit_depth


def angle_encoding(x, n_qubits: int):
    for i in range(n_qubits):
        qml.RY(x[..., i], wires=i)


def hardware_efficient_ansatz(weights, n_qubits: int):
    """weights: (n_layers, n_qubits, 2) -> RY, RZ per qubit then a CNOT ring, per layer."""
    for layer in range(weights.shape[0]):
        for i in range(n_qubits):
            qml.RY(weights[layer, i, 0], wires=i)
            qml.RZ(weights[layer, i, 1], wires=i)
        for i in range(n_qubits):
            qml.CNOT(wires=[i, (i + 1) % n_qubits])


def make_qnode(n_qubits: int, n_layers: int, all_wires: bool):
    dev = qml.device("default.qubit", wires=n_qubits)

    @qml.qnode(dev, interface="torch", diff_method="backprop")
    def circuit(inputs, weights):
        angle_encoding(inputs, n_qubits)
        hardware_efficient_ansatz(weights, n_qubits)
        if all_wires:
            return [qml.expval(qml.PauliZ(i)) for i in range(n_qubits)]
        return qml.expval(qml.PauliZ(0))

    return circuit


def fit_torch(module, X, y, epochs, lr, batch_size, seed):
    """Mini-batch Adam + BCE-with-logits. Returns the per-epoch mean training loss."""
    torch.manual_seed(seed)
    Xt = torch.tensor(np.asarray(X), dtype=torch.float64)
    yt = torch.tensor(np.asarray(y), dtype=torch.float64)
    opt = torch.optim.Adam(module.parameters(), lr=lr)
    loss_fn = torch.nn.BCEWithLogitsLoss()
    gen = torch.Generator().manual_seed(seed)
    history = []
    for _ in range(epochs):
        perm = torch.randperm(len(Xt), generator=gen)
        total = 0.0
        for start in range(0, len(Xt), batch_size):
            idx = perm[start:start + batch_size]
            opt.zero_grad()
            loss = loss_fn(module(Xt[idx]).reshape(-1), yt[idx])
            loss.backward()
            opt.step()
            total += loss.item() * len(idx)
        history.append(total / len(Xt))
    return history


class TorchQuantumClassifier(ClassifierMixin, BaseEstimator):
    """Shared sklearn-style wrapper; subclasses implement _build(). Pickles via state_dict."""

    def _build(self) -> torch.nn.Module:
        raise NotImplementedError

    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        if X.shape[1] != self.n_qubits:
            raise ValueError(f"expected {self.n_qubits} features (one per qubit), got {X.shape[1]}")
        torch.manual_seed(self.seed)
        self.classes_ = np.array([0, 1])
        self.module_ = self._build().double()
        self.loss_history_ = fit_torch(self.module_, X, y, self.epochs, self.lr, self.batch_size, self.seed)
        self.n_qubits_ = self.n_qubits
        self.n_params_ = int(sum(p.numel() for p in self.module_.parameters()))
        weights = torch.zeros(self.n_layers, self.n_qubits, 2, dtype=torch.float64)
        self.circuit_depth_ = circuit_depth(self._qnode(), torch.tensor(X[0]), weights)
        return self

    def _qnode(self):
        return make_qnode(self.n_qubits, self.n_layers, all_wires=False)

    def predict_proba(self, X):
        with torch.no_grad():
            logits = self.module_(torch.tensor(np.asarray(X, dtype=float))).reshape(-1)
        p = torch.sigmoid(logits).numpy()
        return np.column_stack([1 - p, p])

    def predict(self, X):
        return (self.predict_proba(X)[:, 1] >= 0.5).astype(int)

    def __getstate__(self):
        state = self.__dict__.copy()
        if "module_" in state:
            state["module_"] = state["module_"].state_dict()
        return state

    def __setstate__(self, state):
        module_state = state.pop("module_", None)
        self.__dict__.update(state)
        if module_state is not None:
            self.module_ = self._build().double()
            self.module_.load_state_dict(module_state)


class _VQCModule(torch.nn.Module):
    def __init__(self, n_qubits, n_layers):
        super().__init__()
        self.q = qml.qnn.TorchLayer(make_qnode(n_qubits, n_layers, all_wires=False),
                                    {"weights": (n_layers, n_qubits, 2)})
        self.scale = torch.nn.Parameter(torch.tensor(3.0))
        self.bias = torch.nn.Parameter(torch.tensor(0.0))

    def forward(self, x):
        return self.scale * self.q(x) + self.bias


class VQCClassifier(TorchQuantumClassifier):
    def __init__(self, n_qubits=6, n_layers=2, epochs=40, lr=0.05, batch_size=32, seed=SEED):
        self.n_qubits = n_qubits
        self.n_layers = n_layers
        self.epochs = epochs
        self.lr = lr
        self.batch_size = batch_size
        self.seed = seed

    def _build(self):
        return _VQCModule(self.n_qubits, self.n_layers)
