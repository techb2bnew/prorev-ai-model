"""Benchmarks the YOLO11m damage-detection model in isolation.

Goal: find out whether the ~20s/5-images latency seen from the frontend is the
*model* (CPU inference) or the *backend* (network download, DB writes, queue,
HTTP overhead). This script only touches the model and the same image
pre-processing app/inference/ultralytics_adapter.py does - no Flask, no DB, no
network - so whatever time shows up here is the floor the backend can't beat.

Usage:
    python generate_test_images.py     # once, to create test-model/images/*.jpg
    python benchmark.py                # run the full benchmark

Requires the same venv as the main app (ultralytics, torch, opencv, PIL).
"""

import json
import statistics
import time
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageOps

MODEL_PATH = Path(__file__).parent / "model" / "best.pt"
IMAGES_DIR = Path(__file__).parent / "images"
RESULTS_PATH = Path(__file__).parent / "benchmark_results.json"
REPORT_PATH = Path(__file__).parent / "benchmark_report.md"

# Mirrors app/config.py defaults - see docs/SCOPE_OF_WORK.md and
# app/inference/ultralytics_adapter.py for where these come from.
IOU_THRESHOLD = 0.45
INPUT_SIZE = 1024
DETECTION_FLOOR = 0.15
FALLBACK_MIN_CONF = 0.15

# Set for real in main() once torch is imported: 0 (first GPU) if available,
# else "cpu" - same rule app/inference/ultralytics_adapter.py uses, so this
# script reports whatever the server it's run on would actually use.
DEVICE = "cpu"


def now_ms() -> float:
    return time.perf_counter() * 1000


# --- Pre-processing steps, copied from app/inference/preprocess.py and
# app/inference/ultralytics_adapter.py so this script has no dependency on the
# Flask app (which needs DB/env config just to import). ---


def correct_orientation(image: Image.Image) -> Image.Image:
    return ImageOps.exif_transpose(image)


def enhance_damage_contrast(image_rgb: np.ndarray) -> np.ndarray:
    lab = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2LAB)
    l_channel, a_channel, b_channel = cv2.split(lab)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced_l = clahe.apply(l_channel)
    merged = cv2.merge((enhanced_l, a_channel, b_channel))
    return cv2.cvtColor(merged, cv2.COLOR_LAB2RGB)


def analyze_image_quality(image_rgb: np.ndarray) -> dict:
    gray = cv2.cvtColor(image_rgb, cv2.COLOR_RGB2GRAY)
    blur_score = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    brightness = float(np.mean(gray))
    return {"blur_score": round(blur_score, 2), "brightness": round(brightness, 2)}


def load_test_images() -> list[tuple[str, Image.Image]]:
    paths = sorted(IMAGES_DIR.glob("*.jpg"))
    if not paths:
        raise SystemExit(
            f"No test images found in {IMAGES_DIR}. Run generate_test_images.py first."
        )
    return [(p.name, Image.open(p)) for p in paths]


def prepare_one(image: Image.Image, use_clahe: bool) -> dict:
    """Same steps ultralytics_adapter.predict() + image_loader.load_image() do,
    minus the network download, timed individually."""
    timings = {}

    t0 = now_ms()
    image = correct_orientation(image)
    if image.mode != "RGB":
        image = image.convert("RGB")
    timings["orientation_convert_ms"] = round(now_ms() - t0, 2)

    t0 = now_ms()
    array = np.array(image)
    timings["to_array_ms"] = round(now_ms() - t0, 2)

    if use_clahe:
        t0 = now_ms()
        array = enhance_damage_contrast(array)
        timings["clahe_ms"] = round(now_ms() - t0, 2)

    t0 = now_ms()
    analyze_image_quality(array)
    timings["quality_analysis_ms"] = round(now_ms() - t0, 2)

    return {"array": array, "timings": timings}


def run_inference(model, image_np: np.ndarray, imgsz: int, conf: float, augment: bool):
    t0 = now_ms()
    results = model.predict(
        source=image_np,
        imgsz=imgsz,
        conf=conf,
        iou=IOU_THRESHOLD,
        device=DEVICE,
        augment=augment,
        verbose=False,
    )
    duration_ms = now_ms() - t0
    detections = len(results[0].boxes) if results and results[0].boxes is not None else 0
    return duration_ms, detections


