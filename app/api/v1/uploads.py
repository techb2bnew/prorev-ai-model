from flask import Blueprint, jsonify
from flask_jwt_extended import jwt_required

from app.api.deps import current_user
from app.extensions import limiter
from app.schemas import validate_body
from app.schemas.inspection import UploadSignatureRequest
from app.services.upload_service import create_upload_signature

bp = Blueprint("uploads", __name__, url_prefix="/uploads")


@bp.post("/signature")
@jwt_required()
@limiter.limit("60 per hour")
@validate_body(UploadSignatureRequest)
def upload_signature(payload: UploadSignatureRequest):
    """Signed parameters for a direct browser-to-Cloudinary upload.

    The API secret signs the request here and is never sent to the client.
    """
    user = current_user()
    return jsonify(create_upload_signature(str(user.id), folder=payload.folder))
