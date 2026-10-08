"""Simulator selection and noisy evaluation (docs/SIMULATOR_PLAN.md; docs/OPTIMIZATION_PLAN.md E5 and E8).

Models are trained noiselessly; their trained weights are then re-run on another simulator (default.mixed with a
noise model and/or finite shots). Noise model: depolarising p1 after every single-qubit gate and p2 on both wires
after every CNOT. Single-qubit-only noise (p2 = 0) is the control: with a <Z> readout and a monotone link it barely
moves AUC by construction (docs/INFERENCES.md 3.6), so Brier is reported next to AUC and two-qubit noise is the
real test. Simulated noise only; nothing here ran on quantum hardware.

python -m backend.ml.quantum.noise sweep --chosen-from <tuned summary.json> --models vqc,hybrid_qnn
python -m backend.ml.quantum.noise devices          (E5: default.qubit vs lightning.qubit, same weights)
"""

import argparse
import copy
import json
import platform
import time
from dataclasses import asdict, dataclass
from pathlib import Path

import numpy as np
import pennylane as qml
import torch
from sklearn.metrics import brier_score_loss, roc_auc_score
from sklearn.model_selection import StratifiedKFold

from backend.ml.quantum import SEED
from backend.ml.quantum.data import DATASETS, load_dataset, stratified_subsample
from backend.ml.quantum.evaluate import build_model
from backend.ml.quantum.preprocess import make_preprocessor
from backend.ml.quantum.stats import paired_bootstrap

DEVICES = ("default.qubit", "lightning.qubit", "default.mixed")
MAX_MIXED_QUBITS = 8  # density matrices scale as 4^n: 8 qubits already took ~28 s per 200-row forward pass
NOISE_LEVELS = [  # (p1, p2): two-qubit-gate noise with p1 = p2 / 10, then the single-qubit-only control
    (0.0005, 0.005), (0.001, 0.01), (0.002, 0.02),
    (0.01, 0.0), (0.05, 0.0), (0.1, 0.0),
]
SHOTS = (None, 1000)


@dataclass(frozen=True)
class SimConfig:
    device: str = "default.qubit"
    shots: int | None = None
    p1: float = 0.0
    p2: float = 0.0

    def __post_init__(self):
        if self.device not in DEVICES:
            raise ValueError(f"device must be one of {DEVICES}")
        if (self.p1 or self.p2) and self.device != "default.mixed":
            raise ValueError("noise channels need the density-matrix simulator default.mixed")
        if self.shots is not None and self.shots < 1:
            raise ValueError("shots must be a positive integer or None (exact)")

    @property
    def label(self) -> str:
        return f"{self.device}, p1={self.p1:g}, p2={self.p2:g}, shots={self.shots or 'exact'}"


def noise_model(p1: float, p2: float) -> qml.NoiseModel:
    def single(op, **_):
        qml.DepolarizingChannel(p1, wires=op.wires)

    def two_qubit(op, **_):
        for w in op.wires:
            qml.DepolarizingChannel(p2, wires=w)

    rules = {}
    if p1:
        rules[qml.noise.op_in(["RX", "RY", "RZ"])] = single
    if p2:
        rules[qml.noise.op_eq("CNOT")] = two_qubit
    return qml.NoiseModel(rules)


def simulated_scores(estimator, X, sim: SimConfig) -> np.ndarray:
    """P(disease) from a trained VQC / hybrid QNN with its circuit rebuilt on the simulator `sim`."""
    if estimator.n_qubits > MAX_MIXED_QUBITS and sim.device == "default.mixed":
        raise ValueError(f"default.mixed is limited to {MAX_MIXED_QUBITS} qubits here")
    qnode = estimator._qnode(device=sim.device, shots=sim.shots)
    if qnode is None:
        raise ValueError("model has no quantum circuit")
    if sim.p1 or sim.p2:
        qnode = qml.add_noise(qnode, noise_model(sim.p1, sim.p2))
    module = copy.deepcopy(estimator.module_)
    layer = qml.qnn.TorchLayer(qnode, {"weights": tuple(module.q.weights.shape)})
    layer.load_state_dict(module.q.state_dict())
    module.q = layer.double()
    with torch.no_grad():
        logits = module(torch.tensor(np.asarray(X, dtype=float))).reshape(-1)
    return torch.sigmoid(logits).numpy()


