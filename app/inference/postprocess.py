"""Class-aware Non-Maximum Suppression.

DOCUMENTATION.md section 3 step 5: suppression is applied per class, so a dent
overlapping a scratch keeps both boxes. Plain NMS across all classes would drop
one of them and under-report the damage.
"""

import logging

import cv2

from app.inference.base import RawDetection

logger = logging.getLogger(__name__)


def apply_class_aware_nms(
    detections: list[RawDetection], iou_threshold: float = 0.45
) -> list[RawDetection]:
    """Drop duplicate boxes within each class, keeping the most confident.

    Returns detections sorted by confidence, highest first.
    """
    if not detections:
        return []

    by_class: dict[str, list[RawDetection]] = {}
    for detection in detections:
        by_class.setdefault(detection.label, []).append(detection)

    kept: list[RawDetection] = []
    for label, group in by_class.items():
        if len(group) == 1:
            kept.extend(group)
            continue

        boxes_xywh = []
        confidences = []
        for detection in group:
            if detection.bbox is None:
                continue
            x, y, width, height = detection.bbox
            boxes_xywh.append([int(x), int(y), int(width), int(height)])
            confidences.append(float(detection.confidence))

        if not boxes_xywh:
            kept.extend(group)
            continue

        # score_threshold is 0.01 rather than the real confidence threshold:
        # filtering by confidence already happened, this call is only for overlap.
        indices = cv2.dnn.NMSBoxes(boxes_xywh, confidences, 0.01, iou_threshold)

        if len(indices) == 0:
            # Some OpenCV builds return an empty result rather than a single index;
            # keeping the best box is safer than silently dropping the class.
            kept.append(max(group, key=lambda d: d.confidence))
            continue

        for index in _flatten(indices):
            if 0 <= index < len(group):
                kept.append(group[index])

    kept.sort(key=lambda d: d.confidence, reverse=True)
    return kept


def _flatten(indices) -> list[int]:
    """cv2.dnn.NMSBoxes returns different shapes across OpenCV versions."""
    try:
        return [int(i) for i in indices.flatten()]
    except AttributeError:
        return [int(i[0]) if isinstance(i, (list, tuple)) else int(i) for i in indices]
