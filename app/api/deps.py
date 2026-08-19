"""Helpers shared by the route modules."""

from flask import request
from flask_jwt_extended import get_jwt_identity

from app.models import Inspection, User
from app.services import auth_service, inspection_service


def current_user() -> User:
    """The authenticated user. Only valid inside a @jwt_required view."""
    return auth_service.get_user_or_404(get_jwt_identity())


def current_inspection(inspection_id: str) -> Inspection:
    """An inspection owned by the authenticated user, or 404."""
    return inspection_service.get_inspection_for_user(inspection_id, current_user())


def idempotency_key() -> str | None:
    """Read the optional Idempotency-Key header used to make POSTs safe to retry."""
    value = request.headers.get("Idempotency-Key", "").strip()
    return value[:120] or None
