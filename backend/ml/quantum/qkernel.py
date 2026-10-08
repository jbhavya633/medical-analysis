"""Quantum-kernel SVM with a ZZ-style feature map (PennyLane default.qubit).

Hardware-compatible gate set: RY, RZ, CNOT only. The kernel K_ij = |<psi(x_i)|psi(x_j)>|^2 is
computed from batched statevectors (one broadcast circuit execution per data matrix, not per pair).
"""

import numpy as np
import pennylane as qml
from sklearn.base import BaseEstimator, ClassifierMixin
from sklearn.svm import SVC

from backend.ml.quantum import SEED


def zz_feature_map(x, n_qubits: int, reps: int = 2, bandwidth: float = 1.0):
    """ZZ-style map: RY(pi/2) superposition, RZ(2 s x_i), then RZ(2 s^2 (pi-x_i)(pi-x_j)) on CNOT-linked pairs.

    bandwidth s scales every data-dependent phase (s = 1 is the original map). At s = 1 the pair phase reaches
    2 pi^2 ~ 19.7 rad and the kernel is close to diagonal; smaller s widens it (docs/INFERENCES.md 3.2).
    """
    s = bandwidth
    for _ in range(reps):
        for i in range(n_qubits):
            qml.RY(np.pi / 2, wires=i)
            qml.RZ(2.0 * s * x[..., i], wires=i)
        for i in range(n_qubits - 1):
            qml.CNOT(wires=[i, i + 1])
            qml.RZ(2.0 * s * s * (np.pi - x[..., i]) * (np.pi - x[..., i + 1]), wires=i + 1)
            qml.CNOT(wires=[i, i + 1])


def state_qnode(n_qubits: int, reps: int = 2, bandwidth: float = 1.0):
    dev = qml.device("default.qubit", wires=n_qubits)

    @qml.qnode(dev)
    def circuit(x):
        zz_feature_map(x, n_qubits, reps, bandwidth)
        return qml.state()

    return circuit


def statevectors(X: np.ndarray, n_qubits: int, reps: int = 2, bandwidth: float = 1.0) -> np.ndarray:
    states = np.asarray(state_qnode(n_qubits, reps, bandwidth)(np.asarray(X, dtype=float)))
    return states.reshape(len(X), -1) if states.ndim == 2 else states.reshape(1, -1)


def kernel_from_states(A: np.ndarray, B: np.ndarray) -> np.ndarray:
    return np.abs(A.conj() @ B.T) ** 2


def kernel_matrix(X1: np.ndarray, X2: np.ndarray, n_qubits: int, reps: int = 2, bandwidth: float = 1.0) -> np.ndarray:
    return kernel_from_states(statevectors(X1, n_qubits, reps, bandwidth), statevectors(X2, n_qubits, reps, bandwidth))


def kernel_spectrum(K: np.ndarray) -> dict:
    """Shape diagnostics (arXiv 2604.18837 Table 7): mean off-diagonal value and effective-rank ratio."""
    off = K[~np.eye(len(K), dtype=bool)]
    eig = np.clip(np.linalg.eigvalsh(K), 0, None)
    p = eig / eig.sum()
    eff_rank = float(np.exp(-np.sum(p[p > 0] * np.log(p[p > 0]))))
    return {"mean_offdiag": float(off.mean()), "eff_rank_ratio": eff_rank / len(K), "top1_var": float(p.max())}


def circuit_depth(qnode, *args) -> int:
    tape = qml.workflow.construct_tape(qnode)(*args)
    return int(tape.graph.get_depth())


class QuantumKernelSVM(ClassifierMixin, BaseEstimator):
    bandwidth = 1.0  # default for artifacts pickled before the bandwidth parameter existed

    def __init__(self, n_qubits: int = 6, reps: int = 2, C: float = 1.0, bandwidth: float = 1.0, seed: int = SEED):
        self.n_qubits = n_qubits
        self.reps = reps
        self.C = C
        self.bandwidth = bandwidth
        self.seed = seed

    def fit(self, X, y):
        X = np.asarray(X, dtype=float)
        if X.shape[1] != self.n_qubits:
            raise ValueError(f"expected {self.n_qubits} features (one per qubit), got {X.shape[1]}")
        self.classes_ = np.unique(y)
        self.train_states_ = statevectors(X, self.n_qubits, self.reps, self.bandwidth)
        K = kernel_from_states(self.train_states_, self.train_states_)
        self.svc_ = SVC(kernel="precomputed", C=self.C, probability=True, random_state=self.seed).fit(K, y)
        self.kernel_spectrum_ = kernel_spectrum(K)
        self.circuit_depth_ = circuit_depth(state_qnode(self.n_qubits, self.reps, self.bandwidth), X[0])
        self.n_qubits_ = self.n_qubits
        self.n_params_ = int(self.svc_.dual_coef_.size)
        return self

    def _kernel(self, X):
        states = statevectors(np.asarray(X, dtype=float), self.n_qubits, self.reps, self.bandwidth)
        return kernel_from_states(states, self.train_states_)

    def predict(self, X):
        return self.svc_.predict(self._kernel(X))

    def predict_proba(self, X):
        return self.svc_.predict_proba(self._kernel(X))

    def decision_function(self, X):
        return self.svc_.decision_function(self._kernel(X))
