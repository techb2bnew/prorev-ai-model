from datetime import datetime, timezone

from flask import Blueprint, jsonify
from flask_jwt_extended import get_jwt, get_jwt_identity, jwt_required

from app.api.deps import current_user
from app.extensions import limiter
from app.schemas import validate_body
from app.schemas.auth import LoginRequest, RegisterRequest
from app.services import auth_service

bp = Blueprint("auth", __name__, url_prefix="/auth")


@bp.post("/register")
@limiter.limit("10 per hour")
@validate_body(RegisterRequest)
def register(payload: RegisterRequest):
    user = auth_service.register_user(
        email=payload.email,
        password=payload.password,
        full_name=payload.full_name,
        phone=payload.phone,
    )
    tokens = auth_service.issue_tokens(user)
    return jsonify({"user": user.to_dict(), **tokens}), 201


@bp.post("/login")
@limiter.limit("20 per hour")
@validate_body(LoginRequest)
def login(payload: LoginRequest):
    user = auth_service.authenticate(payload.email, payload.password)
    tokens = auth_service.issue_tokens(user)
    return jsonify({"user": user.to_dict(), **tokens})


@bp.post("/refresh")
@jwt_required(refresh=True)
def refresh():
    user = auth_service.get_user_or_404(get_jwt_identity())
    tokens = auth_service.issue_tokens(user)
    # Only the access token is handed back here; the refresh token keeps its own expiry.
    return jsonify({"access_token": tokens["access_token"], "token_type": "Bearer"})


@bp.get("/me")
@jwt_required()
def me():
    return jsonify({"user": current_user().to_dict()})


@bp.post("/logout")
@jwt_required()
def logout():
    """Revoke the access token used on this request. It becomes unusable
    immediately, rather than lingering valid until it expires on its own."""
    claims = get_jwt()
    expires_at = datetime.fromtimestamp(claims["exp"], tz=timezone.utc)
    auth_service.revoke_token(claims["jti"], expires_at)
    return jsonify({"message": "Logged out."})


@bp.delete("/me")
@jwt_required()
def delete_account():
    """Soft-delete the caller's own account and revoke the token used to do it."""
    user = current_user()
    claims = get_jwt()
    expires_at = datetime.fromtimestamp(claims["exp"], tz=timezone.utc)
    auth_service.revoke_token(claims["jti"], expires_at)
    auth_service.delete_account(user)
    return "", 204
