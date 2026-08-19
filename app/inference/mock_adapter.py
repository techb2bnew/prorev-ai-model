"""Stand-in model used by the test suite and for running without the weights file.

Emits the same six labels as the real YOLO11m model, so anything downstream
(class mapping, severity, damage score, report shape) is exercised identically.
Output is deterministic per image - seeded from the Cloudinary public_id - so
tests and demos give the same answer on every run.
"""

import random
import time

from app.inference.base import (
    DamageDetector,
    DetectionOptions,
    InferenceResult,
    PreparedImage,
    RawDetection,
)
from app.inference.raw_output import build_raw_output

# The real model's labels, verified against best.pt.
_CLASS_NAMES = {
    0: "dent",
    1: "scratch",
    2: "crack",
    3: "glass shatter",
    4: "lamp broken",
    5: "tire flat",
}


class MockDetector(DamageDetector):
    backend_name = "mock"

    def load(self) -> None:
        self._loaded = True

    @property
    def class_names(self) -> dict[int, str]:
        return dict(_CLASS_NAMES)

    def predict(
        self, image: PreparedImage, options: DetectionOptions | None = None
    ) -> InferenceResult:
        options = options or DetectionOptions.from_config(self.config)
        started = time.perf_counter()
        rng = random.Random(f"{image.public_id}:{image.width}x{image.height}")

        detections: list[RawDetection] = []

        # 0-4 findings; an occasional clean image is realistic and must be handled.
        for _ in range(rng.randint(0, 4)):
            class_id = rng.randint(0, 5)
            box_w = rng.randint(max(int(image.width * 0.04), 3), max(int(image.width * 0.25), 4))
            box_h = rng.randint(max(int(image.height * 0.04), 3), max(int(image.height * 0.25), 4))
            x = rng.randint(0, max(image.width - box_w, 1))
            y = rng.randint(0, max(image.height - box_h, 1))

            detections.append(
                RawDetection(
                    label=_CLASS_NAMES[class_id],
                    confidence=round(rng.uniform(0.40, 0.98), 4),
                    bbox=(x, y, box_w, box_h),
                    extra={"class_id": class_id},
                )
            )

        duration_ms = int((time.perf_counter() - started) * 1000)
        quality = {
            "blur_score": 150.0,
            "brightness": 128.0,
            "is_blurry": False,
            "warnings": [],
        }

        raw_output = build_raw_output(
            backend=self.backend_name,
            detections=detections,
            width=image.width,
            height=image.height,
            class_names=_CLASS_NAMES,
            image_quality=quality,
            note="synthetic output - not a real prediction",
        )

        return InferenceResult(
            detections=detections,
            raw_output=raw_output,
            duration_ms=duration_ms,
            image_quality=quality,
            effective_confidence=options.confidence,
        )