def section(title: str) -> None:
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")


def build_summary_report(report: dict) -> str:
    """Turns the raw results dict into a short, human-readable Markdown report -
    the thing to open first, with benchmark_results.json as the backing detail."""
    env = report["environment"]
    lines = [
        "# Model speed benchmark report",
        "",
        f"- Device used: **{env['device_used']}** "
        f"({'GPU' if env['cuda_available'] else 'CPU-only'}, "
        f"{env['cpu_count']} CPUs, torch {env['torch_version']}, "
        f"{env['torch_threads']} torch threads)",
        f"- Model load time: {report['model_load_ms']:.0f} ms (once per worker process)",
        "",
        "## Per-image timing (production settings, imgsz=1024)",
        "",
        "| Image | Prep (ms) | Inference (ms) | TTA fallback (ms) | Detections | Total (ms) |",
        "|---|---|---|---|---|---|",
    ]

    for row in report["per_image_at_production_settings"]:
        prep_ms = sum(
            v for k, v in row.items()
            if k.endswith("_ms") and k not in ("inference_ms", "fallback_tta_ms", "total_ms")
        )
        fallback = f"{row['fallback_tta_ms']:.0f}" if row["fallback_tta_ms"] else "-"
        lines.append(
            f"| {row['image']} | {prep_ms:.0f} | {row['inference_ms']:.0f} | {fallback} "
            f"| {row['detections_found']} | {row['total_ms']:.0f} |"
        )

    total_s = report["sequential_total_seconds_no_network"]
    n_images = len(report["per_image_at_production_settings"])
    lines += [
        "",
        f"**Sequential total for {n_images} images, model only (no network/DB): "
        f"{total_s:.1f}s** ({report['avg_ms_per_image']:.0f} ms/image avg)",
        "",
    ]

    if "observed_seconds" in report:
        lines += [
            f"Observed frontend latency for the same number of images: "
            f"{report['observed_seconds']:.1f}s. The model accounts for "
            f"**~{report['model_share_of_observed_percent']:.0f}%** of that.",
            "",
        ]

    aug = report["augment_cost"]
    lines += [
        "## TTA fallback cost (augment=True, fires when nothing found at the 0.15 floor)",
        "",
        f"Single pass: {aug['single_pass_ms_avg']:.0f} ms avg  |  "
        f"TTA pass: {aug['tta_pass_ms_avg']:.0f} ms avg  |  "
        f"**{aug['multiplier']:.1f}x** the single pass, paid *in addition* to it.",
        "",
        "## Inference time vs. imgsz",
        "",
        "| imgsz | ms (avg) |",
        "|---|---|",
    ]
    for imgsz, ms in report["imgsz_comparison_ms"].items():
        lines.append(f"| {imgsz} | {ms:.0f} |")

    bvs = report["batched_vs_sequential_ms"]
    verdict = "faster" if bvs["batched_ms"] < bvs["sequential_ms"] else "slower or no better"
    lines += [
        "",
        "## Batched vs. sequential predict()",
        "",
        f"Sequential: {bvs['sequential_ms']:.0f} ms  |  Batched: {bvs['batched_ms']:.0f} ms  "
        f"-> batching was **{verdict}** on this hardware.",
        "",
        "## Bottom line",
        "",
        "If this total is close to what users see in the frontend, the model "
        "(inference at the configured imgsz, plus any TTA fallback passes) is the "
        "bottleneck, not the backend/network/DB path. Biggest levers, in order of "
        "effort: lower `MODEL_INPUT_SIZE`, run on GPU, or reduce how often the TTA "
        "fallback fires.",
    ]
    return "\n".join(lines)


