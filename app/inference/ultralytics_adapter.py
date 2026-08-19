"""Adapter for the supplied YOLO11m model (weights/best.pt, Ultralytics).

Mirrors the pipeline in DOCUMENTATION.md sections 3 and 7:
  * predict at the caller's conf/iou/imgsz (documented defaults 0.35 / 0.45 / 1024)
  * clamp boxes to the image and drop degenerate ones (< 2px)
  * optional CLAHE contrast pass for glare and shadow (enhancement 3)
  * automatic low-confidence second pass with TTA when nothing is found (enhancement 2)
  * class-aware NMS (section 3 step 5)

One deliberate difference from the reference: the model is run at a low
confidence *floor* rather than at the caller's threshold, and the filtering is
left to the caller. Ultralytics applies `conf` after the forward pass, so a lower
floor costs nothing, and it means the report can say how many findings sat just
below the threshold instead of silently dropping them.

Class names are read from `model.names` at load time, so the index order comes
from the weights file rather than being duplicated here.
"""

import logging
import time

import numpy as np
from PIL import Image

from app.errors import ConfigurationError, InferenceError
from app.inference.base import (
    DamageDetector,
    DetectionOptions,
    InferenceResult,
    PreparedImage,
    RawDetection,
)
from app.inference.postprocess import apply_class_aware_nms
from app.inference.raw_output import build_raw_output
from app.inference.preprocess import analyze_image_quality, enhance_damage_contrast

logger = logging.getLogger(__name__)

MIN_BOX_SIDE = 2.0  # boxes thinner than this are artefacts, not damage


class UltralyticsDetector(DamageDetector):
    backend_name = "ultralytics"

    def load(self) -> None:
        if not self.model_path:
            raise ConfigurationError(
                "MODEL_PATH must point to the .pt weights file for MODEL_BACKEND=ultralytics."
            )

        try:
            from ultralytics import YOLO
        except ImportError as exc:
            raise ConfigurationError(
                "The 'ultralytics' package is not installed. Run: pip install ultralytics"
            ) from exc

        try:
            import torch

            self._device = 0 if torch.cuda.is_available() else "cpu"
        except ImportError:
            self._device = "cpu"

        self._model = YOLO(self.model_path)
        # {0: 'dent', 1: 'scratch', ...} straight from the weights.
        self._names: dict[int, str] = dict(getattr(self._model, "names", {}) or {})

        # Everything the model returns above this is kept for reporting, whatever
        # threshold the caller asked for.
        self.detection_floor = float(self.config.get("MODEL_DETECTION_FLOOR", 0.15))
        self.fallback_min_conf = float(self.config.get("MODEL_FALLBACK_MIN_CONF", 0.15))

        self._loaded = True
        logger.info(
            "YOLO weights loaded",
            extra={
                "extra_fields": {
                    "model_path": self.model_path,
                    "device": str(self._device),
                    "classes": self._names,
                    "detection_floor": self.detection_floor,
                }
            },
        )

    @property
    def class_names(self) -> dict[int, str]:
        return dict(self._names)

    def _to_array(self, image: Image.Image, use_clahe: bool) -> np.ndarray:
        array = np.array(image.convert("RGB"))
        if use_clahe:
            array = enhance_damage_contrast(array)
        return array

    def _run(self, image_np: np.ndarray, options: DetectionOptions, conf: float, augment: bool):
        return self._model.predict(
            source=image_np,
            imgsz=options.input_size,
            conf=conf,
            iou=options.iou,
            device=self._device,
            augment=augment,
            verbose=False,
        )

    def _extract(self, results, width: int, height: int) -> list[RawDetection]:
        """Turn Ultralytics boxes into RawDetections, clamped to the image."""
        detections: list[RawDetection] = []
        if not results:
            return detections

        result = results[0]
        boxes = getattr(result, "boxes", None)
        if boxes is None or len(boxes) == 0:
            return detections

        for index in range(len(boxes)):
            class_id = int(boxes.cls[index].item())
            confidence = float(boxes.conf[index].item())
            x1, y1, x2, y2 = (float(v) for v in boxes.xyxy[index].tolist())

            # Clamp to the frame; the model can predict slightly outside it.
            x1 = max(0.0, min(float(width), x1))
            y1 = max(0.0, min(float(height), y1))
            x2 = max(0.0, min(float(width), x2))
            y2 = max(0.0, min(float(height), y2))

            box_width = max(0.0, x2 - x1)
            box_height = max(0.0, y2 - y1)
            if box_width < MIN_BOX_SIDE or box_height < MIN_BOX_SIDE:
                continue

            detections.append(
                RawDetection(
                    label=self._names.get(class_id, str(class_id)),
                    confidence=round(confidence, 4),
                    bbox=(int(x1), int(y1), int(box_width), int(box_height)),
                    extra={"class_id": class_id},
                )
            )
        return detections

    def predict(
        self, image: PreparedImage, options: DetectionOptions | None = None
    ) -> InferenceResult:
        options = options or DetectionOptions.from_config(self.config)

        started = time.perf_counter()
        image_np = self._to_array(image.image, options.use_clahe)
        height, width = image_np.shape[:2]

        quality = analyze_image_quality(image_np)

        # Run at the floor, never above the caller's threshold.
        floor = min(self.detection_floor, options.confidence)
        used_fallback = False

        try:
            results = self._run(image_np, options, floor, options.augment)
            detections = self._extract(results, width, height)

            # Enhancement 2: nothing at all, even at the floor, is more likely a
            # miss on a hard photo than a genuinely undamaged car - retry with TTA.
            if not detections and options.fallback_enabled and not options.augment:
                used_fallback = True
                retry_conf = min(floor, self.fallback_min_conf)
                logger.info(
                    "Nothing found at the floor, running TTA fallback pass",
                    extra={
                        "extra_fields": {
                            "fallback_conf": retry_conf,
                            "public_id": image.public_id,
                        }
                    },
                )
                results = self._run(image_np, options, retry_conf, True)
                detections = self._extract(results, width, height)
        except Exception as exc:
            raise InferenceError(f"YOLO inference failed: {exc}") from exc

        # NMS on everything, so a suppressed duplicate is not later counted as a
        # separate "below threshold" finding.
        detections = apply_class_aware_nms(detections, options.iou)

        duration_ms = int((time.perf_counter() - started) * 1000)

        raw_output = build_raw_output(
            backend=self.backend_name,
            detections=detections,
            width=width,
            height=height,
            class_names=self._names,
            image_quality=quality,
            confidence_threshold=options.confidence,
            model_path=self.model_path,
            device=str(self._device),
            parameters={
                **options.to_dict(),
                "detection_floor": floor,
                "fallback_pass_used": used_fallback,
            },
        )

        return InferenceResult(
            detections=detections,
            raw_output=raw_output,
            duration_ms=duration_ms,
            image_quality=quality,
            effective_confidence=options.confidence,
        )
