"""Creating, listing and deleting inspections."""

import logging
from datetime import datetime, timezone

import sqlalchemy as sa
from flask import current_app

from app.errors import NotFoundError, PermissionDeniedError, ValidationError
from app.extensions import db
from app.models import (
    DamageType,
    Detection,
    Inspection,
    InspectionImage,
    InspectionStatus,
    User,
)
from app.utils.cloudinary_url import public_id_from_url, thumbnail_url
from app.utils.identifiers import parse_uuid_or_404
from app.utils.pagination import Page

logger = logging.getLogger(__name__)


def resolve_detection_settings(settings_input=None) -> tuple[str | None, dict]:
    """Turn a preset name and/or explicit values into the settings to run with.

    Explicit values override the preset, so a client can start from "sensitive"
    and still nudge a single number.
    """
    presets = current_app.config["DETECTION_PRESETS"]
    default_preset = current_app.config.get("DEFAULT_DETECTION_PRESET", "balanced")

    requested = getattr(settings_input, "preset", None) if settings_input else None
    preset_name = requested or default_preset
    preset = presets.get(preset_name, presets[default_preset])

    resolved = {
        "confidence": preset["confidence"],
        "iou": preset["iou"],
        "input_size": preset["input_size"],
        "augment": preset["augment"],
        "use_clahe": bool(current_app.config.get("MODEL_USE_CLAHE", False)),
    }

    if settings_input is not None:
        overrides = settings_input.model_dump(exclude_none=True)
        overrides.pop("preset", None)
        resolved.update(overrides)
        # Once a value is overridden the label no longer describes the run.
        if overrides:
            preset_name = f"{preset_name}+custom" if requested else "custom"

    return preset_name, resolved


def create_inspection(
    user: User,
    customer_name: str,
    vehicle_type: str,
    images: dict[str, str],
    settings_input=None,
    idempotency_key: str | None = None,
) -> tuple[Inspection, bool]:
    """Create an inspection in the `queued` state.

    ``images`` maps a view angle (front/back/left/right/top) to its Cloudinary
    URL, already validated and in canonical order by the request schema.

    Returns (inspection, created). When an Idempotency-Key is replayed the
    original inspection is returned with created=False, so a retried or
    double-clicked submission never produces a second inspection.
    """
    if idempotency_key:
        existing = db.session.scalar(
            sa.select(Inspection).where(Inspection.idempotency_key == idempotency_key)
        )
        if existing:
            if existing.user_id != user.id:
                raise PermissionDeniedError("This idempotency key belongs to another user.")
            logger.info(
                "Idempotent replay, returning existing inspection",
                extra={"extra_fields": {"inspection_id": str(existing.id)}},
            )
            return existing, False

    max_images = current_app.config.get("MAX_IMAGES_PER_INSPECTION", 10)
    if len(images) > max_images:
        raise ValidationError(
            f"An inspection accepts at most {max_images} images (received {len(images)}).",
            details={"max_images": max_images, "received": len(images)},
        )

    preset_name, settings = resolve_detection_settings(settings_input)

    inspection = Inspection(
        user_id=user.id,
        customer_name=customer_name,
        vehicle_type=vehicle_type,
        status=InspectionStatus.QUEUED,
        detection_preset=preset_name,
        detection_settings=settings,
        idempotency_key=idempotency_key,
    )
    db.session.add(inspection)
    db.session.flush()

    for index, (view_angle, secure_url) in enumerate(images.items()):
        db.session.add(
            InspectionImage(
                inspection_id=inspection.id,
                # Derived from the URL: the payload carries URLs only, and the
                # column is the human-readable handle on the Cloudinary asset.
                cloudinary_public_id=public_id_from_url(secure_url) or secure_url[:255],
                secure_url=secure_url,
                thumbnail_url=thumbnail_url(secure_url),
                view_angle=view_angle,
                sequence_no=index,
            )
        )

    db.session.commit()
    logger.info(
        "Inspection created",
        extra={
            "extra_fields": {
                "inspection_id": str(inspection.id),
                # From the request, not the row: reading it back would re-query
                # the images that were just committed, only to log a number.
                "image_count": len(images),
            }
        },
    )
    return inspection, True


