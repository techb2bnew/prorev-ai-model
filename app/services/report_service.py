"""Builds the damage report from stored detections.

Everything here reads from the database, never from the model, so a report can
be rebuilt at any time without re-running inference.
"""

import sqlalchemy as sa

from app.extensions import db
from app.models import DamageType, Inspection, InspectionStatus, max_severity


def active_damage_types() -> list[DamageType]:
    """The damage classes on offer, in display order."""
    return list(
        db.session.scalars(
            sa.select(DamageType)
            .where(DamageType.is_active.is_(True))
            .order_by(DamageType.sort_order)
        ).all()
    )


def damaged_area_percent(detections) -> float:
    """The share of one image that shows damage, as a percentage.

    Clamped to 100: overlapping boxes of different classes can otherwise total
    more than the image they sit in.
    """
    return round(min(100.0, sum(float(d.area_ratio or 0.0) for d in detections) * 100), 2)


def build_damage_summary(inspection: Inspection) -> list[dict]:
    """Per-class counts, including the classes that were NOT found.

    Reporting the zeroes matters: "no glass shatter" is a finding the user wants
    to see, not an absence to be inferred from a missing key.
    """
    grouped: dict[str, list] = {}
    for detection in inspection.detections:
        grouped.setdefault(detection.damage_type.class_key, []).append(detection)

    summary = []
    for damage_type in active_damage_types():
        found = grouped.get(damage_type.class_key, [])
        summary.append(
            {
                "class_key": damage_type.class_key,
                "label": damage_type.display_name,
                "color_hex": damage_type.color_hex,
                "is_critical": damage_type.is_critical,
                "count": len(found),
                "max_severity": max_severity([d.severity for d in found]) if found else None,
                "total_area_percent": damaged_area_percent(found) if found else 0.0,
            }
        )
    return summary


def error_block(inspection: Inspection) -> dict | None:
    """The error envelope for an inspection, or None when it did not fail."""
    if not inspection.error_code:
        return None
    return {"code": inspection.error_code, "message": inspection.error_message}


def build_report(inspection: Inspection) -> dict:
    """The full report payload for one inspection."""
    summary = build_damage_summary(inspection)
    total = sum(row["count"] for row in summary)

    failed_images = [img for img in inspection.images if img.status == "failed"]
    analysed = len(inspection.images) - len(failed_images)

    if inspection.status == InspectionStatus.FAILED:
        overall_status = "failed"
    elif total > 0:
        overall_status = "damage_detected"
    else:
        overall_status = "no_damage_detected"

    # Surface photo-quality warnings at the top level: when a report comes back
    # empty, a blurry or dark photo is the most likely reason, and the user can
    # act on that.
    quality_warnings = [
        {"sequence_no": image.sequence_no, "warning": warning}
        for image in inspection.images
        for warning in (image.quality_report or {}).get("warnings", [])
    ]

    return {
        "overall_status": overall_status,
        "overall_severity": inspection.overall_severity,
        "damage_score": inspection.damage_score,
        "total_detections": total,
        "total_area_percent": inspection.total_area_percent,
        "images_submitted": len(inspection.images),
        "images_analysed": analysed,
        "partial_success": bool(failed_images) and analysed > 0,
        "damage_summary": summary,
        "image_quality_warnings": quality_warnings,
        # What the model was told to do, and what the threshold excluded. Both
        # matter when a report looks thinner than the user expected.
        "detection_preset": inspection.detection_preset,
        "detection_settings": inspection.detection_settings,
        "below_threshold_count": inspection.below_threshold_count,
        "images": [_image_block(image) for image in inspection.images],
        "model": {
            "name": inspection.model_name,
            "version": inspection.model_version,
            "backend": inspection.model_backend,
        },
        "processing_ms": inspection.processing_ms,
        "generated_at": (
            inspection.processing_completed_at.isoformat()
            if inspection.processing_completed_at
            else None
        ),
    }


def _image_block(image) -> dict:
    return {
        "inspection_image_id": str(image.id),
        "secure_url": image.secure_url,
        "thumbnail_url": image.thumbnail_url,
        "view_angle": image.view_angle,
        "sequence_no": image.sequence_no,
        "status": image.status,
        "failure_reason": image.failure_reason,
        "dimensions": {"width": image.width, "height": image.height},
        "quality": image.quality_report,
        "detections": [detection.to_dict() for detection in image.detections],
    }


def serialise_identity(inspection: Inspection) -> dict:
    """The fields every inspection response carries, whatever its shape."""
    return {
        "id": str(inspection.id),
        "status": inspection.status,
        "customer_name": inspection.customer_name,
        "vehicle_type": inspection.vehicle_type,
        "overall_severity": inspection.overall_severity,
        "damage_score": inspection.damage_score,
        "total_detections": inspection.total_detections,
        "image_count": inspection.image_count,
        "created_at": inspection.created_at.isoformat() if inspection.created_at else None,
    }


def serialise_inspection(inspection: Inspection, include_report: bool = True) -> dict:
    payload = {**serialise_identity(inspection), "error": error_block(inspection)}
    if include_report:
        payload["report"] = build_report(inspection)
    return payload


def serialise_summary_row(inspection: Inspection) -> dict:
    """Compact shape for the history list - no per-detection detail."""
    return {
        **serialise_identity(inspection),
        "damage_summary": inspection.damage_summary,
        "thumbnail_url": inspection.images[0].thumbnail_url if inspection.images else None,
    }