def main() -> None:
    import argparse
    import os

    import torch
    from ultralytics import YOLO

    global DEVICE

    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--observed-seconds",
        type=float,
        default=None,
        help="What the frontend actually measured for this many images, so the "
        "report can say what share of it the model accounts for.",
    )
    args = parser.parse_args()

    DEVICE = 0 if torch.cuda.is_available() else "cpu"

    report: dict = {
        "environment": {
            "torch_threads": torch.get_num_threads(),
            "cpu_count": os.cpu_count(),
            "torch_version": torch.__version__,
            "cuda_available": torch.cuda.is_available(),
            "device_used": str(DEVICE),
        }
    }

    section("Loading model")
    t0 = now_ms()
    model = YOLO(str(MODEL_PATH))
    load_ms = now_ms() - t0
    print(f"Model load: {load_ms:.0f} ms (happens once per worker process, not per request)")
    report["model_load_ms"] = round(load_ms, 2)

    images = load_test_images()
    print(f"Loaded {len(images)} test images from {IMAGES_DIR}")

    section("Warm-up pass (first predict() call pays a one-off graph/JIT cost)")
    warmup_np = np.array(images[0][1].convert("RGB"))
    warm_ms, _ = run_inference(model, warmup_np, INPUT_SIZE, DETECTION_FLOOR, False)
    print(f"First predict() call: {warm_ms:.0f} ms (excluded from the stats below)")

    # ------------------------------------------------------------------
    # 1. Per-image breakdown at production settings (imgsz=1024, floor=0.15),
    #    including the automatic TTA fallback pass exactly as the real job
    #    would trigger it (when nothing is found at the floor).
    # ------------------------------------------------------------------
    section("Per-image breakdown at production settings (imgsz=1024)")
    per_image_results = []
    for name, image in images:
        prepared = prepare_one(image, use_clahe=False)
        inference_ms, detections = run_inference(
            model, prepared["array"], INPUT_SIZE, DETECTION_FLOOR, False
        )

        fallback_ms = None
        if detections == 0:
            fallback_ms, detections = run_inference(
                model, prepared["array"], INPUT_SIZE, FALLBACK_MIN_CONF, True
            )

        prep_total = sum(prepared["timings"].values())
        total_ms = prep_total + inference_ms + (fallback_ms or 0)

        row = {
            "image": name,
            **prepared["timings"],
            "inference_ms": round(inference_ms, 2),
            "fallback_tta_ms": round(fallback_ms, 2) if fallback_ms else None,
            "detections_found": detections,
            "total_ms": round(total_ms, 2),
        }
        per_image_results.append(row)
        fallback_note = f" + {fallback_ms:.0f}ms TTA fallback" if fallback_ms else ""
        print(
            f"  {name}: prep={prep_total:.0f}ms  inference={inference_ms:.0f}ms{fallback_note}"
            f"  -> total={total_ms:.0f}ms  ({detections} detections)"
        )

    report["per_image_at_production_settings"] = per_image_results
    total_sequential_ms = sum(r["total_ms"] for r in per_image_results)
    print(
        f"\nSequential total for {len(images)} images (no network, no DB): "
        f"{total_sequential_ms:.0f} ms  ({total_sequential_ms / 1000:.1f} s)"
    )
    report["sequential_total_ms_no_network"] = round(total_sequential_ms, 2)

    # ------------------------------------------------------------------
    # 2. Cost of the automatic TTA fallback pass in isolation (augment=True
    #    is documented as "roughly triples inference time").
    # ------------------------------------------------------------------
    section("Cost of augment=True (the TTA fallback pass) vs. a single pass")
    sample_np = per_image_results and np.array(images[0][1].convert("RGB"))
    single_times, augmented_times = [], []
    for _ in range(3):
        d, _ = run_inference(model, sample_np, INPUT_SIZE, DETECTION_FLOOR, False)
        single_times.append(d)
        d, _ = run_inference(model, sample_np, INPUT_SIZE, FALLBACK_MIN_CONF, True)
        augmented_times.append(d)
    single_avg = statistics.mean(single_times)
    augmented_avg = statistics.mean(augmented_times)
    print(f"Single pass (augment=False): {single_avg:.0f} ms avg")
    print(f"TTA pass    (augment=True):  {augmented_avg:.0f} ms avg  ({augmented_avg / single_avg:.1f}x)")
    print(
        "-> Every image where the model finds nothing at the 0.15 floor pays "
        "for BOTH passes (single + TTA), not just one."
    )
    report["augment_cost"] = {
        "single_pass_ms_avg": round(single_avg, 2),
        "tta_pass_ms_avg": round(augmented_avg, 2),
        "multiplier": round(augmented_avg / single_avg, 2),
    }

    # ------------------------------------------------------------------
    # 3. imgsz trade-off: 1024 is the documented/configured default for every
    #    detection preset. How much would dropping it cost in speed?
    # ------------------------------------------------------------------
    section("Inference time vs. imgsz (all presets currently use 1024)")
    imgsz_results = {}
    for imgsz in (1024, 768, 640, 512):
        times = []
        for _ in range(3):
            d, _ = run_inference(model, sample_np, imgsz, DETECTION_FLOOR, False)
            times.append(d)
        avg = statistics.mean(times)
        imgsz_results[imgsz] = round(avg, 2)
        print(f"  imgsz={imgsz}: {avg:.0f} ms avg (single pass, no TTA)")
    report["imgsz_comparison_ms"] = imgsz_results

    # ------------------------------------------------------------------
    # 4. Batched vs. sequential: does handing all 5 images to predict() at
    #    once beat looping and calling predict() once per image (what the
    #    real job currently does)?
    # ------------------------------------------------------------------
    section("Batched predict() vs. sequential predict() x N")
    arrays = [np.array(img.convert("RGB")) for _, img in images]

    t0 = now_ms()
    for arr in arrays:
        model.predict(source=arr, imgsz=INPUT_SIZE, conf=DETECTION_FLOOR, iou=IOU_THRESHOLD, device="cpu", verbose=False)
    sequential_ms = now_ms() - t0

    t0 = now_ms()
    model.predict(source=arrays, imgsz=INPUT_SIZE, conf=DETECTION_FLOOR, iou=IOU_THRESHOLD, device="cpu", verbose=False)
    batched_ms = now_ms() - t0

    print(f"Sequential ({len(arrays)} calls): {sequential_ms:.0f} ms")
    print(f"Batched (1 call, {len(arrays)} images): {batched_ms:.0f} ms")
    if batched_ms < sequential_ms:
        print(f"-> Batching would save ~{sequential_ms - batched_ms:.0f} ms ({(1 - batched_ms / sequential_ms) * 100:.0f}%) "
              "on CPU inference alone for a 5-image inspection.")
    else:
        print("-> Batching did not help on this CPU; sequential is as fast or faster.")
    report["batched_vs_sequential_ms"] = {
        "sequential_ms": round(sequential_ms, 2),
        "batched_ms": round(batched_ms, 2),
    }

    # ------------------------------------------------------------------
    section("Summary")
    avg_per_image = total_sequential_ms / len(images)
    print(f"Model + pre-processing only, no network/DB: {avg_per_image:.0f} ms/image avg, "
          f"{total_sequential_ms / 1000:.1f}s for {len(images)} images.")

    observed_seconds = args.observed_seconds
    if observed_seconds:
        share = (total_sequential_ms / 1000) / observed_seconds * 100
        print(
            f"Observed frontend latency: {observed_seconds:.1f}s for {len(images)} images. "
            f"The model accounts for ~{share:.0f}% of that."
        )
        report["observed_seconds"] = observed_seconds
        report["model_share_of_observed_percent"] = round(share, 1)
    else:
        print(
            "Pass --observed-seconds <N> (what the frontend actually measured) to see "
            "what share of that the model accounts for."
        )
    report["sequential_total_seconds_no_network"] = round(total_sequential_ms / 1000, 2)
    report["avg_ms_per_image"] = round(avg_per_image, 2)

    RESULTS_PATH.write_text(json.dumps(report, indent=2))
    print(f"\nFull results (JSON) written to {RESULTS_PATH}")

    REPORT_PATH.write_text(build_summary_report(report))
    print(f"Summary report (Markdown) written to {REPORT_PATH}")


if __name__ == "__main__":
    main()
