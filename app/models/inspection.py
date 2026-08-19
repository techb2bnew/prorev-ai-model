import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base, JSONType, SoftDeleteMixin, TimestampMixin, UUIDMixin
from app.models.enums import InspectionStatus, Severity


class Inspection(Base, UUIDMixin, TimestampMixin, SoftDeleteMixin):
    """One submission of up to five photos. This row *is* the history record.

    Every column below is either read by the API or needed to run the job. The
    denormalised ones (`damage_score`, `damage_summary`, `total_detections`,
    `total_area_percent`, `overall_severity`) are deliberate: the history list
    and dashboard render straight from these without aggregating detections for
    every row on every request.
    """

    __tablename__ = "inspections"
    __table_args__ = (
        # The history list is always "this user's, newest first", so the two
        # columns are indexed together rather than separately.
        sa.Index("ix_inspections_user_created", "user_id", "created_at"),
    )

    # --- Ownership ---

    #: Who submitted it. Scopes every read, and cascades on account deletion.
    user_id: Mapped[uuid.UUID] = mapped_column(
        sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )

    #: Who the inspection is *for*, which is not the account holder - one
    #: surveyor account submits work for many customers. Indexed because the
    #: history page searches on it.
    customer_name: Mapped[str | None] = mapped_column(sa.String(150), index=True)

    #: Car body style (sedan, suv, hatchback...). Every vehicle here is a car,
    #: so this is the shape, not the category. Indexed because reporting slices
    #: by it, and the same damage reads differently across body styles.
    vehicle_type: Mapped[str | None] = mapped_column(sa.String(40), index=True)

    # --- Lifecycle ---

    #: queued -> processing -> completed / partial_success / failed. Indexed
    #: because it is the most-used history filter and drives the client's poll.
    status: Mapped[str] = mapped_column(
        sa.String(20), default=InspectionStatus.QUEUED, nullable=False, index=True
    )

    #: Set when the caller sends an Idempotency-Key. Unique, so a retried or
    #: double-clicked submit returns the original instead of creating a twin.
    idempotency_key: Mapped[str | None] = mapped_column(sa.String(120), unique=True, index=True)

    # --- Headline result ---

    #: Worst severity across the whole inspection - the one-word answer.
    overall_severity: Mapped[str] = mapped_column(
        sa.String(20), default=Severity.NONE, nullable=False
    )

    #: Aggregate 0-100 score, per the formula in DOCUMENTATION.md section 4.
    #: Stored rather than recomputed so history rows sort and filter on it.
    damage_score: Mapped[int] = mapped_column(sa.Integer, default=0, nullable=False)

    #: How many detections were kept. Stored so the poll endpoint and history
    #: list can report progress without counting rows per inspection.
    total_detections: Mapped[int] = mapped_column(sa.Integer, default=0, nullable=False)

    #: Mean share of each analysed photo that shows damage. Averaged, not summed:
    #: five photos at 60% each is 60% damaged, not 300%.
    total_area_percent: Mapped[float] = mapped_column(sa.Float, default=0.0, nullable=False)

    #: Per-class counts, denormalised. This is what makes the history list one
    #: query instead of one aggregate per row.
    damage_summary: Mapped[dict | None] = mapped_column(JSONType)

    #: In-scope findings the model saw but the confidence threshold excluded.
    #: Surfaced so a thin report reads as "3 more below 0.35" rather than as the
    #: model having missed the damage.
    below_threshold_count: Mapped[int] = mapped_column(sa.Integer, default=0, nullable=False)

    # --- Reproducibility: what was run, and with what settings ---

    #: The preset name the caller chose, e.g. "balanced" or "sensitive+custom".
    detection_preset: Mapped[str | None] = mapped_column(sa.String(20))

    #: The exact conf/iou/imgsz/augment used. Raw model output is not retained,
    #: so this is what lets a surprising report be explained or reproduced.
    detection_settings: Mapped[dict | None] = mapped_column(JSONType)

    #: Which model produced the findings. Kept per-inspection because the
    #: weights can be swapped between runs, and an old report must not silently
    #: appear to have come from the current model.
    model_name: Mapped[str | None] = mapped_column(sa.String(100))
    model_version: Mapped[str | None] = mapped_column(sa.String(50))
    model_backend: Mapped[str | None] = mapped_column(sa.String(40))

    # --- Timing and failure ---

    #: When the job finished. Doubles as the report's `generated_at`.
    processing_completed_at: Mapped[datetime | None] = mapped_column(sa.DateTime(timezone=True))

    #: Wall-clock duration of the job, shown in the UI and used to spot a model
    #: or host that has become slow.
    processing_ms: Mapped[int | None] = mapped_column(sa.Integer)

    #: Why it failed, in a form the client can branch on plus a message it can
    #: show. Both null on success.
    error_code: Mapped[str | None] = mapped_column(sa.String(60))
    error_message: Mapped[str | None] = mapped_column(sa.Text)

    user: Mapped["User"] = relationship(back_populates="inspections")  # noqa: F821
    images: Mapped[list["InspectionImage"]] = relationship(  # noqa: F821
        back_populates="inspection",
        cascade="all, delete-orphan",
        order_by="InspectionImage.sequence_no",
        lazy="selectin",
    )
    detections: Mapped[list["Detection"]] = relationship(  # noqa: F821
        back_populates="inspection", cascade="all, delete-orphan", lazy="selectin"
    )

    @property
    def image_count(self) -> int:
        """How many photos were submitted.

        Derived rather than stored: `images` is eager-loaded anyway, and a second
        copy of the number could only ever drift away from the rows themselves.
        """
        return len(self.images)

    @property
    def is_finished(self) -> bool:
        return self.status in {
            InspectionStatus.COMPLETED,
            InspectionStatus.PARTIAL_SUCCESS,
            InspectionStatus.FAILED,
        }
