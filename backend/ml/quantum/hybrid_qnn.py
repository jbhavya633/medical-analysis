"""Hybrid quantum neural network: Linear -> TorchLayer (PQC, <Z> on every qubit) -> Linear head."""

import numpy as np
import pennylane as qml
import torch

from backend.ml.quantum import SEED
from backend.ml.quantum.vqc import TorchQuantumClassifier, make_qnode


class _HybridModule(torch.nn.Module):
    def __init__(self, n_features, n_qubits, n_layers):
        super().__init__()
        self.pre = torch.nn.Linear(n_features, n_qubits)
        self.q = qml.qnn.TorchLayer(make_qnode(n_qubits, n_layers, all_wires=True),
                                    {"weights": (n_layers, n_qubits, 2)})
        self.head = torch.nn.Linear(n_qubits, 1)

    def forward(self, x):
        angles = np.pi * torch.sigmoid(self.pre(x))  # keep encoded angles in [0, pi]
        return self.head(self.q(angles))


class HybridQNNClassifier(TorchQuantumClassifier):
    def __init__(self, n_qubits=6, n_layers=2, epochs=40, lr=0.03, batch_size=32, seed=SEED):
        self.n_qubits = n_qubits
        self.n_layers = n_layers
        self.epochs = epochs
        self.lr = lr
        self.batch_size = batch_size
        self.seed = seed

    def _build(self):
        return _HybridModule(self.n_qubits, self.n_qubits, self.n_layers)

    def _qnode(self):
        return make_qnode(self.n_qubits, self.n_layers, all_wires=True)