def gate_counts(estimator, x) -> dict:
    """Gate types, total count and depth of the trained model's circuit (qml.specs; no Qiskit needed)."""
    qnode = estimator._qnode()
    weights = torch.zeros(estimator.n_layers, estimator.n_qubits, 2, dtype=torch.float64)
    r = qml.specs(qnode)(torch.tensor(estimator._circuit_inputs(x)), weights)["resources"]
    return {"gates": dict(r.gate_types), "num_gates": int(r.num_gates), "depth": int(r.depth)}


def _fold_models(name, dataset, chosen, n_qubits, seed):
    """Refit the model of every outer fold with the hyperparameters its nested search chose (no new tuning)."""
    X, y, _ = load_dataset(dataset)
    for k, (tr, va) in enumerate(StratifiedKFold(5, shuffle=True, random_state=seed).split(X, y)):
        X_tr, y_tr = stratified_subsample(X[tr], y[tr], 200, seed)
        pre = make_preprocessor(n_qubits, "mutual_info", seed).fit(X_tr, y_tr)
        model = build_model(name, n_qubits, seed).set_params(**(chosen[k] if chosen else {}))
        yield y, va, model.fit(pre.transform(X_tr), y_tr), pre.transform(X[va])


def noise_sweep(name, dataset, chosen=None, n_qubits=6, seed=SEED) -> dict:
    configs = [SimConfig()] + [SimConfig("default.mixed", shots, p1, p2) for shots in SHOTS
                                for p1, p2 in [(0.0, 0.0), *NOISE_LEVELS]]
    scores = {c: None for c in configs}
    timing = {c: 0.0 for c in configs}
    gates = None
    for y, va, model, A_va in _fold_models(name, dataset, chosen, n_qubits, seed):
        gates = gates or gate_counts(model, A_va[0])
        for c in configs:
            if scores[c] is None:
                scores[c] = np.full(len(y), np.nan)
            t0 = time.perf_counter()
            scores[c][va] = simulated_scores(model, A_va, c)
            timing[c] += time.perf_counter() - t0
    ref = scores[configs[0]]
    rows = []
    for c in configs:
        s = scores[c]
        rows.append({**asdict(c), "label": c.label, "auc": float(roc_auc_score(y, s)),
                     "brier": float(brier_score_loss(y, s)), "ms_per_sample": 1000 * timing[c] / len(y),
                     "delta_auc_vs_exact": paired_bootstrap(y, s, ref, seed=seed),
                     "delta_brier_vs_exact": paired_bootstrap(y, s, ref, metric=brier_score_loss, seed=seed)})
    return {"model": name, "dataset": dataset, "hyperparameters_per_fold": chosen, "gate_counts": gates,
            "rows": rows}


def device_comparison(n_qubits_list=(4, 6, 8, 10), seed=SEED) -> dict:
    """E5: identical trained weights on default.qubit vs lightning.qubit; max |difference| and wall time."""
    X, y, _ = load_dataset("breast_cancer")
    X, y = stratified_subsample(X, y, 200, seed)
    out = []
    for n in n_qubits_list:
        A = make_preprocessor(n, "mutual_info", seed).fit(X, y).transform(X)
        model = build_model("vqc", n, seed, epochs=5).fit(A, y)
        row = {"n_qubits": n}
        for device in ("default.qubit", "lightning.qubit"):
            simulated_scores(model, A[:2], SimConfig(device))  # warm-up
            t0 = time.perf_counter()
            row[device] = simulated_scores(model, A, SimConfig(device))
            row[f"{device}_s_per_200_rows"] = time.perf_counter() - t0
        row["max_abs_diff"] = float(np.max(np.abs(row["default.qubit"] - row["lightning.qubit"])))
        out.append({k: v for k, v in row.items() if not isinstance(v, np.ndarray)})
    return {"rows": out, "note": "forward pass of a trained 2-layer VQC on 200 rows; one run, after warm-up"}


