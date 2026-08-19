from pydantic import BaseModel, Field, field_validator

from app.models.enums import VEHICLE_TYPES, VIEW_ANGLES


class DetectionSettingsInput(BaseModel):
    """Per-inspection model sensitivity.

    Either name a preset, or set the values directly - explicit values win over
    the preset. Mirrors the reference API's conf/iou/imgsz/augment form fields.
    """

    preset: str | None = None
    confidence: float | None = Field(default=None, ge=0.01, le=1.0)
    iou: float | None = Field(default=None, ge=0.1, le=0.95)
    input_size: int | None = Field(default=None, ge=320, le=2048)
    augment: bool | None = None
    use_clahe: bool | None = None

    @field_validator("preset")
    @classmethod
    def known_preset(cls, value: str | None) -> str | None:
        if value is None:
            return None
        normalised = value.strip().lower()
        allowed = {"balanced", "sensitive", "strict"}
        if normalised not in allowed:
            raise ValueError(f"Unknown preset. Allowed: {', '.join(sorted(allowed))}.")
        return normalised

    @field_validator("input_size")
    @classmethod
    def multiple_of_32(cls, value: int | None) -> int | None:
        # YOLO strides by 32; anything else is silently rounded by Ultralytics,
        # which would make the stored settings a lie.
        if value is not None and value % 32 != 0:
            raise ValueError("input_size must be a multiple of 32 (e.g. 640, 1024, 1280).")
        return value


class CreateInspectionRequest(BaseModel):
    """One inspection: who it is for, what kind of vehicle, and the photos.

    ``vehicle_type`` is the car's body style, not its category - everything here
    is a car. ``images`` is keyed by which side of the vehicle each photo shows,
    so the view angle is part of the structure rather than a field that can
    disagree with it. The frontend uploads to Cloudinary first and sends the URLs
    here - the backend never receives the files themselves.

        {
          "customer_name": "test",
          "vehicle_type": "suv",
          "images": {
            "front": "https://res.cloudinary.com/.../front.jpg",
            "back":  "https://res.cloudinary.com/.../back.jpg",
            "left":  "https://res.cloudinary.com/.../left.jpg",
            "right": "https://res.cloudinary.com/.../right.jpg",
            "top":   "https://res.cloudinary.com/.../top.jpg"
          }
        }
    """

    customer_name: str = Field(min_length=1, max_length=150)
    vehicle_type: str = Field(min_length=1, max_length=40)
    images: dict[str, str]
    settings: DetectionSettingsInput | None = None

    @field_validator("customer_name")
    @classmethod
    def tidy_name(cls, value: str) -> str:
        cleaned = " ".join(value.split())
        if not cleaned:
            raise ValueError("customer_name cannot be blank.")
        return cleaned

    @field_validator("vehicle_type")
    @classmethod
    def known_vehicle_type(cls, value: str) -> str:
        """A car body style, from a closed set.

        Every vehicle here is a car, so this is the body shape - `sedan`, `suv`
        and so on. Closed rather than free text so that history filters and
        reporting group cleanly instead of splitting across spellings.
        """
        cleaned = " ".join(value.split()).lower()
        if cleaned not in VEHICLE_TYPES:
            raise ValueError(
                f"Unknown vehicle_type '{value}'. Allowed: {', '.join(VEHICLE_TYPES)}."
            )
        return cleaned

    @field_validator("images")
    @classmethod
    def known_views_with_https_urls(cls, value: dict[str, str]) -> dict[str, str]:
        if not value:
            raise ValueError(
                f"At least one image is required. Expected keys: {', '.join(VIEW_ANGLES)}."
            )

        cleaned: dict[str, str] = {}
        for raw_view, raw_url in value.items():
            view = str(raw_view).strip().lower()
            if view not in VIEW_ANGLES:
                raise ValueError(
                    f"Unknown image view '{raw_view}'. Allowed: {', '.join(VIEW_ANGLES)}."
                )
            if view in cleaned:
                raise ValueError(f"View '{view}' was given more than once.")

            url = str(raw_url).strip()
            if not url.startswith("https://"):
                raise ValueError(f"The {view} image must be an https URL.")
            cleaned[view] = url

        if len(set(cleaned.values())) != len(cleaned):
            raise ValueError("The same image URL was used for more than one view.")

        # Canonical order, so sequence_no does not depend on JSON key order.
        return {view: cleaned[view] for view in VIEW_ANGLES if view in cleaned}


class UploadSignatureRequest(BaseModel):
    folder: str | None = Field(default=None, max_length=120)
