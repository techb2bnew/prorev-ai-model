"""Run the real model over a local image file, bypassing the API and database.

Useful as a first check after changing MODEL_PATH or the inference settings:

    python scripts/verify_model.py path/to/car.jpg
    python scripts/verify_model.py path/to/car.jpg --conf 0.22   # sensitive mode
"""

import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PIL import Image  # noqa: E402

from app.config import get_config  # noqa: E402
from app.inference.base import DetectionOptions, PreparedImage  # noqa: E402
from app.inference.normalizer import normalise  # noqa: E402
from app.inference.preprocess import correct_orientation  # noqa: E402
from app.inference.severity import compute_damage_score  # noqa: E402
from app.inference.ultralytics_adapter import UltralyticsDetector  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the damage model on one local image.")
    parser.add_argument("image", help="Path to a .jpg/.png image")
    parser.add_argument("--preset", choices=["balanced", "sensitive", "strict"], default=None)
    parser.add_argument("--conf", type=float, default=None, help="Confidence threshold override")
    parser.add_argument("--iou", type=float, default=None, help="NMS IoU override")
    parser.add_argument("--imgsz", type=int, default=None, help="Inference resolution override")
    parser.add_argument("--clahe", action="store_true", help="Enable the CLAHE contrast pass")
    parser.add_argument("--augment", action="store_true", help="Enable test-time augmentation")
    args = parser.parse_args()

    image_path = Path(args.image)
    if not image_path.exists():
        print(f"No such file: {image_path}")
        return 1

    # The adapter takes a plain dict, so flatten the config class's settings.
    config_class = get_config()
    config = {key: getattr(config_class, key) for key in dir(config_class) if key.isupper()}

    if not config.get("MODEL_PATH"):
        print("MODEL_PATH is not set in .env")
        return 1

    # Build the options exactly as the inspection job does: start from the
    # preset, then apply any explicit overrides.
    overrides = {}
    if args.preset:
        overrides.update(config["DETECTION_PRESETS"][args.preset])
        overrides.pop("label", None)
        overrides.pop("description", None)
    if args.conf is not None:
        overrides["confidence"] = args.conf
    if args.iou is not None:
        overrides["iou"] = args.iou
    if args.imgsz is not None:
        overrides["input_size"] = args.imgsz
    if args.clahe:
        overrides["use_clahe"] = True
    if args.augment:
        overrides["augment"] = True

    options = DetectionOptions.from_config(config, overrides)

    detector = UltralyticsDetector(config)
    detector.ensure_loaded()

    print(f"Model      : {config['MODEL_PATH']}")
    print(f"Classes    : {detector.class_names}")
    print(f"conf/iou   : {options.confidence} / {options.iou}")
    print(f"imgsz      : {options.input_size}  augment={options.augment}  clahe={options.use_clahe}")
    print(f"floor      : {detector.detection_floor} (model runs here; filtering happens after)")
    print("-" * 60)

    pil_image = correct_orientation(Image.open(image_path)).convert("RGB")
    prepared = PreparedImage(
        image=pil_image,
        width=pil_image.width,
        height=pil_image.height,
        source_url=str(image_path),
        public_id=image_path.stem,
    )

    result = detector.predict(prepared, options)

    print(f"Image      : {prepared.width}x{prepared.height}")
    print(f"Quality    : {json.dumps(result.image_quality)}")
    print(f"Duration   : {result.duration_ms} ms")
    print(f"Raw boxes  : {len(result.detections)} (above the {detector.detection_floor} floor)")

    # Everything the model saw, so it is visible what the threshold removes.
    print("All findings above the floor:")
    for raw in sorted(result.detections, key=lambda d: d.confidence, reverse=True):
        keep = "REPORTED" if raw.confidence >= options.confidence else "below threshold"
        print(f"  {raw.confidence:.3f}  {raw.label:<14} {keep}")

    detections = normalise(
        raw_detections=result.detections,
        pixel_area=prepared.pixel_area,
        confidence_threshold=result.effective_confidence,
        class_mapping_path=config["CLASS_MAPPING_PATH"],
        severity_rules_path=config["SEVERITY_RULES_PATH"],
    )

    print("-" * 60)
    print(f"Reported   : {len(detections)}")
    for item in detections:
        print(
            f"  - {item.class_key:<14} conf={item.confidence:.3f} "
            f"severity={item.severity:<8} area={(item.area_ratio or 0) * 100:.2f}% bbox={item.bbox}"
        )

    total_area_percent = sum((d.area_ratio or 0) for d in detections) * 100
    score = compute_damage_score(
        config["SEVERITY_RULES_PATH"],
        [d.class_key for d in detections],
        total_area_percent,
    )
    print("-" * 60)
    print(f"Damage score: {score['score']}/100  band={score['band']}  critical={score['critical_count']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
