import logging

import sqlalchemy as sa
from flask import Blueprint, current_app, jsonify

from app.extensions import db
from app.inference.registry import get_detector

logger = logging.getLogger(__name__)

bp = Blueprint("health", __name__)


@bp.get("/health")
def health():
    """Liveness - is the process up. No dependency checks."""
    return jsonify({"status": "ok", "service": "dent-detection-api"})


@bp.get("/health/ready")
def readiness():
    """Readiness - can we actually serve traffic (database + model)."""
    checks: dict[str, dict] = {}

    try:
        db.session.execute(sa.text("SELECT 1"))
        checks["database"] = {"ok": True}
    except Exception as exc:
        logger.error("Database readiness check failed: %s", exc)
        checks["database"] = {"ok": False, "error": str(exc)}

    try:
        detector = get_detector(current_app.config)
        checks["model"] = {"ok": True, **detector.describe()}
    except Exception as exc:
        logger.error("Model readiness check failed: %s", exc)
        checks["model"] = {"ok": False, "error": str(exc)}

    cloudinary_ready = bool(
        current_app.config.get("CLOUDINARY_CLOUD_NAME")
        and current_app.config.get("CLOUDINARY_API_KEY")
        and current_app.config.get("CLOUDINARY_API_SECRET")
    )
    checks["cloudinary"] = {"ok": cloudinary_ready, "configured": cloudinary_ready}

    # Cloudinary is only needed for uploads, so it does not gate readiness.
    ready = checks["database"]["ok"] and checks["model"]["ok"]
    return jsonify({"status": "ready" if ready else "not_ready", "checks": checks}), (
        200 if ready else 503
    )
