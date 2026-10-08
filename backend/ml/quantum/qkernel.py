"""Quantum-kernel SVM with a ZZ-style feature map (PennyLane default.qubit).

Hardware-compatible gate set: RY, RZ, CNOT only. The kernel K_ij = |<psi(x_i)|psi(x_j)>|^2 is
computed from batched statevectors (one broadcast circuit execution per data matrix, not per pair).
"""

import numpy as np
import pennylane as qml
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.svm import SVC

from backend.ml.quantum import SEED


def zz_feature_map(x, n_qubits: int, reps: int = 2):
    """ZZ-style map: RY(pi/2) superposition, RZ(2x_i), then RZ(2(pi-x_i)(pi-x_j)) on CNOT-linked pairs."""
    for _ in range(reps):
        for i in range(n_qubits):
            qml.RY(np.pi / 2, wires=i)
            qml.RZ(2.0 * x[..., i], wires=i)
        for i in range(n_qubits - 1):
            qml.CNOT(wires=[i, i + 1])
            qml.RZ(2.0 * (np.pi - x[..., i]) * (np.pi - x[..., i + 1]), wires=i + 1)
            qml.CNOT(wires=[i, i + 1])


def state_qnode(n_qubits: int, reps: int = 2):
    dev = qml.device("default.qubit", wires=n_qubits)

    @qml.qnode(dev)
    def circuit(x):
        zz_feature_map(x, n_qubits, reps)
        return qml.state()

    return circuit


def statevectors(X: np.ndarray, n_qubits: int, reps: int = 2) -> np.ndarray:
    states = np.asarray(state_qnode(n_qubits, reps)(np.asarray(X, dtype=float)))
    return states.reshape(len(X), -1) if states.ndim == 2 else states.reshape(1, -1)


def kernel_from_states(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    return np.abs(A.conj() @ B.T) ** 2


def kernel_matrix(X1: np.ndarray, X2: np.ndarray, n_qubits: int, reps: int = 2) -> np.ndarray:
    return kernel_from_states(statevectors(X1, n_qubits, reps), statevectors(X2, n_qubits, reps))


def circuit_depth(qnode, *args) -> int:
    tape = qml.workflow.construct_tape(qnode)(*args)
    return int(tape.graph.get_depth())


class QuantumKernelSVM(ClassifierMixin, BaseEstimator):
    def __init__(self, n_qubits: int = 6, reps: int = 2, C: float = 1.0, seed: int = SEED):
        self.n_qubits = n_qubits
        self.reps = reps
        self.C = C
        self.seed = seed

    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        if X.shape[1] != self.n_qubits:
            raise ValueError(f"expected {self.n_qubits} features (one per qubit), got {X.shape[1]}")
        self.classes_ = np.unique(y)
        self.train_states_ = statevectors(X, self.n_qubits, self.reps)
        K = kernel_from_states(self.train_states_, self.train_states_)
        self.svc_ = SVC(kernel="precomputed", C=self.C, probability=True, random_state=self.seed).fit(K, y)
        self.circuit_depth_ = circuit_depth(state_qnode(self.n_qubits, self.reps), X[0])
        self.n_qubits_ = self.n_qubits
        self.n_params_ = int(self.svc_.dual_coef_.size)
        return self

    def _kernel(self, X):
        return kernel_from_states(statevectors(np.asarray(X, dtype=float), self.n_qubits, self.reps), self.train_states_)

    def predict(self, X):
        return self.svc_.predict(self._kernel(X))

    def predict_proba(self, X):
        return self.svc_.predict_proba(self._kernel(X))

    def decision_function(self, X):
        return self.svc_.decision_function(self._kernel(X))
