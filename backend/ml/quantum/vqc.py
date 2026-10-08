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


def hardware_efficient_ansatz(weights, n_qubits: int, entangle: bool = True):
    """weights: (n_layers, n_qubits, 2) -> RY, RZ per qubit then a CNOT ring (unless entangle=False), per layer."""
    for layer in range(weights.shape[0]):
        for i in range(n_qubits):
            qml.RY(weights[layer, i, 0], wires=i)
            qml.RZ(weights[layer, i, 1], wires=i)
        if entangle:
            for i in range(n_qubits):
                qml.CNOT(wires=[i, (i + 1) % n_qubits])


def make_qnode(n_qubits: int, n_layers: int, all_wires: bool, reupload: bool = False, entangle: bool = True,
               device: str = "default.qubit", shots: int | None = None):
    """reupload=True: inputs hold one angle vector per layer (n_layers * n_qubits values) and each layer is
    preceded by its own RY encoding (data re-uploading). entangle=False drops the CNOT ring (ablation).
    device / shots select the simulator (docs/SIMULATOR_PLAN.md): finite shots need parameter-shift gradients,
    lightning.qubit uses adjoint, the other PennyLane simulators backprop."""
    dev = qml.device(device, wires=n_qubits, seed=SEED) if shots else qml.device(device, wires=n_qubits)
    diff_method = "parameter-shift" if shots else "adjoint" if device == "lightning.qubit" else "backprop"

    @qml.qnode(dev, interface="torch", diff_method=diff_method)
    def circuit(inputs, weights):
        if reupload:
            for layer in range(n_layers):
                angle_encoding(inputs[..., layer * n_qubits:(layer + 1) * n_qubits], n_qubits)
                hardware_efficient_ansatz(weights[layer:layer + 1], n_qubits, entangle)
        else:
            angle_encoding(inputs, n_qubits)
            hardware_efficient_ansatz(weights, n_qubits, entangle)
        if all_wires:
            return [qml.expval(qml.PauliZ(i)) for i in range(n_qubits)]
        return qml.expval(qml.PauliZ(0))

    return qml.set_shots(circuit, shots) if shots else circuit


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
        self.n_params_ = int(sum(p.numel() for p in self.module_.parameters()))
        qnode = self._qnode()
        if qnode is not None:  # None: classical ablation, no circuit to report
            self.n_qubits_ = self.n_qubits
            weights = torch.zeros(self.n_layers, self.n_qubits, 2, dtype=torch.float64)
            self.circuit_depth_ = circuit_depth(qnode, torch.tensor(self._circuit_inputs(X[0])), weights)
        return self

    def _qnode(self, **sim):
        """The model's circuit; sim (device, shots) rebuilds it on another simulator with the same structure."""
        return make_qnode(self.n_qubits, self.n_layers, all_wires=False, **sim)

    def _circuit_inputs(self, x):
        return x

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


INPUT_SCALINGS = ("none", "affine", "reupload")
READOUTS = ("z0", "allz")


class _VQCModule(torch.nn.Module):
    """input_scaling: "none" (angles = x), "affine" (trainable a_i x_i + b_i, encoded once) or "reupload"
    (trainable s_{l,i} x_i re-encoded before every layer). readout: <Z0> or the mean of <Z_i> over all qubits.
    The extra input parameters start at a = s = 1, b = 0, so every variant starts from the base circuit."""

    def __init__(self, n_qubits, n_layers, input_scaling="none", readout="z0", entangle=True):
        super().__init__()
        self.input_scaling, self.readout, self.n_layers = input_scaling, readout, n_layers
        self.q = qml.qnn.TorchLayer(
            make_qnode(n_qubits, n_layers, all_wires=readout == "allz", reupload=input_scaling == "reupload",
                       entangle=entangle),
            {"weights": (n_layers, n_qubits, 2)})
        self.scale = torch.nn.Parameter(torch.tensor(3.0))
        self.bias = torch.nn.Parameter(torch.tensor(0.0))
        if input_scaling == "affine":
            self.in_scale = torch.nn.Parameter(torch.ones(n_qubits))
            self.in_shift = torch.nn.Parameter(torch.zeros(n_qubits))
        elif input_scaling == "reupload":
            self.in_scale = torch.nn.Parameter(torch.ones(n_layers, n_qubits))

    def forward(self, x):
        if self.input_scaling == "affine":
            x = self.in_scale * x + self.in_shift
        elif self.input_scaling == "reupload":
            x = (self.in_scale.unsqueeze(0) * x.unsqueeze(1)).reshape(len(x), -1)
        out = self.q(x)
        if self.readout == "allz":
            out = out.mean(dim=-1)
        return self.scale * out + self.bias


class VQCClassifier(TorchQuantumClassifier):
    # defaults for artifacts pickled before these options existed
    input_scaling, readout, entangle = "none", "z0", True

    def __init__(self, n_qubits=6, n_layers=2, epochs=40, lr=0.05, batch_size=32, seed=SEED,
                 input_scaling="none", readout="z0", entangle=True):
        self.n_qubits = n_qubits
        self.n_layers = n_layers
        self.epochs = epochs
        self.lr = lr
        self.batch_size = batch_size
        self.seed = seed
        self.input_scaling = input_scaling
        self.readout = readout
        self.entangle = entangle

    def _build(self):
        if self.input_scaling not in INPUT_SCALINGS or self.readout not in READOUTS:
            raise ValueError(f"input_scaling must be one of {INPUT_SCALINGS}, readout one of {READOUTS}")
        return _VQCModule(self.n_qubits, self.n_layers, self.input_scaling, self.readout, self.entangle)

    def _qnode(self, **sim):
        return make_qnode(self.n_qubits, self.n_layers, all_wires=self.readout == "allz",
                          reupload=self.input_scaling == "reupload", entangle=self.entangle, **sim)

    def _circuit_inputs(self, x):
        return np.tile(x, self.n_layers) if self.input_scaling == "reupload" else x
