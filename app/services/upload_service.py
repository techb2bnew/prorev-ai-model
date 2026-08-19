"""Cloudinary signed uploads.

The frontend uploads directly to Cloudinary. It cannot hold the API secret, so
the backend signs the upload parameters and hands back everything the browser
needs - the secret itself never leaves the server.
"""

import logging
import time

import cloudinary
import cloudinary.utils
from flask import current_app

from app.errors import ConfigurationError
from app.utils.image_formats import extensions_list

logger = logging.getLogger(__name__)


def configure_cloudinary(app) -> None:
    """Called once from the app factory."""
    cloud_name = app.config.get("CLOUDINARY_CLOUD_NAME")
    if not cloud_name:
        app.logger.warning(
            "Cloudinary is not configured; /uploads/signature will return 500 until "
            "CLOUDINARY_* variables are set in .env"
        )
        return

    cloudinary.config(
        cloud_name=cloud_name,
        api_key=app.config.get("CLOUDINARY_API_KEY"),
        api_secret=app.config.get("CLOUDINARY_API_SECRET"),
        secure=True,
    )


def _require_credentials() -> tuple[str, str, str]:
    cloud_name = current_app.config.get("CLOUDINARY_CLOUD_NAME")
    api_key = current_app.config.get("CLOUDINARY_API_KEY")
    api_secret = current_app.config.get("CLOUDINARY_API_SECRET")

    if not (cloud_name and api_key and api_secret):
        raise ConfigurationError(
            "Cloudinary credentials are missing. Set CLOUDINARY_CLOUD_NAME, "
            "CLOUDINARY_API_KEY and CLOUDINARY_API_SECRET in .env."
        )
    return cloud_name, api_key, api_secret


def create_upload_signature(user_id: str, folder: str | None = None) -> dict:
    """Build the signed parameters for one direct browser upload."""
    cloud_name, api_key, api_secret = _require_credentials()

    base_folder = folder or current_app.config.get("CLOUDINARY_UPLOAD_FOLDER", "dent-inspections")
    # One sub-folder per user keeps assets tidy and easy to purge later.
    target_folder = f"{base_folder}/{user_id}"
    timestamp = int(time.time())

    params_to_sign = {"folder": target_folder, "timestamp": timestamp}
    signature = cloudinary.utils.api_sign_request(params_to_sign, api_secret)

    return {
        "cloud_name": cloud_name,
        "api_key": api_key,
        "timestamp": timestamp,
        "folder": target_folder,
        "signature": signature,
        "upload_url": f"https://api.cloudinary.com/v1_1/{cloud_name}/image/upload",
        "constraints": {
            "allowed_formats": extensions_list(),
            "max_bytes": current_app.config.get("MAX_IMAGE_BYTES"),
            "max_images": current_app.config.get("MAX_IMAGES_PER_INSPECTION"),
        },
    }