def _versions() -> dict:
    import importlib.metadata as md
    return {"python": platform.python_version(),
            **{p: md.version(p) for p in ("pennylane", "pennylane_lightning", "torch", "numpy", "scikit-learn")}}


def plot_sweep(result, path):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, axes = plt.subplots(1, 2, figsize=(9, 3.6))
    shot_settings = sorted({r["shots"] for r in result["rows"]}, key=lambda s: s or 0)
    for ax, metric in zip(axes, ("auc", "brier")):
        for shots, style in zip(shot_settings, ("-", ":", "--")):
            for kind, color in (("two-qubit", "#4a3aa7"), ("single-qubit control", "#a8a79f")):
                pts = [r for r in result["rows"] if r["device"] == "default.mixed" and r["shots"] == shots
                       and ((r["p2"] > 0) if kind == "two-qubit" else (r["p2"] == 0 and r["p1"] > 0))]
                base = [r for r in result["rows"] if r["device"] == "default.mixed" and r["shots"] == shots
                        and r["p1"] == 0 and r["p2"] == 0]
                xs = [0.0] + [r["p2"] if kind == "two-qubit" else r["p1"] for r in pts]
                ax.plot(xs, [r[metric] for r in base + pts], style, color=color, marker="o", markersize=4,
                        label=f"{kind}, {'exact' if shots is None else f'{shots} shots'}")
        ax.set_xlabel("Depolarising probability (p2, or p1 for the control)")
        ax.set_title(metric.upper() if metric == "auc" else "Brier (lower is better)", loc="left")
    axes[0].legend(frameon=False, fontsize=7)
    fig.suptitle(f"Simulated noise - {result['model']}, {result['dataset']} (pooled out-of-fold)", x=0.01, ha="left")
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = parser.add_subparsers(dest="cmd", required=True)
    sweep = sub.add_parser("sweep")
    sweep.add_argument("--chosen-from", type=Path, help="tuned summary.json whose per-fold choices are reused")
    sweep.add_argument("--models", default="vqc,hybrid_qnn")
    sweep.add_argument("--dataset", default="all", choices=["all", *DATASETS])
    sweep.add_argument("--out", type=Path, default=Path("backend/ml/quantum/results/experiments/e8_noise"))
    devices = sub.add_parser("devices")
    devices.add_argument("--out", type=Path, default=Path("backend/ml/quantum/results/experiments/e5_devices"))
    args = parser.parse_args(argv)
    args.out.mkdir(parents=True, exist_ok=True)
    if args.cmd == "devices":
        result = {**device_comparison(), "versions": _versions()}
        (args.out / "devices.json").write_text(json.dumps(result, indent=1), encoding="utf-8")
        return
    tuned = json.loads(args.chosen_from.read_text(encoding="utf-8")) if args.chosen_from else None
    results = []
    for dataset in (DATASETS if args.dataset == "all" else [args.dataset]):
        for name in args.models.split(","):
            chosen = tuned["datasets"][dataset]["models"][name]["tuning"]["chosen"] if tuned else None
            r = noise_sweep(name, dataset, chosen)
            plot_sweep(r, args.out / f"noise_{dataset}_{name}.png")
            results.append(r)
    (args.out / "noise.json").write_text(json.dumps({"versions": _versions(), "seed": SEED, "results": results},
                                                    indent=1), encoding="utf-8")


if __name__ == "__main__":
    main()
