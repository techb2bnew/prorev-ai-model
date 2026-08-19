"""Model inference layer.

The seam that keeps the model swappable: `DamageDetector` is the contract,
`registry.get_detector` picks the concrete adapter from MODEL_BACKEND, and
`normalizer` converts whatever the model says into one canonical shape.

Adapters are NOT imported here - the registry imports them lazily so optional
dependencies stay optional.
"""

from app.inference.base import DamageDetector, InferenceResult, PreparedImage, RawDetection
from app.inference.class_mapping import SUPPORTED_CLASS_KEYS, resolve_class_key
from app.inference.image_loader import load_image
from app.inference.normalizer import NormalisedDetection, normalise
from app.inference.registry import get_detector, reset_detector
from app.inference.severity import derive_severity

__all__ = [
    "DamageDetector",
    "InferenceResult",
    "PreparedImage",
    "RawDetection",
    "NormalisedDetection",
    "SUPPORTED_CLASS_KEYS",
    "derive_severity",
    "get_detector",
    "load_image",
    "normalise",
    "resolve_class_key",
    "reset_detector",
]
