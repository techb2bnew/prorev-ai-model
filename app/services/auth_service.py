"""Registration, login and the current-user lookup."""

import logging
import uuid
from datetime import datetime

import sqlalchemy as sa
from flask_jwt_extended import create_access_token, create_refresh_token

from app.errors import AuthenticationError, ConflictError, NotFoundError
from app.extensions import db
from app.models import TokenBlocklist, User, utcnow
from app.utils.identifiers import parse_uuid_or_404

logger = logging.getLogger(__name__)


def register_user(email: str, password: str, full_name: str | None, phone: str | None) -> User:
    normalised_email = email.strip().lower()

    existing = db.session.scalar(sa.select(User).where(User.email == normalised_email))
    if existing:
        raise ConflictError(
            "An account with this email already exists.", details={"email": normalised_email}
        )

    user = User(email=normalised_email, full_name=full_name, phone=phone)
    user.set_password(password)

    db.session.add(user)
    db.session.commit()

    logger.info("User registered", extra={"extra_fields": {"user_id": str(user.id)}})
    return user


def authenticate(email: str, password: str) -> User:
    user = db.session.scalar(sa.select(User).where(User.email == email.strip().lower()))

    # Same error for unknown email and wrong password, so the response does not
    # reveal which accounts exist.
    if user is None or not user.check_password(password):
        raise AuthenticationError()

    if not user.is_active or user.is_deleted:
        raise AuthenticationError("This account is disabled.")

    return user


def issue_tokens(user: User) -> dict:
    identity = str(user.id)
    claims = {"role": user.role, "email": user.email}
    return {
        "access_token": create_access_token(identity=identity, additional_claims=claims),
        "refresh_token": create_refresh_token(identity=identity, additional_claims=claims),
        "token_type": "Bearer",
    }


def get_user_or_404(user_id: str | uuid.UUID) -> User:
    user = db.session.get(User, parse_uuid_or_404(user_id, "User"))
    if user is None or user.is_deleted:
        raise NotFoundError("User not found.")
    return user


def revoke_token(jti: str, expires_at: datetime) -> None:
    """Block one JWT before its natural expiry. Safe to call twice for the
    same jti - a repeat logout on an already-revoked token is a no-op."""
    already_revoked = db.session.scalar(
        sa.select(TokenBlocklist.id).where(TokenBlocklist.jti == jti)
    )
    if already_revoked:
        return

    db.session.add(TokenBlocklist(jti=jti, expires_at=expires_at))
    db.session.commit()


def delete_account(user: User) -> None:
    """Soft-delete the account. Past inspections are left as-is - deleting an
    account is not a request to erase the history it produced."""
    user.deleted_at = utcnow()
    db.session.commit()
    logger.info("User account deleted", extra={"extra_fields": {"user_id": str(user.id)}})
