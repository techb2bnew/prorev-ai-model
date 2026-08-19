"""Reference data the UI needs, plus the dashboard stats.

These are served from the backend so the frontend never keeps a second copy of a
list or a threshold that could drift out of step with what the API enforces.
"""

from flask import Blueprint, current_app, jsonify
from flask_jwt_extended import jwt_required

from app.api.deps import current_user
from app.models import VEHICLE_TYPE_LABELS
from app.services.inspection_service import user_damage_stats
from app.services.report_service import active_damage_types

bp = Blueprint("reference", __name__)


@bp.get("/damage-types")
def index():
    """The damage classes the model can detect, with their UI colours.

    Public so the frontend can build its legend before a user logs in.
    """
    rows = active_damage_types()
    return jsonify({"items": [row.to_dict() for row in rows], "total": len(rows)})


@bp.get("/vehicle-types")
def vehicle_types():
    """The car body styles an inspection can be tagged with.

    Every vehicle inspected is a car, so these are body shapes - sedan, SUV and
    so on. Public, so the submission form can be built before a user logs in.
    """
    return jsonify(
        {
            "items": [{"key": key, "label": label} for key, label in VEHICLE_TYPE_LABELS.items()],
            "total": len(VEHICLE_TYPE_LABELS),
        }
    )


@bp.get("/detection-presets")
def detection_presets():
    """The sensitivity modes a client can choose per inspection.

    Served from the backend so the UI does not keep its own copy of the numbers.
    """
    presets = current_app.config["DETECTION_PRESETS"]
    default = current_app.config.get("DEFAULT_DETECTION_PRESET", "balanced")
    return jsonify(
        {
            "items": [
                {
                    "key": key,
                    "label": value["label"],
                    "description": value["description"],
                    "confidence": value["confidence"],
                    "iou": value["iou"],
                    "input_size": value["input_size"],
                    "augment": value["augment"],
                    "is_default": key == default,
                }
                for key, value in presets.items()
            ],
            "default": default,
        }
    )


@bp.get("/stats/summary")
@jwt_required()
def stats_summary():
    """Counts per damage class and per severity, for dashboard tiles."""
    return jsonify(user_damage_stats(current_user()))
