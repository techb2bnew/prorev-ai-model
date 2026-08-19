from flask import Blueprint, jsonify, request
from flask_jwt_extended import jwt_required

from app.api.deps import current_inspection, current_user, idempotency_key
from app.extensions import limiter
from app.schemas import validate_body
from app.schemas.inspection import CreateInspectionRequest
from app.services import inspection_service
from app.services.report_service import (
    build_report,
    error_block,
    serialise_identity,
    serialise_inspection,
    serialise_summary_row,
)
from app.tasks.inspection_job import process_inspection
from app.tasks.queue import enqueue
from app.utils.pagination import get_pagination_args

bp = Blueprint("inspections", __name__, url_prefix="/inspections")


@bp.post("")
@jwt_required()
@limiter.limit("60 per hour")
@validate_body(CreateInspectionRequest)
def create(payload: CreateInspectionRequest):
    """Submit images for inspection.

    Returns 202 immediately and runs the model in the background, so the client
    is never held open for the length of inference.
    """
    inspection, created = inspection_service.create_inspection(
        user=current_user(),
        customer_name=payload.customer_name,
        vehicle_type=payload.vehicle_type,
        images=payload.images,
        settings_input=payload.settings,
        idempotency_key=idempotency_key(),
    )

    if created:
        enqueue(process_inspection, str(inspection.id))

    return (
        jsonify(
            {
                **serialise_identity(inspection),
                "detection_preset": inspection.detection_preset,
                "detection_settings": inspection.detection_settings,
                "created": created,
                "message": (
                    "Inspection queued for analysis."
                    if created
                    else "This inspection was already submitted."
                ),
            }
        ),
        202 if created else 200,
    )


@bp.get("")
@jwt_required()
def index():
    """Paginated inspection history with filters."""
    page, page_size = get_pagination_args()

    result = inspection_service.list_inspections(
        user=current_user(),
        page=page,
        page_size=page_size,
        status=request.args.get("status"),
        damage_type=request.args.get("damage_type"),
        customer_name=request.args.get("customer_name"),
        vehicle_type=request.args.get("vehicle_type"),
        date_from=request.args.get("date_from"),
        date_to=request.args.get("date_to"),
    )
    return jsonify(result.to_dict(serialiser=serialise_summary_row))


@bp.get("/<inspection_id>")
@jwt_required()
def show(inspection_id: str):
    """Full inspection with its report."""
    return jsonify(serialise_inspection(current_inspection(inspection_id)))


@bp.get("/<inspection_id>/status")
@jwt_required()
def status(inspection_id: str):
    """Lightweight poll target - deliberately small, since clients call it repeatedly."""
    inspection = current_inspection(inspection_id)
    return jsonify(
        {
            "id": str(inspection.id),
            "status": inspection.status,
            "is_finished": inspection.is_finished,
            "damage_score": inspection.damage_score,
            "total_detections": inspection.total_detections,
            "error": error_block(inspection),
        }
    )


@bp.get("/<inspection_id>/report")
@jwt_required()
def report(inspection_id: str):
    """Report only, for rendering or exporting."""
    inspection = current_inspection(inspection_id)
    return jsonify(
        {
            "status": inspection.status,
            "customer_name": inspection.customer_name,
            "vehicle_type": inspection.vehicle_type,
            "report": build_report(inspection),
        }
    )


@bp.delete("/<inspection_id>")
@jwt_required()
def destroy(inspection_id: str):
    """Soft delete - the history row and its detections stay in the database."""
    inspection = current_inspection(inspection_id)
    inspection_service.soft_delete_inspection(inspection)
    return jsonify({"id": str(inspection.id), "deleted": True})
