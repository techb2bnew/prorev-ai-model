import uuid
from datetime import datetime

import sqlalchemy as sa
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utcnow


class TokenBlocklist(Base):
    """JWTs revoked before their natural expiry, e.g. by /auth/logout.

    Rows are useless once `expires_at` passes - the token they refer to would
    be rejected as expired anyway - but nothing purges them yet. Volume is one
    row per logout, so this is fine until that stops being true.
    """

    __tablename__ = "token_blocklist"

    id: Mapped[uuid.UUID] = mapped_column(sa.Uuid, primary_key=True, default=uuid.uuid4)
    jti: Mapped[str] = mapped_column(sa.String(36), unique=True, nullable=False, index=True)
    expires_at: Mapped[datetime] = mapped_column(sa.DateTime(timezone=True), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True), default=utcnow, nullable=False
    )
