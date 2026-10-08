"""Purely classical baselines (scikit-learn)."""

from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.neural_network import MLPClassifier
from sklearn.svm import SVC

from backend.ml.quantum import SEED

CLASSICAL_MODELS = ["logreg", "svm_rbf", "random_forest", "mlp"]

# Nested-CV grids: exactly 6 configurations per model (equal tuning budget, docs/OPTIMIZATION_PLAN.md E10).
# Keys are Pipeline parameters ("model__" = the estimator); each grid contains today's default configuration.
CLASSICAL_GRIDS = {
    "logreg": {"model__C": [0.01, 0.1, 1.0, 10.0, 100.0, 1000.0]},
    "svm_rbf": {"model__C": [0.1, 1.0, 10.0], "model__gamma": ["scale", 0.1]},
    "random_forest": {"model__max_depth": [3, 6, None], "model__max_features": ["sqrt", None]},
    "mlp": {"model__hidden_layer_sizes": [(8,), (16,), (32,)], "model__alpha": [1e-4, 1e-2]},
}


def build_baseline(name: str, seed: int = SEED):
    if name == "logreg":
        return LogisticRegression(max_iter=2000, random_state=seed)
    if name == "svm_rbf":
        return SVC(kernel="rbf", C=1.0, gamma="scale", probability=True, random_state=seed)
    if name == "random_forest":
        return RandomForestClassifier(n_estimators=200, max_depth=6, random_state=seed, n_jobs=1)
    if name == "mlp":
        return MLPClassifier(hidden_layer_sizes=(16,), max_iter=2000, random_state=seed)
    raise KeyError(f"unknown classical model: {name}")


def count_params(model) -> int:
    """Number of learned parameters (support vectors for SVM, tree nodes for RF)."""
    if hasattr(model, "n_params_"):
        return int(model.n_params_)
    if isinstance(model, LogisticRegression):
        return int(model.coef_.size + model.intercept_.size)
    if isinstance(model, MLPClassifier):
        return int(sum(w.size for w in model.coefs_) + sum(b.size for b in model.intercepts_))
    if isinstance(model, SVC):
        return int(model.support_vectors_.size + model.dual_coef_.size)
    if isinstance(model, RandomForestClassifier):
        return int(sum(t.tree_.node_count for t in model.estimators_))
    return 0
