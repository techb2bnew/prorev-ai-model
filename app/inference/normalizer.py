"""Turns raw model output into the canonical detection shape used everywhere else.

Responsibilities:
  * map the model's labels onto our six class keys (dropping anything else)
  * drop detections below the confidence threshold
  * compute area_ratio from the bbox or polygon
  * attach a severity
"""

import logging
from dataclasses import dataclass
from pathlib import Path

from app.inference.base import RawDetection
from app.inference.class_mapping import resolve_class_key
from app.inference.severity import derive_severity

logger = logging.getLogger(__name__)


@dataclass
class NormalisedDetection:
    class_key: str
    confidence: float
    severity: str
    bbox: tuple[int, int, int, int] | None
    polygon: list[list[int]] | None
    area_ratio: float | None


def _polygon_area(polygon: list[list[int]]) -> float:
    """Shoelace formula. Returns 0 for a degenerate polygon."""
    if not polygon or len(polygon) < 3:
        return 0.0
    total = 0.0
    for i in range(len(polygon)):
        x1, y1 = polygon[i][0], polygon[i][1]
        x2, y2 = polygon[(i + 1) % len(polygon)][0], polygon[(i + 1) % len(polygon)][1]
        total += x1 * y2 - x2 * y1
    return abs(total) / 2.0


def _area_ratio(detection: RawDetection, pixel_area: int) -> float | None:
    """Damaged area as a fraction of the image. None for classification models."""
    if detection.polygon:
        area = _polygon_area(detection.polygon)
    elif detection.bbox:
        area = float(detection.bbox[2] * detection.bbox[3])
    else:
        return None
    return round(min(area / pixel_area, 1.0), 6)


def count_in_scope_below_threshold(
    raw_detections: list[RawDetection],
    confidence_threshold: float,
    class_mapping_path: str | Path,
) -> int:
    """How many in-scope findings the model saw but the threshold excluded.

    Reported so that a thin-looking report is explainable - "3 more findings
    below 0.35" tells the user to retry at a higher sensitivity, instead of
    leaving them to conclude the model missed the damage entirely.
    """
    count = 0
    for detection in raw_detections:
        if detection.confidence >= confidence_threshold:
            continue
        if resolve_class_key(detection.label, class_mapping_path) is not None:
            count += 1
    return count


def normalise(
    raw_detections: list[RawDetection],
    pixel_area: int,
    confidence_threshold: float,
    class_mapping_path: str | Path,
    severity_rules_path: str | Path,
) -> list[NormalisedDetection]:
    """Normalise every detection found in one image."""
    # Pass 1: resolve class keys and drop what is out of scope or low confidence,
    # so the per-class counts used by the hail severity rule are accurate.
    staged: list[tuple[str, RawDetection]] = []
    for detection in raw_detections:
        if detection.confidence < confidence_threshold:
            continue
        class_key = resolve_class_key(detection.label, class_mapping_path)
        if class_key is None:
            continue
        staged.append((class_key, detection))

    class_counts: dict[str, int] = {}
    for class_key, _ in staged:
        class_counts[class_key] = class_counts.get(class_key, 0) + 1

    # Pass 2: severity, which for hail depends on how many dents were counted.
    results: list[NormalisedDetection] = []
    for class_key, detection in staged:
        ratio = _area_ratio(detection, pixel_area)
        severity = derive_severity(
            class_key=class_key,
            rules_path=severity_rules_path,
            area_ratio=ratio,
            confidence=detection.confidence,
            class_count=class_counts.get(class_key, 1),
            model_severity=detection.severity,
        )
        results.append(
            NormalisedDetection(
                class_key=class_key,
                confidence=round(float(detection.confidence), 4),
                severity=severity,
                bbox=detection.bbox,
                polygon=detection.polygon,
                area_ratio=ratio,
            )
        )
    return results
