"""Reading and building Cloudinary delivery URLs.

A Cloudinary URL looks like ``.../upload/v123/folder/id.jpg``. Inserting a
transformation segment after ``/upload/`` is how both the thumbnail and the
downscale-before-download URLs are produced, so the splitting lives here once.
"""

import re

_MARKER = "/upload/"

#: A version segment, e.g. `v1787118301`.
_VERSION = re.compile(r"^v\d+$")


def with_transformation(secure_url: str, transformation: str) -> str | None:
    """Insert ``transformation`` into a Cloudinary URL.

    Returns None when the URL is empty or is not a Cloudinary delivery URL, so
    callers can decide whether that is a problem or simply means "no thumbnail".
    """
    if not secure_url or _MARKER not in secure_url:
        return None
    head, tail = secure_url.split(_MARKER, 1)
    return f"{head}{_MARKER}{transformation}/{tail}"


def public_id_from_url(secure_url: str) -> str | None:
    """The Cloudinary public id carried by a delivery URL.

    ``.../upload/v1787118301/dent-inspections/abc/xy.jpg`` -> ``dent-inspections/abc/xy``.
    The folder can be nested, so everything between the version segment and the
    extension is kept. Returns None when the URL is not a Cloudinary one.

    Only used as a label - the image itself is always fetched from the URL the
    client sent - so a transformed URL yielding an approximate id is harmless.
    """
    if not secure_url or _MARKER not in secure_url:
        return None

    path = secure_url.split(_MARKER, 1)[1].split("?", 1)[0]
    segments = [segment for segment in path.split("/") if segment]

    # Drop the leading version and any transformation segments (`c_fill,w_320`).
    while segments and (_VERSION.match(segments[0]) or "," in segments[0]):
        segments.pop(0)

    if not segments:
        return None

    public_id = "/".join(segments)
    head, _, extension = public_id.rpartition(".")
    # Only treat the tail as an extension if it looks like one.
    return head if head and extension and "/" not in extension else public_id


def thumbnail_url(secure_url: str, width: int = 320) -> str | None:
    """A square cropped preview, for history lists and image strips."""
    return with_transformation(secure_url, f"c_fill,w_{width},h_{width},q_auto")


def downscaled_url(secure_url: str, target_width: int) -> str:
    """Ask Cloudinary to downscale before sending the bytes.

    Downloading a 1024px image instead of a 4000px one is most of the per-image
    cost. Falls back to the original URL, since fetching it is still correct.
    """
    return with_transformation(secure_url, f"c_limit,w_{target_width},q_auto") or secure_url