def get_inspection_for_user(inspection_id: str, user: User) -> Inspection:
    """Fetch an inspection, enforcing ownership.

    A record owned by someone else is reported as 404, not 403, so the API does
    not confirm that the id exists.
    """
    inspection = db.session.get(Inspection, parse_uuid_or_404(inspection_id, "Inspection"))

    if inspection is None or inspection.is_deleted:
        raise NotFoundError("Inspection not found.")

    if inspection.user_id != user.id and not user.is_admin:
        raise NotFoundError("Inspection not found.")

    return inspection


def list_inspections(
    user: User,
    page: int,
    page_size: int,
    status: str | None = None,
    damage_type: str | None = None,
    customer_name: str | None = None,
    vehicle_type: str | None = None,
    date_from: str | None = None,
    date_to: str | None = None,
) -> Page:
    """The history list, filtered and paginated."""
    query = sa.select(Inspection).where(Inspection.deleted_at.is_(None))

    # Admins see everything; everyone else sees only their own history.
    if not user.is_admin:
        query = query.where(Inspection.user_id == user.id)

    if status:
        valid = {s.value for s in InspectionStatus}
        if status not in valid:
            raise ValidationError(
                f"Unknown status filter. Allowed: {', '.join(sorted(valid))}.",
            )
        query = query.where(Inspection.status == status)

    if damage_type:
        damage_type_row = db.session.scalar(
            sa.select(DamageType).where(DamageType.class_key == damage_type)
        )
        if damage_type_row is None:
            raise ValidationError(f"Unknown damage type '{damage_type}'.")
        query = query.where(
            Inspection.id.in_(
                sa.select(Detection.inspection_id).where(
                    Detection.damage_type_id == damage_type_row.id
                )
            )
        )

    if customer_name:
        # Partial and case-insensitive: this is a "find the customer" box, and
        # the caller cannot be expected to know the exact stored spelling.
        query = query.where(Inspection.customer_name.ilike(f"%{customer_name.strip()}%"))

    if vehicle_type:
        query = query.where(Inspection.vehicle_type == vehicle_type.strip().lower())

    if date_from:
        query = query.where(Inspection.created_at >= _parse_date(date_from, "date_from"))
    if date_to:
        query = query.where(Inspection.created_at <= _parse_date(date_to, "date_to"))

    total = db.session.scalar(sa.select(sa.func.count()).select_from(query.subquery())) or 0

    rows = db.session.scalars(
        query.order_by(Inspection.created_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    return Page(items=list(rows), page=page, page_size=page_size, total=total)


def _parse_date(value: str, field: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError as exc:
        raise ValidationError(
            f"{field} must be an ISO-8601 date, e.g. 2026-08-18 or 2026-08-18T10:00:00Z."
        ) from exc
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed


def soft_delete_inspection(inspection: Inspection) -> None:
    """Mark as deleted; the row and its history stay in the database."""
    inspection.deleted_at = datetime.now(timezone.utc)
    db.session.commit()
    logger.info(
        "Inspection soft deleted",
        extra={"extra_fields": {"inspection_id": str(inspection.id)}},
    )


def user_damage_stats(user: User) -> dict:
    """Counts per damage class and per severity, for dashboard tiles."""
    scope = sa.select(Inspection.id).where(
        Inspection.deleted_at.is_(None),
        Inspection.status.in_([InspectionStatus.COMPLETED, InspectionStatus.PARTIAL_SUCCESS]),
    )
    if not user.is_admin:
        scope = scope.where(Inspection.user_id == user.id)

    by_class = db.session.execute(
        sa.select(DamageType.class_key, DamageType.display_name, sa.func.count(Detection.id))
        .join(Detection, Detection.damage_type_id == DamageType.id)
        .where(Detection.inspection_id.in_(scope))
        .group_by(DamageType.class_key, DamageType.display_name)
    ).all()

    by_severity = db.session.execute(
        sa.select(Detection.severity, sa.func.count(Detection.id))
        .where(Detection.inspection_id.in_(scope))
        .group_by(Detection.severity)
    ).all()

    total_inspections = (
        db.session.scalar(sa.select(sa.func.count()).select_from(scope.subquery())) or 0
    )

    return {
        "total_inspections": total_inspections,
        "by_damage_type": [
            {"class_key": key, "label": label, "count": count} for key, label, count in by_class
        ],
        "by_severity": {severity: count for severity, count in by_severity},
    }
