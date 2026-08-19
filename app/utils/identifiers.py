"""Parsing the UUIDs that arrive as path segments and query parameters."""

import uuid

from app.errors import NotFoundError, ValidationError


def parse_uuid_or_404(value, what: str = "Resource") -> uuid.UUID:
    """A UUID from an untrusted string, or 404.

    A malformed id cannot match any row, so it is reported as "not found"
    rather than as a validation error - the caller asked for something that
    does not exist.
    """
    if isinstance(value, uuid.UUID):
        return value
    try:
        return uuid.UUID(str(value))
    except (ValueError, AttributeError, TypeError) as exc:
        raise NotFoundError(f"{what} not found.") from exc


def parse_uuid_or_422(value, field: str) -> uuid.UUID:
    """A UUID from a filter the caller supplied, or 422.

    Unlike a path segment, a bad filter value is the caller's mistake to fix,
    so it is worth telling them which field was wrong.
    """
    try:
        return uuid.UUID(str(value))
    except (ValueError, AttributeError, TypeError) as exc:
        raise ValidationError(f"{field} must be a valid UUID.") from exc
