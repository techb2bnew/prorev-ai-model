"""Severity derivation.

If the model reports severity itself, we map it straight through. If it does
not, we derive severity from the rules in config/severity_rules.json - the
thresholds are configuration, not code, so they can be tuned without a release.
"""

import logging
from pathlib import Path

from app.models.enums import Severity
from app.utils.json_config import clear_cache as clear_json_cache
from app.utils.json_config import load_json_config

logger = logging.getLogger(__name__)

_LEVELS = (Severity.SEVERE, Severity.MODERATE, Severity.MINOR)

# Wording a model might use for each of our three levels.
_MODEL_SEVERITY_ALIASES = {
    "severe": Severity.SEVERE,
    "high": Severity.SEVERE,
    "major": Severity.SEVERE,
    "critical": Severity.SEVERE,
    "3": Severity.SEVERE,
    "moderate": Severity.MODERATE,
    "medium": Severity.MODERATE,
    "mid": Severity.MODERATE,
    "2": Severity.MODERATE,
    "minor": Severity.MINOR,
    "low": Severity.MINOR,
    "small": Severity.MINOR,
    "1": Severity.MINOR,
}


def _score_rules(path: str | Path) -> dict:
    """The ``damage_score`` section, read by three of the functions below."""
    return load_json_config(path).get("damage_score", {})


def map_model_severity(value: str | None) -> str | None:
    """Translate the model's own severity wording onto minor/moderate/severe."""
    if value is None:
        return None
    return _MODEL_SEVERITY_ALIASES.get(str(value).strip().lower())


def _matches(conditions: dict, area_ratio: float, confidence: float, class_count: int) -> bool:
    """A rule matches only when every condition in it is satisfied."""
    if "min_area_ratio" in conditions and area_ratio < float(conditions["min_area_ratio"]):
        return False
    if "min_confidence" in conditions and confidence < float(conditions["min_confidence"]):
        return False
    if "min_count" in conditions and class_count < int(conditions["min_count"]):
        return False
    return True


def derive_severity(
    class_key: str,
    rules_path: str | Path,
    area_ratio: float | None = None,
    confidence: float = 0.0,
    class_count: int = 1,
    model_severity: str | None = None,
) -> str:
    """Work out the severity of a single detection.

    ``class_count`` is how many detections of this same class were found in the
    image - what makes a cluster of hail dents 'severe' rather than 'minor'.
    """
    from_model = map_model_severity(model_severity)
    if from_model:
        return from_model

    rules = load_json_config(rules_path)
    class_rules = rules.get("classes", {}).get(class_key) or rules.get("default", {})
    fallback = rules.get("fallback", Severity.MINOR)

    ratio = float(area_ratio or 0.0)

    for level in _LEVELS:
        conditions = class_rules.get(level)
        if conditions and _matches(conditions, ratio, confidence, class_count):
            return level

    return fallback


def compute_damage_score(
    rules_path: str | Path,
    class_keys: list[str],
    total_area_percent: float,
) -> dict:
    """The aggregate 0-100 damage score from DOCUMENTATION.md section 4.

        score = min(100, critical*25 + count*8 + min(40, total_area% * 4))

    ``class_keys`` is one entry per detection across the whole inspection, so a
    class appearing three times contributes three times.

    Note the score saturates: past roughly a dozen findings everything reads
    100, so it ranks light damage against heavy damage but does not separate
    heavy from catastrophic.
    """
    rules = _score_rules(rules_path)

    critical_classes = set(rules.get("critical_classes", []))
    critical_weight = float(rules.get("critical_weight", 25))
    damage_weight = float(rules.get("damage_weight", 8))
    area_multiplier = float(rules.get("area_multiplier", 4))
    area_cap = float(rules.get("area_cap", 40))
    max_score = float(rules.get("max_score", 100))

    critical_count = sum(1 for key in class_keys if key in critical_classes)
    damage_count = len(class_keys)

    area_term = min(area_cap, float(total_area_percent) * area_multiplier)
    raw_score = (critical_count * critical_weight) + (damage_count * damage_weight) + area_term
    score = int(min(max_score, raw_score))

    return {
        "score": score,
        "band": score_band(rules_path, score),
        "critical_count": critical_count,
        "damage_count": damage_count,
        "total_area_percent": round(float(total_area_percent), 2),
    }


def score_band(rules_path: str | Path, score: int) -> str:
    """Map a 0-100 score onto none/minor/moderate/severe."""
    rules = _score_rules(rules_path)
    for band in rules.get("bands", []):
        if int(band.get("min_score", 0)) <= score <= int(band.get("max_score", 100)):
            return str(band.get("label", Severity.MINOR))
    return Severity.NONE if score <= 0 else Severity.MINOR


def critical_class_keys(rules_path: str | Path) -> set[str]:
    return set(_score_rules(rules_path).get("critical_classes", []))


def clear_cache() -> None:
    clear_json_cache()
