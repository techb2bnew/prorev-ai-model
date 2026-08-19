"""Cached reader for the JSON files in config/.

Both the class mapping and the severity rules are read on every detection, are
small, and change only between deploys - so they are cached by path. A missing
or malformed file logs and yields an empty dict rather than raising: detection
carries on with defaults instead of failing the whole inspection.
"""

import json
import logging
from functools import lru_cache
from pathlib import Path

logger = logging.getLogger(__name__)


@lru_cache(maxsize=8)
def _read(path: str) -> dict:
    try:
        with open(path, encoding="utf-8") as handle:
            return json.load(handle)
    except (OSError, json.JSONDecodeError) as exc:
        logger.error("Could not read JSON config at %s: %s", path, exc)
        return {}


def load_json_config(path: str | Path) -> dict:
    """The parsed contents of a config file, cached by path."""
    return _read(str(path))


def clear_cache() -> None:
    """Drop the cache (tests, or after editing a config file)."""
    _read.cache_clear()
