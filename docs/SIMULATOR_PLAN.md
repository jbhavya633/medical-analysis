# Simulator plan (SIH26139): design only, not built

Written 2026-10-08. A small simulator layer so every early-disease-detection experiment states **which simulator, which noise and how many shots** it ran on, and so the Quantum Lab can show this. This design builds nothing; implementation belongs to `docs/IMPROVEMENT_PROMPT.md` (experiments E5 and E8 in `docs/OPTIMIZATION_PLAN.md`).

## 1. Where devices are created today
- `backend/ml/quantum/vqc.py:31`: `qml.device("default.qubit", wires=n_qubits)` inside `make_qnode`, used by the VQC and (via import) the hybrid QNN (`hybrid_qnn.py:15`). It uses `diff_method="backprop"` (`vqc.py:33`).
- `backend/ml/quantum/qkernel.py:28`: `default.qubit` inside `state_qnode`, returning `qml.state()` (`qkernel.py:33`). The kernel is then `|<psi_i|psi_j>|^2` from batched statevectors (`qkernel.py:43-44`).
- `backend/ml/quantum/benchmark.py:197`: config records `"simulator": "default.qubit"` as a string only.

So the device is hard-coded in two places, and the kernel path depends on `qml.state()`. A statevector is undefined under noise or shots, which is the main design constraint.

## 2. Backend options and trade-offs

| Backend | New dependency? | Noise | Shots | Gradients | Measured on this laptop (6 qubits, 200 rows, `scratch/h5.out`) | Fit for us |
|---|---|---|---|---|---|---|
| PennyLane `default.qubit` | **No** (in `.venv`, 0.45.1) | No (pure states) | Yes (`qml.set_shots`) | backprop (batched) | forward 0.012 s, backward 0.010 s | **Default.** Fastest at 4-10 qubits for batched backprop. |
| PennyLane `lightning.qubit` | **No** (`pennylane_lightning` 0.45.0 already installed) | No | Yes | adjoint | forward 0.60 s, backward 0.21 s (per-sample loop; batched mode not tested) | Optional. Advantage expected only at higher qubit counts or many parameters (not measured here). |
| PennyLane `default.mixed` | **No** | **Yes**: channels (`DepolarizingChannel`, `AmplitudeDamping`, ...), `qml.add_noise` / `NoiseModel` (T4-1) | Yes | backprop | forward 0.33 s, backward 0.89 s at 6 qubits; **28.2 s / 24.3 s at 8 qubits** | **Noisy evaluation at ≤ 6-8 qubits only.** No noisy training beyond 6 qubits within budget. |
| Qiskit Aer | **Yes** (`qiskit`, `qiskit-aer` not installed) | Device-derived noise models | Yes | via plugin / parameter shift | not measured (BLOCKED: no downloads) | Later, if we want IBM-calibrated noise. The qiskit MCP is the no-install route for transpilation and gate counts. |
| TorchQuantum (B6) | **Yes** | Not documented in README | n/a | PyTorch autograd | not measured | **Not recommended.** README lists Python 3.7-3.9; we run 3.13.3. |

Qubit scaling measured on this laptop (`scratch/h5_noise_and_scaling.py`; angle encoding + 2 × [RY,RZ + CNOT ring], `<Z0>`, 200-row batch, one run, not warmed up):

| Qubits | default.qubit fwd / bwd (s) | lightning.qubit fwd / bwd (s) | default.mixed fwd / bwd (s) |
|---|---|---|---|
| 4 | 0.005 / 0.020 | 0.429 / 0.137 | 0.071 / 0.048 |
| 6 | 0.012 / 0.010 | 0.599 / 0.211 | 0.332 / 0.894 |
| 8 | 0.072 / 0.110 | 1.113 / 0.287 | 28.189 / 24.293 |
| 10 | 0.239 / 0.162 | 2.044 / 0.372 | skipped (4^n memory/time) |

Practical limits on this laptop: noiseless experiments are cheap up to at least 10 qubits (more than our 4-8-qubit UI range, `QuantumLab.tsx:101-102`). Noisy density-matrix simulation is practical at ≤ 6 qubits for evaluation, and marginal at 8.

## 3. Selecting a backend by config
Add one frozen config object, passed in rather than read from globals ("no new abstractions" rule: one dataclass plus a factory function):

```
SimConfig: device = "default.qubit" | "lightning.qubit" | "default.mixed"
           shots = None | int
           noise = None | {"p1": float, "p2": float, "amp_damp": float, "readout": float}
           diff_method = "backprop" | "adjoint" | "parameter-shift" (derived from device if omitted)
```

