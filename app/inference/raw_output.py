"""Builds the ``raw_output`` block every adapter returns.

Both adapters describe their findings in the same shape, so the shape is defined
once here. It is stored verbatim on the inspection, which makes it a contract:
changing a key changes what a saved report can be rebuilt from.
"""

from app.inference.base import RawDetection


def detection_block(
    detection: RawDetection, total_area: float, confidence_threshold: float | None = None
) -> dict:
    """One detection, in the reporting shape (corner coords, area, percentages)."""
    x, y, width, height = detection.bbox
    area = width * height

    block = {
        "class_id": detection.extra.get("class_id"),
        "class_name": detection.label,
        "confidence": detection.confidence,
        "confidence_percent": round(detection.confidence * 100, 1),
        "bbox": {"x1": x, "y1": y, "x2": x + width, "y2": y + height},
        "width": width,
        "height": height,
        "area": area,
        "area_percentage": round(area / total_area * 100, 2),
    }
    if confidence_threshold is not None:
        block["above_threshold"] = detection.confidence >= confidence_threshold
    return block


def build_raw_output(
    *,
    backend: str,
    detections: list[RawDetection],
    width: int,
    height: int,
    class_names: dict[int, str],
    image_quality: dict,
    confidence_threshold: float | None = None,
    **extra,
) -> dict:
    """Assemble the full raw-output payload for one image.

    ``extra`` carries whatever else the adapter wants recorded (model path,
    device, the parameters it ran with).
    """
    total_area = float(width * height) or 1.0

    return {
        "backend": backend,
        "class_names": {str(key): value for key, value in class_names.items()},
        "image_dimensions": {"width": width, "height": height},
        "image_quality": image_quality,
        "detection_count": len(detections),
        # Detections below the reporting threshold are kept too, so a report can
        # be rebuilt at a lower sensitivity without re-running the model.
        "detections": [
            detection_block(detection, total_area, confidence_threshold)
            for detection in detections
            if detection.bbox
        ],
        **extra,
    }
