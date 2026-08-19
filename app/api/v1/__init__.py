"""Version 1 of the API. All routes are mounted under /api/v1."""

from flask import Blueprint

from app.api.v1 import auth, health, inspections, reference, uploads

bp = Blueprint("v1", __name__, url_prefix="/api/v1")

bp.register_blueprint(health.bp)
bp.register_blueprint(auth.bp)
bp.register_blueprint(uploads.bp)
bp.register_blueprint(inspections.bp)
bp.register_blueprint(reference.bp)
