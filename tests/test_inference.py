"""Unit tests for the model-facing logic: class mapping, NMS, severity, damage score."""

import pytest

from app.inference.base import RawDetection
from app.inference.class_mapping import SUPPORTED_CLASS_KEYS, clear_cache, resolve_class_key
from app.inference.normalizer import _polygon_area, normalise
from app.inference.postprocess import apply_class_aware_nms
from app.inference.severity import compute_damage_score, derive_severity, map_model_severity
from app.models.enums import Severity
from app.utils.cloudinary_url import (
    downscaled_url,
    public_id_from_url,
    thumbnail_url,
)

CLASS_MAPPING = "config/class_mapping.json"
SEVERITY_RULES = "config/severity_rules.json"


@pytest.fixture(autouse=True)
def _clear_config_cache():
    clear_cache()
    yield
    clear_cache()


class TestClassMapping:
    def test_maps_all_six_model_labels(self):
        """Every label the real model emits must resolve - verified from best.pt."""
        model_labels = ["dent", "scratch", "crack", "glass shatter", "lamp broken", "tire flat"]
        resolved = [resolve_class_key(label, CLASS_MAPPING) for label in model_labels]

        assert resolved == ["dent", "scratch", "crack", "glass_shatter", "lamp_broken", "tire_flat"]
        assert set(resolved) == set(SUPPORTED_CLASS_KEYS)

    def test_folds_spelling_variants(self):
        assert resolve_class_key("Glass Shatter", CLASS_MAPPING) == "glass_shatter"
        assert resolve_class_key("glass-shatter", CLASS_MAPPING) == "glass_shatter"
        assert resolve_class_key("  TIRE FLAT  ", CLASS_MAPPING) == "tire_flat"

    def test_accepts_british_tyre_spelling(self):
        assert resolve_class_key("flat_tyre", CLASS_MAPPING) == "tire_flat"

    def test_unknown_label_returns_none(self):
        assert resolve_class_key("spontaneous_combustion", CLASS_MAPPING) is None


class TestClassAwareNms:
    def test_keeps_overlapping_boxes_of_different_classes(self):
        """A dent and a scratch in the same spot are two findings, not one."""
        detections = [
            RawDetection(label="dent", confidence=0.9, bbox=(10, 10, 100, 100)),
            RawDetection(label="scratch", confidence=0.8, bbox=(12, 12, 100, 100)),
        ]
        kept = apply_class_aware_nms(detections, iou_threshold=0.45)
        assert {d.label for d in kept} == {"dent", "scratch"}

    def test_suppresses_duplicates_within_a_class(self):
        detections = [
            RawDetection(label="dent", confidence=0.95, bbox=(10, 10, 100, 100)),
            RawDetection(label="dent", confidence=0.60, bbox=(12, 12, 100, 100)),
        ]
        kept = apply_class_aware_nms(detections, iou_threshold=0.45)
        assert len(kept) == 1
        assert kept[0].confidence == 0.95

    def test_sorts_by_confidence_descending(self):
        detections = [
            RawDetection(label="dent", confidence=0.5, bbox=(0, 0, 50, 50)),
            RawDetection(label="scratch", confidence=0.9, bbox=(500, 500, 50, 50)),
            RawDetection(label="crack", confidence=0.7, bbox=(900, 900, 50, 50)),
        ]
        kept = apply_class_aware_nms(detections)
        assert [d.confidence for d in kept] == [0.9, 0.7, 0.5]

    def test_empty_input(self):
        assert apply_class_aware_nms([]) == []


class TestSeverity:
    def test_model_severity_wins_when_provided(self):
        """If a future model reports severity, we must not override it with our rules."""
        result = derive_severity(
            "scratch", SEVERITY_RULES, area_ratio=0.0001, confidence=0.4, model_severity="high"
        )
        assert result == Severity.SEVERE

    def test_maps_model_wording(self):
        assert map_model_severity("HIGH") == Severity.SEVERE
        assert map_model_severity("medium") == Severity.MODERATE
        assert map_model_severity("low") == Severity.MINOR
        assert map_model_severity("nonsense") is None
        assert map_model_severity(None) is None

    def test_large_scratch_is_severe(self):
        assert derive_severity("scratch", SEVERITY_RULES, area_ratio=0.10, confidence=0.9) == (
            Severity.SEVERE
        )

    def test_small_scratch_is_minor(self):
        assert derive_severity("scratch", SEVERITY_RULES, area_ratio=0.001, confidence=0.9) == (
            Severity.MINOR
        )

    def test_lamp_broken_uses_confidence_not_area(self):
        """A broken lamp is a small object; area would always read as minor."""
        assert derive_severity("lamp_broken", SEVERITY_RULES, area_ratio=0.001, confidence=0.95) == (
            Severity.SEVERE
        )

    def test_unknown_class_falls_back_to_default_rules(self):
        assert derive_severity("unknown_thing", SEVERITY_RULES, area_ratio=0.20, confidence=0.9) == (
            Severity.SEVERE
        )


