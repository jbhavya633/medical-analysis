"""Model wrappers used by the FastAPI gateway (backend/main.py).

Every wrapper loads real weights or reports itself unavailable; none returns placeholder output.
"""


class ModelUnavailableError(RuntimeError):
    """Raised when a prediction is requested from a model whose weights are not loaded."""


class InvalidInputError(ValueError):
    """Raised when an uploaded input fails size, type or shape validation."""
