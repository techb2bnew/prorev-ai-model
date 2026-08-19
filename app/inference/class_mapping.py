"""Maps the model's own label strings onto our six in-scope class keys."""

import logging
import re
from pathlib import Path

from app.utils.json_config import clear_cache as clear_json_cache
from app.utils.json_config import load_json_config

logger = logging.getLogger(__name__)

#: The six classes the supplied YOLO11m model detects, verified against best.pt.
SUPPORTED_CLASS_KEYS = (
    "dent",
    "scratch",
    "crack",
    "glass_shatter",
    "lamp_broken",
    "tire_flat",
)


def _load_aliases(path: str | Path) -> dict[str, str]:
    aliases = load_json_config(path).get("aliases", {})
    return {_normalise(key): value for key, value in aliases.items()}


def _normalise(label: str) -> str:
    """Fold label spelling differences: 'Scratch Deep' / 'scratch-deep' -> 'scratch_deep'."""
    return re.sub(r"[\s\-]+", "_", str(label).strip().lower())


def resolve_class_key(label: str, mapping_path: str | Path) -> str | None:
    """Return our class key for a model label, or None if it is out of scope.

    Out-of-scope labels are not an error - the raw output still records them,
    they are just left out of the report.
    """
    aliases = _load_aliases(mapping_path)
    normalised = _normalise(label)

    if normalised in aliases:
        return aliases[normalised]
    if normalised in SUPPORTED_CLASS_KEYS:
        return normalised

    logger.info(
        "Model label not in scope, skipping",
        extra={"extra_fields": {"model_label": label, "normalised": normalised}},
    )
    return None


def clear_cache() -> None:
    """Drop the cached mapping (used by tests and after editing the config file)."""
    clear_json_cache()