- `make_device(sim, wires)` returns `qml.device(sim.device, wires=wires)`. QNodes take `sim` and apply `qml.set_shots` and `qml.add_noise` when set.
- Thread `sim` through:
  - `vqc.make_qnode` (`vqc.py:30`) and `TorchQuantumClassifier` (constructor parameter, so `GridSearchCV` / `clone` keep working).
  - `qkernel.state_qnode` / `QuantumKernelSVM` (`qkernel.py:27`, `:56`).
  - `evaluate.build_model` (`evaluate.py:22`).
- CLI: `benchmark.py --device default.qubit --shots 0 --noise none|p1=0.001,p2=0.01`. The config dict at `benchmark.py:196-198` records the full `SimConfig`, replacing the bare `"simulator"` string.
- **Kernel path under noise/shots:** `qml.state()` is not available, so switch to the overlap circuit `U(x_j)^† U(x_i)` measured as `P(|0...0>)`. That gives one circuit per pair, O(N²). Restrict noisy QSVM to a 60-row subsample, as C12 did on hardware (Sec. 5.3), and label it.
- **Training stays noiseless by default.** Noise is applied at evaluation (E8). Noisy training is opt-in, 6 qubits max.

## 4. Noise channels and shot settings (defaults to propose)
- **Levels:** p₁ (after each single-qubit gate) ∈ {0, 1e-4, 1e-3}; p₂ (after each CNOT, on both wires) ∈ {0, 5e-3, 1e-2, 2e-2}; optional amplitude damping γ ∈ {0, 1e-3}; readout bit-flip ∈ {0, 1e-2}. This matches the order of magnitude C12 used (p₁q 1e-3, p₂q 1e-2; Sec. 4.4).
- **Shots:** {None (exact), 1000, 4000}.
- **Mandatory control row:** single-qubit-only depolarising noise. AUC is expected to stay flat by construction (`docs/INFERENCES.md` 3.6), and showing that guards against over-reading.
- **Report:** AUC and **Brier** vs noise; gate counts (`qml.specs`) per circuit; and, when the qiskit MCP is connected, a transpiled count on a named device such as `ibm_heron`, labelled "simulated, not run on hardware".

## 5. Reproducibility
- Seed 42 everywhere: `torch.manual_seed` already set (`vqc.py:46`, `:77`). Add a seed for shot sampling via `qml.device(..., seed=42)`.
- Record in every results JSON: `python`, `pennylane`, `pennylane_lightning`, `torch`, `numpy`, `scikit-learn` versions (`importlib.metadata`), `git_commit` (already at `benchmark.py:213`), and the full `SimConfig`.
- Same weights must give the same outputs across `default.qubit` and `lightning.qubit` to within 1e-8 (E5 acceptance check). Shot-based runs are reproducible only with a fixed device seed. Note this in the JSON.

## 6. Result schema (addition to `summary.json`)
```
"simulator": {
  "device": "default.mixed", "shots": 1000, "diff_method": "backprop",
  "noise": {"p1": 0.001, "p2": 0.01, "amp_damp": 0.0, "readout": 0.0},
  "versions": {"pennylane": "0.45.1", "pennylane_lightning": "0.45.0", "torch": "2.14.1+cpu"},
  "seed": 42
},
"models": { "<model>": { ..., "gate_counts": {"RY": 18, "RZ": 12, "CNOT": 12}, "depth": 17,
                         "noise_sweep": [{"p2": 0.0, "auc": ..., "brier": ...}, ...] } }
```
Breaking-change check: existing keys stay. `simulator` replaces the config string, and `QuantumLab.tsx` reads only `config` fields it already knows, so a fallback is needed for old JSON.

## 7. How the Quantum Lab page would expose it
- **Header badge:** "Simulator: default.qubit · exact (no shots) · noiseless", from `summary.simulator`. Shown next to the existing qubit picker (`QuantumLab.tsx:101-102`) and the "not a diagnostic tool" notice (`QuantumLab.tsx:81`).
- **Train form:** add `device` and `shots` pickers to the existing `/train` call (`router.py:52-53`, `service.start_training` at `service.py:69`). The noise picker is disabled above 6 qubits, with an explanation ("density-matrix simulation scales as 4^n"). `BusyError` (`service.py:39`) already guards concurrent jobs.
- **New chart:** "AUC and Brier vs noise" in a `ChartFrame` (same component as the ROC chart, `QuantumLab.tsx:263`), with the single-qubit control series drawn dashed.
- **Gate-count table:** extend the existing "Qubits / depth" column (`QuantumLab.tsx:195`, `:213`) with CNOT count.
- **Wording:** "simulated noise model" and never "hardware result".

## 8. What needs no new dependency
Everything in sections 3-7 except Qiskit Aer noise models and TorchQuantum. That covers device selection, `default.mixed` noise, shots, `lightning.qubit`, `qml.specs` gate counts, the result schema and the UI. Transpiled gate counts for a named IBM device need either the qiskit MCP (installed, currently disconnected) or `qiskit` in `.venv` (a download, which needs approval).