class TestDamageScore:
    """The 0-100 formula from DOCUMENTATION.md section 4."""

    def test_no_damage_scores_zero(self):
        result = compute_damage_score(SEVERITY_RULES, [], 0.0)
        assert result["score"] == 0
        assert result["band"] == Severity.NONE

    def test_single_non_critical_damage(self):
        # 0 critical + 1 damage*8 + min(40, 1.0*4) = 12
        result = compute_damage_score(SEVERITY_RULES, ["scratch"], 1.0)
        assert result["score"] == 12
        assert result["band"] == Severity.MINOR
        assert result["critical_count"] == 0

    def test_critical_class_adds_25(self):
        # 1 critical*25 + 1 damage*8 + min(40, 0*4) = 33
        result = compute_damage_score(SEVERITY_RULES, ["tire_flat"], 0.0)
        assert result["score"] == 33
        assert result["critical_count"] == 1
        assert result["band"] == Severity.MODERATE

    def test_area_term_is_capped_at_40(self):
        # 1 damage*8 + min(40, 90*4=360) = 48
        result = compute_damage_score(SEVERITY_RULES, ["dent"], 90.0)
        assert result["score"] == 48

    def test_score_is_capped_at_100(self):
        keys = ["glass_shatter", "lamp_broken", "tire_flat", "dent", "scratch"] * 3
        result = compute_damage_score(SEVERITY_RULES, keys, 50.0)
        assert result["score"] == 100
        assert result["band"] == Severity.SEVERE

    def test_repeated_class_counts_each_time(self):
        single = compute_damage_score(SEVERITY_RULES, ["dent"], 0.0)["score"]
        triple = compute_damage_score(SEVERITY_RULES, ["dent", "dent", "dent"], 0.0)["score"]
        assert triple == single * 3


class TestNormaliser:
    def test_drops_low_confidence_detections(self):
        detections = [
            RawDetection(label="dent", confidence=0.10, bbox=(0, 0, 50, 50)),
            RawDetection(label="dent", confidence=0.90, bbox=(0, 0, 50, 50)),
        ]
        result = normalise(detections, 1_000_000, 0.35, CLASS_MAPPING, SEVERITY_RULES)
        assert len(result) == 1
        assert result[0].confidence == 0.9

    def test_drops_out_of_scope_labels(self):
        detections = [
            RawDetection(label="mirror_damage", confidence=0.9, bbox=(0, 0, 50, 50)),
            RawDetection(label="scratch", confidence=0.9, bbox=(0, 0, 50, 50)),
        ]
        result = normalise(detections, 1_000_000, 0.35, CLASS_MAPPING, SEVERITY_RULES)
        assert [d.class_key for d in result] == ["scratch"]

    def test_computes_area_ratio_from_bbox(self):
        detections = [RawDetection(label="dent", confidence=0.9, bbox=(0, 0, 100, 100))]
        result = normalise(detections, 1_000_000, 0.35, CLASS_MAPPING, SEVERITY_RULES)
        assert result[0].area_ratio == pytest.approx(0.01)

    def test_area_ratio_is_none_without_a_box(self):
        """A classification-only model gives no geometry, and that must not crash."""
        detections = [RawDetection(label="dent", confidence=0.9, bbox=None)]
        result = normalise(detections, 1_000_000, 0.35, CLASS_MAPPING, SEVERITY_RULES)
        assert result[0].area_ratio is None

    def test_polygon_area_uses_shoelace(self):
        square = [[0, 0], [10, 0], [10, 10], [0, 10]]
        assert _polygon_area(square) == pytest.approx(100.0)

    def test_degenerate_polygon_is_zero_area(self):
        assert _polygon_area([[0, 0], [1, 1]]) == 0.0


class TestCloudinaryUrls:
    """The request now carries URLs only, so the public id is derived from them."""

    @pytest.mark.parametrize(
        "url, expected",
        [
            # The shape Cloudinary returns from an upload.
            (
                "https://res.cloudinary.com/dfcj6nmpe/image/upload/v1787118301/"
                "dent-inspections/c1ee4j9ff0avmp8xzorz.jpg",
                "dent-inspections/c1ee4j9ff0avmp8xzorz",
            ),
            # Nested folders: this project uploads into a per-user sub-folder.
            (
                "https://res.cloudinary.com/utlka8ks/image/upload/v1787037277/"
                "dent-inspections/1159bb7c-34c8/qzpsklymqo3cvzhbjf96.jpg",
                "dent-inspections/1159bb7c-34c8/qzpsklymqo3cvzhbjf96",
            ),
            # No version segment.
            ("https://res.cloudinary.com/demo/image/upload/car.jpg", "car"),
            # A transformation in the path must not become part of the id.
            (
                "https://res.cloudinary.com/demo/image/upload/c_fill,w_320/v123/folder/car.png",
                "folder/car",
            ),
            # Query strings are not part of the id.
            ("https://res.cloudinary.com/demo/image/upload/v1/a/b.jpg?x=1", "a/b"),
            # Not a Cloudinary delivery URL.
            ("https://example.com/photos/car.jpg", None),
            ("", None),
        ],
    )
    def test_public_id_is_read_from_the_url(self, url, expected):
        assert public_id_from_url(url) == expected

    def test_thumbnail_and_downscale_insert_transformations(self):
        url = "https://res.cloudinary.com/demo/image/upload/v1/a/b.jpg"
        assert thumbnail_url(url, 320) == (
            "https://res.cloudinary.com/demo/image/upload/c_fill,w_320,h_320,q_auto/v1/a/b.jpg"
        )
        assert downscaled_url(url, 1024) == (
            "https://res.cloudinary.com/demo/image/upload/c_limit,w_1024,q_auto/v1/a/b.jpg"
        )

    def test_downscale_falls_back_to_the_original_url(self):
        """Fetching the original is still correct, so a non-Cloudinary URL passes through."""
        assert downscaled_url("https://example.com/a.jpg", 1024) == "https://example.com/a.jpg"
