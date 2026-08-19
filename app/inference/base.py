"""The contract every model adapter implements.

This is the seam that keeps the model swappable. Nothing above this layer
knows or cares whether the model is PyTorch, ONNX, TensorFlow or a hosted
service - only the adapter does.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from PIL.Image import Image


@dataclass
class PreparedImage:
    """An image downloaded from Cloudinary and ready for the model."""

    image: Image
    width: int
    height: int
    source_url: str
    public_id: str

    @property
    def pixel_area(self) -> int:
        return max(self.width * self.height, 1)


@dataclass
class RawDetection:
    """One finding, still in the model's own vocabulary.

    ``label`` is whatever the model called it; mapping it onto our six class
    keys happens in the normaliser, not here.
    """

    label: str
    confidence: float
    bbox: tuple[int, int, int, int] | None = None  # x, y, width, height in pixels
    polygon: list[list[int]] | None = None
    severity: str | None = None  # set only if the model reports it
    extra: dict[str, Any] = field(default_factory=dict)


@dataclass
class DetectionOptions:
    """Per-request model settings, mirroring the reference API's form fields.

    Sensitivity has to be adjustable per inspection: the documented default of
    0.35 discards faint dents and cracks, which typically score 0.15-0.30.
    """

    confidence: float = 0.35
    iou: float = 0.45
    input_size: int = 1024
    augment: bool = False
    use_clahe: bool = False
    fallback_enabled: bool = True

    @classmethod
    def from_config(cls, config: dict, overrides: dict | None = None) -> "DetectionOptions":
        options = cls(
            confidence=float(config.get("MODEL_CONFIDENCE_THRESHOLD", 0.35)),
            iou=float(config.get("MODEL_IOU_THRESHOLD", 0.45)),
            input_size=int(config.get("MODEL_INPUT_SIZE", 1024)),
            augment=bool(config.get("MODEL_AUGMENT", False)),
            use_clahe=bool(config.get("MODEL_USE_CLAHE", False)),
            fallback_enabled=bool(config.get("MODEL_FALLBACK_ENABLED", True)),
        )
        for key, value in (overrides or {}).items():
            if value is not None and hasattr(options, key):
                setattr(options, key, value)
        return options

    def to_dict(self) -> dict:
        return {
            "conf": self.confidence,
            "iou": self.iou,
            "imgsz": self.input_size,
            "augment": self.augment,
            "clahe": self.use_clahe,
        }


@dataclass
class InferenceResult:
    detections: list[RawDetection]
    raw_output: dict[str, Any]
    duration_ms: int
    #: Blur/exposure diagnostics, so a user who submitted an unusable photo is
    #: told why rather than just shown an empty report.
    image_quality: dict[str, Any] = field(default_factory=dict)
    #: The threshold the caller should filter at. The model is deliberately run
    #: at a lower floor (filtering is post-processing and costs nothing extra),
    #: so `detections` can contain sub-threshold findings and the caller must not
    #: assume they are already filtered.
    effective_confidence: float = 0.35


class DamageDetector(ABC):
    """Base class for all model adapters."""

    #: Short identifier written to inference_runs.model_backend
    backend_name: str = "unknown"

    def __init__(self, config: dict):
        self.config = config
        self.model_path = config.get("MODEL_PATH") or ""
        self.confidence_threshold = float(config.get("MODEL_CONFIDENCE_THRESHOLD", 0.35))
        self.input_size = int(config.get("MODEL_INPUT_SIZE", 640))
        self._loaded = False

    @property
    def is_loaded(self) -> bool:
        return self._loaded

    @abstractmethod
    def load(self) -> None:
        """Load the model into memory. Called once per worker process, not per request."""

    @abstractmethod
    def predict(
        self, image: PreparedImage, options: DetectionOptions | None = None
    ) -> InferenceResult:
        """Run the model on one image, honouring per-request options."""

    def ensure_loaded(self) -> None:
        if not self._loaded:
            self.load()
            self._loaded = True

    def describe(self) -> dict:
        return {
            "backend": self.backend_name,
            "name": self.config.get("MODEL_NAME"),
            "version": self.config.get("MODEL_VERSION"),
            "loaded": self._loaded,
        }
