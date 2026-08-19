"""Picks the model adapter from MODEL_BACKEND and keeps one loaded instance.

Adapters are imported lazily: `mock` must work without torch installed, and
loading YOLO weights costs seconds so it happens once per process, never per
request.
"""

import logging
import threading

from app.errors import ConfigurationError
from app.inference.base import DamageDetector

logger = logging.getLogger(__name__)

_instance: DamageDetector | None = None
_instance_backend: str | None = None
_lock = threading.Lock()


def _build(backend: str, config: dict) -> DamageDetector:
    if backend == "mock":
        from app.inference.mock_adapter import MockDetector

        return MockDetector(config)

    if backend in {"ultralytics", "yolo", "pt"}:
        from app.inference.ultralytics_adapter import UltralyticsDetector

        return UltralyticsDetector(config)

    raise ConfigurationError(
        f"Unknown MODEL_BACKEND '{backend}'. Supported: mock, ultralytics.",
        details={"model_backend": backend},
    )


def get_detector(config: dict) -> DamageDetector:
    """Return the loaded detector, building it on first use."""
    global _instance, _instance_backend

    backend = str(config.get("MODEL_BACKEND", "mock")).lower()

    with _lock:
        if _instance is None or _instance_backend != backend:
            detector = _build(backend, config)
            detector.ensure_loaded()
            _instance, _instance_backend = detector, backend
            logger.info(
                "Damage detection model ready",
                extra={"extra_fields": detector.describe()},
            )
        return _instance


def reset_detector() -> None:
    """Drop the cached detector (tests, or after changing MODEL_BACKEND)."""
    global _instance, _instance_backend
    with _lock:
        _instance, _instance_backend = None, None
