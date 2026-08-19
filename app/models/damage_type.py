import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, TimestampMixin, UUIDMixin


class DamageType(Base, UUIDMixin, TimestampMixin):
    """Lookup table for the six in-scope damage classes (seeded, not user-editable)."""

    __tablename__ = "damage_types"

    class_key: Mapped[str] = mapped_column(
        sa.String(50), unique=True, nullable=False, index=True
    )
    display_name: Mapped[str] = mapped_column(sa.String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(sa.Text)

    #: The model's own label and class index, kept so a report can always be
    #: traced back to what the model actually emitted.
    model_label: Mapped[str | None] = mapped_column(sa.String(60))
    model_class_index: Mapped[int | None] = mapped_column(sa.Integer)

    #: UI colour from DOCUMENTATION.md section 2, so the frontend does not have
    #: to hardcode a second copy of the palette.
    color_hex: Mapped[str | None] = mapped_column(sa.String(9))

    #: Whether this class counts towards the critical term of the damage score.
    is_critical: Mapped[bool] = mapped_column(sa.Boolean, default=False, nullable=False)

    is_active: Mapped[bool] = mapped_column(sa.Boolean, default=True, nullable=False)
    sort_order: Mapped[int] = mapped_column(sa.Integer, default=0, nullable=False)

    def to_dict(self) -> dict:
        return {
            "class_key": self.class_key,
            "label": self.display_name,
            "description": self.description,
            "model_label": self.model_label,
            "model_class_index": self.model_class_index,
            "color_hex": self.color_hex,
            "is_critical": self.is_critical,
            "is_active": self.is_active,
            "sort_order": self.sort_order,
        }
