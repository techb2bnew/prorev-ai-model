"""The image formats this system accepts.

Defined once because the same list is enforced in three places that must agree:
the upload signature tells Cloudinary what to accept, the request schema checks
what the client claims it uploaded, and the loader checks what actually decoded.
"""

#: Extensions as a client and Cloudinary spell them.
ALLOWED_EXTENSIONS = ("jpg", "jpeg", "png", "webp")

#: The same formats as PIL reports them from a decoded image.
ALLOWED_PIL_FORMATS = frozenset({"JPEG", "PNG", "WEBP"})


def extensions_list() -> list[str]:
    """A fresh mutable copy, for JSON payloads."""
    return list(ALLOWED_EXTENSIONS)


def format_list() -> str:
    """The extensions as a human-readable string, for error messages."""
    return ", ".join(sorted(ALLOWED_EXTENSIONS))
