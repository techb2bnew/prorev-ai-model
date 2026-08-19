"""The job that runs the model over an inspection's images and stores the result.

Per-image isolation is the important property here: one unusable image is
recorded as failed and the inspection still completes with the rest.
"""

import logging
import time
import uuid
from datetime import datetime, timezone

import sqlalchemy as sa
from flask import current_app

from app.errors import ImageUnreachableError
from app.extensions import db
from app.inference.base import DetectionOptions
from app.inference.image_loader import load_image
from app.inference.normalizer import count_in_scope_below_threshold, normalise
from app.inference.registry import get_detector
from app.inference.severity import compute_damage_score
from app.models import (
    DamageType,
    Detection,
    ImageStatus,
    Inspection,
    InspectionImage,
    InspectionStatus,
    Severity,
    max_severity,
)
from app.services.report_service import build_damage_summary, damaged_area_percent
from app.utils.identifiers import parse_uuid_or_404

logger = logging.getLogger(__name__)


def _mean_damaged_area_percent(inspection: Inspection) -> float:
    """Mean damaged area across the images that were successfully analysed.

    Averaged rather than summed: each image's damaged fraction is already 0-100,
    so adding five of them could report "300% damaged". The mean answers "how
    much of the vehicle we photographed shows damage", which is comparable
    between a 2-image and a 5-image job.
    """
    analysed = [img for img in inspection.images if img.status == ImageStatus.PROCESSED]
    if not analysed:
        return 0.0

    per_image = [damaged_area_percent(image.detections) for image in analysed]
    return round(sum(per_image) / len(per_image), 2)


def _damage_type_ids() -> dict[str, uuid.UUID]:
    """class_key -> damage_types.id, so detections can be linked by key."""
    rows = db.session.execute(sa.select(DamageType.class_key, DamageType.id)).all()
    return {key: row_id for key, row_id in rows}


def _record_model(inspection: Inspection, detector=None) -> None:
    """Stamp which model produced this inspection's findings."""
    config = current_app.config
    inspection.model_name = config.get("MODEL_NAME")
    inspection.model_version = config.get("MODEL_VERSION")
    if detector is not None:
        inspection.model_backend = detector.backend_name


def process_inspection(inspection_id: str) -> None:
    """Run the whole pipeline for one inspection. Safe to call more than once."""
    inspection = db.session.get(Inspection, parse_uuid_or_404(inspection_id, "Inspection"))
    if inspection is None:
        logger.error("Inspection vanished before processing: %s", inspection_id)
        return

    if inspection.status not in {InspectionStatus.QUEUED, InspectionStatus.FAILED}:
        logger.info(
            "Inspection is not queued, skipping",
            extra={"extra_fields": {"inspection_id": inspection_id, "status": inspection.status}},
        )
        return

    config = current_app.config
    started_perf = time.perf_counter()

    inspection.status = InspectionStatus.PROCESSING
    inspection.error_code = None
    inspection.error_message = None
    db.session.commit()

    try:
        detector = get_detector(config)
    except Exception as exc:
        logger.exception("Model could not be loaded")
        _fail(inspection, "MODEL_LOAD_FAILED", str(exc), started_perf)
        return

    # Settings chosen when the inspection was created, falling back to the
    # configured defaults for rows created before settings existed.
    options = DetectionOptions.from_config(config, inspection.detection_settings or {})

    type_ids = _damage_type_ids()
    processed_count = 0
    failed_count = 0
    below_threshold_total = 0

    for image_row in inspection.images:
        ok, below = _process_one_image(inspection, image_row, detector, config, type_ids, options)
        if ok:
            processed_count += 1
            below_threshold_total += below
        else:
            failed_count += 1

    # Every image failed -> the inspection failed. Some failed -> partial success.
    if processed_count == 0:
        _fail(
            inspection,
            "ALL_IMAGES_FAILED",
            "None of the submitted images could be analysed.",
            started_perf,
            detector=detector,
        )
        return

    inspection.status = (
        InspectionStatus.PARTIAL_SUCCESS if failed_count else InspectionStatus.COMPLETED
    )
    _record_model(inspection, detector)

    db.session.flush()
    db.session.refresh(inspection)

    detections = inspection.detections
    total_area_percent = _mean_damaged_area_percent(inspection)
    score = compute_damage_score(
        rules_path=config["SEVERITY_RULES_PATH"],
        class_keys=[d.damage_type.class_key for d in detections],
        total_area_percent=total_area_percent,
    )

    inspection.total_detections = len(detections)
    inspection.total_area_percent = total_area_percent
    inspection.below_threshold_count = below_threshold_total
    inspection.damage_score = score["score"]
    # The 0-100 band is the headline severity; the worst single detection is kept
    # as a floor so one severe finding is never reported as merely minor.
    inspection.overall_severity = max_severity([score["band"], *[d.severity for d in detections]])
    inspection.damage_summary = build_damage_summary(inspection)
    _finish(inspection, started_perf)

    db.session.commit()

    logger.info(
        "Inspection processed",
        extra={
            "extra_fields": {
                "inspection_id": str(inspection.id),
                "status": inspection.status,
                "images_processed": processed_count,
                "images_failed": failed_count,
                "total_detections": inspection.total_detections,
                "damage_score": inspection.damage_score,
                "overall_severity": inspection.overall_severity,
                "processing_ms": inspection.processing_ms,
            }
        },
    )


