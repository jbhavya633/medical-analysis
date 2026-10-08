"""Hybrid quantum neural network: Linear -> TorchLayer (PQC, <Z> on every qubit) -> Linear head.

quantum=False is the quantum-layer ablation (docs/OPTIMIZATION_PLAN.md E4): the PQC is replaced by a classical
Linear(n_qubits, n_qubits) + tanh of the same width, trained identically.
"""

import numpy as np
import pennylane as qml
import torch

from backend.ml.quantum import SEED
from backend.ml.quantum.vqc import TorchQuantumClassifier, make_qnode


class _HybridModule(torch.nn.Module):
    def __init__(self, n_features, n_qubits, n_layers, quantum=True):
        super().__init__()
        self.pre = torch.nn.Linear(n_features, n_qubits)
        if quantum:
            self.q = qml.qnn.TorchLayer(make_qnode(n_qubits, n_layers, all_wires=True),
                                        {"weights": (n_layers, n_qubits, 2)})
        else:
            self.q = torch.nn.Sequential(torch.nn.Linear(n_qubits, n_qubits), torch.nn.Tanh())
        self.head = torch.nn.Linear(n_qubits, 1)

    def forward(self, x):
        angles = np.pi * torch.sigmoid(self.pre(x))  # keep encoded angles in [0, pi]
        return self.head(self.q(angles))


RESIDUAL_CLASSICAL_WIDTH = 4  # tanh(W x), W: 6 x 4 -> 28 params; head on 10 inputs -> 11; total 39 vs quantum 37


class _ResidualModule(torch.nn.Module):
    """Readout-side bypass (docs/OPTIMIZATION_PLAN.md E15): head([x, block(x)]). quantum: block = <Z_i> of the angle-
    encoded 2-layer circuit (24 weights) -> head Linear(12, 1); total 37. classical control: block = tanh(W x) with
    4 units -> head Linear(10, 1); total 39."""

    def __init__(self, n_qubits, n_layers, quantum=True):
        super().__init__()
        if quantum:
            self.q = qml.qnn.TorchLayer(make_qnode(n_qubits, n_layers, all_wires=True),
                                        {"weights": (n_layers, n_qubits, 2)})
            width = n_qubits
        else:
            self.q = torch.nn.Sequential(torch.nn.Linear(n_qubits, RESIDUAL_CLASSICAL_WIDTH), torch.nn.Tanh())
            width = RESIDUAL_CLASSICAL_WIDTH
        self.head = torch.nn.Linear(n_qubits + width, 1)

    def forward(self, x):
        return self.head(torch.cat([x, self.q(x)], dim=-1))


class ResidualQNNClassifier(TorchQuantumClassifier):
    def __init__(self, n_qubits=6, n_layers=2, epochs=40, lr=0.05, batch_size=32, seed=SEED, quantum=True):
        self.n_qubits = n_qubits
        self.n_layers = n_layers
        self.epochs = epochs
        self.lr = lr
        self.batch_size = batch_size
        self.seed = seed
        self.quantum = quantum

    def _build(self):
        return _ResidualModule(self.n_qubits, self.n_layers, self.quantum)

    def _qnode(self, **sim):
        return make_qnode(self.n_qubits, self.n_layers, all_wires=True, **sim) if self.quantum else None


class HybridQNNClassifier(TorchQuantumClassifier):
    quantum = True  # default for artifacts pickled before the option existed

    def __init__(self, n_qubits=6, n_layers=2, epochs=40, lr=0.03, batch_size=32, seed=SEED, quantum=True):
        self.n_qubits = n_qubits
        self.n_layers = n_layers
        self.epochs = epochs
        self.lr = lr
        self.batch_size = batch_size
        self.seed = seed
        self.quantum = quantum

    def _build(self):
        return _HybridModule(self.n_qubits, self.n_qubits, self.n_layers, self.quantum)

    def _qnode(self, **sim):
        return make_qnode(self.n_qubits, self.n_layers, all_wires=True, **sim) if self.quantum else None
