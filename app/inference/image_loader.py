"""Fetches an image from Cloudinary and prepares it for the model."""

import io
import logging

import requests
from PIL import Image, UnidentifiedImageError

from app.errors import ImageUnreachableError
from app.inference.base import PreparedImage
from app.inference.preprocess import correct_orientation
from app.utils.cloudinary_url import downscaled_url
from app.utils.image_formats import ALLOWED_PIL_FORMATS

logger = logging.getLogger(__name__)

#: Below this on the shorter side there is not enough detail to detect damage
#: reliably. Checked after decoding rather than from the request, because the
#: request carries only a URL - and the decoded image is the truth anyway.
MIN_DIMENSION = 320


def load_image(
    secure_url: str,
    public_id: str,
    *,
    timeout: int = 20,
    max_bytes: int = 10 * 1024 * 1024,
    target_width: int | None = None,
) -> PreparedImage:
    """Download and decode one image.

    Raises ImageUnreachableError for anything that makes the image unusable -
    the caller marks that single image as failed and carries on with the rest.
    """
    url = downscaled_url(secure_url, target_width) if target_width else secure_url

    try:
        response = requests.get(url, timeout=timeout, stream=True)
        response.raise_for_status()
    except requests.RequestException as exc:
        raise ImageUnreachableError(f"Could not download image: {exc}") from exc

    # Trust the header when present, but still cap what we actually read.
    declared = response.headers.get("Content-Length")
    if declared and declared.isdigit() and int(declared) > max_bytes:
        raise ImageUnreachableError(
            f"Image is larger than the {max_bytes} byte limit.",
            details={"content_length": int(declared)},
        )

    chunks = bytearray()
    for chunk in response.iter_content(chunk_size=65536):
        chunks.extend(chunk)
        if len(chunks) > max_bytes:
            raise ImageUnreachableError(f"Image exceeded the {max_bytes} byte limit while downloading.")

    if not chunks:
        raise ImageUnreachableError("Downloaded image was empty.")

    try:
        image = Image.open(io.BytesIO(bytes(chunks)))
        image.load()
    except (UnidentifiedImageError, OSError) as exc:
        raise ImageUnreachableError(f"Image could not be decoded: {exc}") from exc

    if image.format and image.format.upper() not in ALLOWED_PIL_FORMATS:
        raise ImageUnreachableError(
            f"Unsupported image format: {image.format}",
            details={"allowed": sorted(ALLOWED_PIL_FORMATS)},
        )

    # Enhancement 1 (DOCUMENTATION.md 7): apply the EXIF rotation flag before
    # anything else. A sideways car is out of distribution for this model and is
    # a common cause of zero detections on an obviously damaged vehicle.
    image = correct_orientation(image)

    if image.mode != "RGB":
        image = image.convert("RGB")

    # Cloudinary's c_limit only ever shrinks, so a small original stays small.
    if min(image.width, image.height) < MIN_DIMENSION:
        raise ImageUnreachableError(
            f"Image is {image.width}x{image.height}; at least {MIN_DIMENSION}px on the "
            "shorter side is needed to detect damage reliably.",
            details={"width": image.width, "height": image.height, "minimum": MIN_DIMENSION},
        )

    return PreparedImage(
        image=image,
        width=image.width,
        height=image.height,
        source_url=secure_url,
        public_id=public_id,
    )