def _mark_image_failed(image_row: InspectionImage, reason: str) -> tuple[bool, int]:
    image_row.status = ImageStatus.FAILED
    image_row.failure_reason = reason
    db.session.commit()
    logger.warning(
        "Image could not be analysed",
        extra={"extra_fields": {"image_id": str(image_row.id), "reason": reason}},
    )
    return False, 0


def _process_one_image(
    inspection: Inspection,
    image_row: InspectionImage,
    detector,
    config,
    type_ids: dict[str, uuid.UUID],
    options: DetectionOptions,
) -> tuple[bool, int]:
    """Download, infer, normalise and store one image.

    Returns (succeeded, findings_below_threshold).
    """
    try:
        prepared = load_image(
            image_row.secure_url,
            image_row.cloudinary_public_id,
            timeout=config.get("IMAGE_DOWNLOAD_TIMEOUT", 20),
            max_bytes=config.get("MAX_IMAGE_BYTES"),
            target_width=options.input_size,
        )
    except ImageUnreachableError as exc:
        return _mark_image_failed(image_row, exc.message)

    max_attempts = max(int(config.get("INFERENCE_MAX_RETRIES", 3)), 1)
    result = None
    last_error: Exception | None = None

    for attempt in range(1, max_attempts + 1):
        try:
            result = detector.predict(prepared, options)
            break
        except Exception as exc:  # model failures are retried, then given up on
            last_error = exc
            logger.warning(
                "Inference attempt failed",
                extra={
                    "extra_fields": {
                        "image_id": str(image_row.id),
                        "attempt": attempt,
                        "error": str(exc),
                    }
                },
            )
            if attempt < max_attempts:
                time.sleep(min(2 ** (attempt - 1), 8))  # 1s, 2s, 4s ... capped

    if result is None:
        return _mark_image_failed(
            image_row, f"Model failed after {max_attempts} attempts: {last_error}"
        )

    # Filter at the threshold the adapter actually ran with. Using the config
    # default here was a bug: it discarded everything the low-confidence fallback
    # pass found, making that whole retry path pointless.
    threshold = result.effective_confidence

    detections = normalise(
        raw_detections=result.detections,
        pixel_area=prepared.pixel_area,
        confidence_threshold=threshold,
        class_mapping_path=config["CLASS_MAPPING_PATH"],
        severity_rules_path=config["SEVERITY_RULES_PATH"],
    )

    # Findings the model saw but the threshold excluded, so a thin report can be
    # explained rather than looking like the model simply missed the damage.
    below_threshold = count_in_scope_below_threshold(
        result.detections, threshold, config["CLASS_MAPPING_PATH"]
    )

    for detection in detections:
        damage_type_id = type_ids.get(detection.class_key)
        if damage_type_id is None:
            # Mapping produced a key with no seeded row - a config/seed mismatch.
            logger.error(
                "No damage_types row for class key, detection dropped",
                extra={"extra_fields": {"class_key": detection.class_key}},
            )
            continue

        bbox = detection.bbox
        db.session.add(
            Detection(
                inspection_id=inspection.id,
                inspection_image_id=image_row.id,
                damage_type_id=damage_type_id,
                confidence=detection.confidence,
                severity=detection.severity,
                bbox_x=bbox[0] if bbox else None,
                bbox_y=bbox[1] if bbox else None,
                bbox_width=bbox[2] if bbox else None,
                bbox_height=bbox[3] if bbox else None,
                polygon=detection.polygon,
                area_ratio=detection.area_ratio,
            )
        )

    # Boxes are in the coordinate space of the image the model actually saw,
    # which may be a downscaled Cloudinary transformation - so record those
    # dimensions alongside them. A client scales the two together (the frontend
    # uses them as an SVG viewBox); storing the original size here instead would
    # make the boxes disagree with the numbers next to them.
    image_row.width = prepared.width
    image_row.height = prepared.height
    image_row.status = ImageStatus.PROCESSED
    image_row.failure_reason = None
    image_row.quality_report = result.image_quality or None

    db.session.commit()
    return True, below_threshold


def _finish(inspection: Inspection, started_perf: float) -> None:
    inspection.processing_completed_at = datetime.now(timezone.utc)
    inspection.processing_ms = int((time.perf_counter() - started_perf) * 1000)


def _fail(
    inspection: Inspection,
    code: str,
    message: str,
    started_perf: float,
    detector=None,
) -> None:
    inspection.status = InspectionStatus.FAILED
    inspection.error_code = code
    inspection.error_message = message
    inspection.overall_severity = Severity.NONE
    inspection.total_detections = 0
    inspection.damage_summary = build_damage_summary(inspection)
    if detector is not None:
        _record_model(inspection, detector)
    _finish(inspection, started_perf)
    db.session.commit()
    logger.error(
        "Inspection failed",
        extra={"extra_fields": {"inspection_id": str(inspection.id), "error_code": code}},
    )


def requeue_stuck_inspections() -> int:
    """Re-queue inspections left mid-flight by a restart.

    Jobs live in the process, so a crash or redeploy would otherwise leave an
    inspection stuck in `processing` for ever.
    """
    stuck = db.session.scalars(
        sa.select(Inspection).where(Inspection.status == InspectionStatus.PROCESSING)
    ).all()

    for inspection in stuck:
        inspection.status = InspectionStatus.QUEUED

    if stuck:
        db.session.commit()
        logger.warning("Re-queued %s inspection(s) left in processing by a restart", len(stuck))

    return len(stuck)
