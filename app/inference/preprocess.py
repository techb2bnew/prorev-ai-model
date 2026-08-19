"""Image preparation and quality diagnostics.

Implements enhancements 1, 3 and 4 from DOCUMENTATION.md section 7, which exist
because the most common cause of a missed detection is the photo, not the model.
"""

import logging

import cv2
import numpy as np
from PIL import Image, ImageOps

logger = logging.getLogger(__name__)

# Enhancement 4 thresholds, from DOCUMENTATION.md.
BLUR_THRESHOLD = 80.0
DARK_THRESHOLD = 40.0
BRIGHT_THRESHOLD = 225.0


def correct_orientation(image: Image.Image) -> Image.Image:
    """Enhancement 1: honour the EXIF rotation flag that phones set.

    A phone photo carries its rotation in metadata rather than in the pixels.
    Loaded naively the car comes out sideways, and since the model was trained
    on upright cars that alone can yield zero detections.
    """
    try:
        return ImageOps.exif_transpose(image)
    except Exception as exc:  # corrupt EXIF should not lose the image
        logger.warning("EXIF orientation could not be applied: %s", exc)
        return image


def enhance_damage_contrast(image_rgb: np.ndarray) -> np.ndarray:
    """Enhancement 3: CLAHE on the L channel in LAB space.

    Clear coat reflects sky and lighting, which flattens faint scratches. Boosting
    local luminance contrast brings those edges back without shifting colour.
    """
    lab = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)

    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced_l = clahe.apply(l_channel)

    merged = cv2.merge((enhanced_l, a_channel, b_channel))
    return cv2.cvtColor(merged, cv2.COLOR_LAB2RGB)


def analyze_image_quality(image_rgb: np.ndarray) -> dict:
    """Enhancement 4: blur and exposure diagnostics.

    Returned to the caller so a user who submitted an unusable photo is told
    why, instead of being shown an empty report and left guessing.
    """
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)

    # Variance of the Laplacian: low variance means few sharp edges, i.e. blur.
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    brightness = float(np.mean(gray))

    warnings: list[str] = []
    if blur_score < BLUR_THRESHOLD:
        warnings.append("Image appears blurry or out of focus. Damage edges may be missed.")
    if brightness < DARK_THRESHOLD:
        warnings.append("Image is underexposed. Consider retaking it in better lighting.")
    elif brightness > BRIGHT_THRESHOLD:
        warnings.append("Image has strong glare or overexposure, which can hide scratches.")

    return {
        "blur_score": round(blur_score, 2),
        "brightness": round(brightness, 2),
        "is_blurry": blur_score < BLUR_THRESHOLD,
        "warnings": warnings,
    }
