"""SQLAlchemy models.

Every model is imported here so that ``db.create_all()`` sees the full metadata.
"""

from app.models.base import Base, JSONType, SoftDeleteMixin, TimestampMixin, UUIDMixin, utcnow
from app.models.damage_type import DamageType
from app.models.detection import Detection
from app.models.enums import (
    SEVERITY_ORDER,
    VEHICLE_TYPE_LABELS,
    VEHICLE_TYPES,
    VIEW_ANGLES,
    ImageStatus,
    InspectionStatus,
    Severity,
    UserRole,
    VehicleType,
    ViewAngle,
    max_severity,
)
from app.models.inspection import Inspection
from app.models.inspection_image import InspectionImage
from app.models.token_blocklist import TokenBlocklist
from app.models.user import User

__all__ = [
    "Base",
    "JSONType",
    "SoftDeleteMixin",
    "TimestampMixin",
    "UUIDMixin",
    "utcnow",
    "DamageType",
    "Detection",
    "Inspection",
    "InspectionImage",
    "TokenBlocklist",
    "User",
    "ImageStatus",
    "InspectionStatus",
    "Severity",
    "SEVERITY_ORDER",
    "UserRole",
    "VEHICLE_TYPES",
    "VEHICLE_TYPE_LABELS",
    "VehicleType",
    "VIEW_ANGLES",
    "ViewAngle",
    "max_severity",
]
