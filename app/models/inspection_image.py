import uuid

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, JSONType, TimestampMixin, UUIDMixin
from app.models.enums import ImageStatus


class InspectionImage(Base, UUIDMixin, TimestampMixin):
    """A reference to one image in Cloudinary. Binaries never live in this database."""

    __tablename__ = "inspection_images"

    inspection_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("inspections.id", ondelete="CASCADE"), nullable=False, index=True
    )

    cloudinary_public_id: Mapped[str] = mapped_column(sa.String(255), nullable=False)
    secure_url: Mapped[str] = mapped_column(sa.Text, nullable=False)
    thumbnail_url: Mapped[str | None] = mapped_column(sa.Text)

    view_angle: Mapped[str | None] = mapped_column(sa.String(20))
    width: Mapped[int | None] = mapped_column(sa.Integer)
    height: Mapped[int | None] = mapped_column(sa.Integer)
    file_size_bytes: Mapped[int | None] = mapped_column(sa.BigInteger)
    format: Mapped[str | None] = mapped_column(sa.String(10))

    sequence_no: Mapped[int] = mapped_column(sa.Integer, default=0, nullable=False)
    status: Mapped[str] = mapped_column(
        sa.String(20), default=ImageStatus.PENDING, nullable=False
    )
    failure_reason: Mapped[str | None] = mapped_column(sa.Text)

    #: Blur/exposure diagnostics for this photo, so a user who submitted an
    #: unusable image is told why rather than shown an empty result.
    quality_report: Mapped[dict | None] = mapped_column(JSONType)

    inspection: Mapped["Inspection"] = relationship(back_populates="images")  # noqa: F821
    detections: Mapped[list["Detection"]] = relationship(  # noqa: F821
        back_populates="image", cascade="all, delete-orphan", lazy="selectin"
    )
