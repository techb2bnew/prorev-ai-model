"""Seed data for the damage_types lookup table.

The six classes come from the supplied YOLO11m model (verified against best.pt)
and the colour codes from DOCUMENTATION.md section 2. Re-running this is safe:
existing rows are updated, not duplicated.
"""

import logging

import sqlalchemy as sa

from app.extensions import db
from app.inference.severity import critical_class_keys
from app.models import DamageType

logger = logging.getLogger(__name__)

# class_key, model label, model index, display name, hex colour, description
DAMAGE_TYPES: list[dict] = [
    {
        "class_key": "dent",
        "model_label": "dent",
        "model_class_index": 0,
        "display_name": "Dent",
        "color_hex": "#38bdf8",
        "description": "Indentations, dings and sheet metal compressions.",
        "sort_order": 1,
    },
    {
        "class_key": "scratch",
        "model_label": "scratch",
        "model_class_index": 1,
        "display_name": "Scratch",
        "color_hex": "#f59e0b",
        "description": "Paint abrasions, scrape lines and clear-coat scuffs.",
        "sort_order": 2,
    },
    {
        "class_key": "crack",
        "model_label": "crack",
        "model_class_index": 2,
        "display_name": "Crack",
        "color_hex": "#f43f5e",
        "description": "Windshield fissures and bumper or fender cracks.",
        "sort_order": 3,
    },
    {
        "class_key": "glass_shatter",
        "model_label": "glass shatter",
        "model_class_index": 3,
        "display_name": "Glass Shatter",
        "color_hex": "#c084fc",
        "description": "Webbed breaks and shattered window panels.",
        "sort_order": 4,
    },
    {
        "class_key": "lamp_broken",
        "model_label": "lamp broken",
        "model_class_index": 4,
        "display_name": "Lamp Broken",
        "color_hex": "#fde047",
        "description": "Broken headlight, taillight or turn signal lenses.",
        "sort_order": 5,
    },
    {
        "class_key": "tire_flat",
        "model_label": "tire flat",
        "model_class_index": 5,
        "display_name": "Tire Flat",
        "color_hex": "#34d399",
        "description": "Deflated tyre, punctured sidewall or exposed rim.",
        "sort_order": 6,
    },
]


def seed_damage_types(app=None) -> int:
    """Insert or update the six damage type rows. Returns how many were written."""
    config = app.config if app else db.get_app().config
    critical = critical_class_keys(config["SEVERITY_RULES_PATH"])

    written = 0
    for entry in DAMAGE_TYPES:
        existing = db.session.scalar(
            sa.select(DamageType).where(DamageType.class_key == entry["class_key"])
        )
        target = existing or DamageType(class_key=entry["class_key"])

        target.model_label = entry["model_label"]
        target.model_class_index = entry["model_class_index"]
        target.display_name = entry["display_name"]
        target.color_hex = entry["color_hex"]
        target.description = entry["description"]
        target.sort_order = entry["sort_order"]
        target.is_critical = entry["class_key"] in critical
        target.is_active = True

        if existing is None:
            db.session.add(target)
        written += 1

    db.session.commit()
    logger.info("Seeded %s damage types", written)
    return written
