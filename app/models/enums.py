"""Shared string enums. Stored as plain VARCHAR so adding a value needs no migration."""

from enum import StrEnum


class UserRole(StrEnum):
    USER = "user"
    SURVEYOR = "surveyor"
    ADMIN = "admin"


class InspectionStatus(StrEnum):
    QUEUED = "queued"
    PROCESSING = "processing"
    COMPLETED = "completed"
    PARTIAL_SUCCESS = "partial_success"
    FAILED = "failed"


class ImageStatus(StrEnum):
    PENDING = "pending"
    PROCESSED = "processed"
    FAILED = "failed"


class Severity(StrEnum):
    NONE = "none"
    MINOR = "minor"
    MODERATE = "moderate"
    SEVERE = "severe"


# Ordered weakest -> strongest, used to pick the overall severity of an inspection.
SEVERITY_ORDER: list[str] = [
    Severity.NONE,
    Severity.MINOR,
    Severity.MODERATE,
    Severity.SEVERE,
]


def max_severity(values) -> str:
    """Return the most serious severity in ``values`` (``none`` when empty)."""
    ranked = [v for v in values if v in SEVERITY_ORDER]
    if not ranked:
        return Severity.NONE
    return max(ranked, key=SEVERITY_ORDER.index)


class VehicleType(StrEnum):
    """Car body style.

    Every vehicle this system inspects is a car - the model was trained on car
    damage - so this records the *shape* of the car, not whether it is a car.
    It matters because the same dent reads differently on a hatchback tailgate
    than on an SUV rear quarter, and because it is what fleet and claims
    reporting slices by.
    """

    HATCHBACK = "hatchback"
    SEDAN = "sedan"
    SUV = "suv"
    MUV = "muv"
    COUPE = "coupe"
    CONVERTIBLE = "convertible"
    PICKUP = "pickup"
    VAN = "van"
    #: Escape hatch, so an unusual body style never blocks a submission.
    OTHER = "other"


#: Display labels for the UI, so the frontend keeps no second copy of the list.
VEHICLE_TYPE_LABELS: dict[str, str] = {
    VehicleType.HATCHBACK: "Hatchback",
    VehicleType.SEDAN: "Sedan",
    VehicleType.SUV: "SUV",
    VehicleType.MUV: "MUV / MPV",
    VehicleType.COUPE: "Coupe",
    VehicleType.CONVERTIBLE: "Convertible",
    VehicleType.PICKUP: "Pickup",
    VehicleType.VAN: "Van",
    VehicleType.OTHER: "Other",
}

#: The body styles, in the order the UI should offer them.
VEHICLE_TYPES: tuple[str, ...] = tuple(VEHICLE_TYPE_LABELS)


class ViewAngle(StrEnum):
    """The five sides of a vehicle a submission is made up of.

    Declaration order is the canonical order: it decides `sequence_no`, and so
    the order photos appear in a report.
    """

    FRONT = "front"
    BACK = "back"
    LEFT = "left"
    RIGHT = "right"
    TOP = "top"


#: The five view keys, in canonical order.
VIEW_ANGLES: tuple[str, ...] = tuple(angle.value for angle in ViewAngle)
