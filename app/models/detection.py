import uuid
from decimal import Decimal

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, JSONType, TimestampMixin, UUIDMixin


class Detection(Base, UUIDMixin, TimestampMixin):
    """One damage instance found in one image."""

    __tablename__ = "detections"

    inspection_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("inspections.id", ondelete="CASCADE"), nullable=False, index=True
    )
    inspection_image_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("inspection_images.id", ondelete="CASCADE"), nullable=False, index=True
    )
    damage_type_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("damage_types.id", ondelete="RESTRICT"), nullable=False, index=True
    )

    confidence: Mapped[Decimal] = mapped_column(sa.Numeric(5, 4), nullable=False)
    severity: Mapped[str] = mapped_column(sa.String(20), nullable=False)

    # Present for detection models, NULL for pure classification models.
    bbox_x: Mapped[int | None] = mapped_column(sa.Integer)
    bbox_y: Mapped[int | None] = mapped_column(sa.Integer)
    bbox_width: Mapped[int | None] = mapped_column(sa.Integer)
    bbox_height: Mapped[int | None] = mapped_column(sa.Integer)

    # Present only for segmentation models.
    polygon: Mapped[list | None] = mapped_column(JSONType)

    area_ratio: Mapped[Decimal | None] = mapped_column(sa.Numeric(7, 6))

    inspection: Mapped["Inspection"] = relationship(back_populates="detections")  # noqa: F821
    image: Mapped["InspectionImage"] = relationship(back_populates="detections")  # noqa: F821
    damage_type: Mapped["DamageType"] = relationship(lazy="joined")  # noqa: F821

    @property
    def bbox(self) -> dict | None:
        if self.bbox_x is None:
            return None
        return {
            "x": self.bbox_x,
            "y": self.bbox_y,
            "width": self.bbox_width,
            "height": self.bbox_height,
        }

    def to_dict(self) -> dict:
        return {
            "id": str(self.id),
            "class_key": self.damage_type.class_key,
            "label": self.damage_type.display_name,
            "confidence": float(self.confidence),
            "severity": self.severity,
            "bbox": self.bbox,
            "polygon": self.polygon,
            "area_ratio": float(self.area_ratio) if self.area_ratio is not None else None,
        }
