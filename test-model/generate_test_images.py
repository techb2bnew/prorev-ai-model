"""Creates synthetic car-photo-sized images for the benchmark.

We don't have real inspection photos in this repo, and inference speed is
driven by resolution, not content, so a synthetic image at the same size a
downloaded Cloudinary photo would be (~1024px on the long side, matching
MODEL_INPUT_SIZE) is a valid stand-in for timing purposes.

Run once: `python generate_test_images.py`. Re-run with --count/--sizes to
change how many images or what resolutions are generated.
"""

import argparse
import random
from pathlib import Path

from PIL import Image, ImageDraw

OUT_DIR = Path(__file__).parent / "images"

# width x height. 1024-wide matches the target_width the real pipeline asks
# Cloudinary to downscale to before the model ever sees the image.
DEFAULT_SIZES = [
    (1024, 768),
    (1024, 683),
    (1024, 1024),
    (900, 1200),
    (1024, 768),
]


def make_image(width: int, height: int, seed: int) -> Image.Image:
    rng = random.Random(seed)
    image = Image.new("RGB", (width, height), color=(rng.randint(60, 200),) * 3)
    draw = ImageDraw.Draw(image)

    # A few shapes so the image isn't a flat colour (flat colours can make
    # some CV ops artificially fast/slow) - not meant to resemble real damage.
    for _ in range(40):
        x1 = rng.randint(0, width)
        y1 = rng.randint(0, height)
        x2 = min(width, x1 + rng.randint(10, 200))
        y2 = min(height, y1 + rng.randint(10, 200))
        color = (rng.randint(0, 255), rng.randint(0, 255), rng.randint(0, 255))
        draw.ellipse([x1, y1, x2, y2], outline=color, width=rng.randint(1, 4))

    return image


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", type=int, default=len(DEFAULT_SIZES))
    args = parser.parse_args()

    OUT_DIR.mkdir(exist_ok=True)
    sizes = DEFAULT_SIZES[: args.count] or DEFAULT_SIZES
    while len(sizes) < args.count:
        sizes.append(DEFAULT_SIZES[len(sizes) % len(DEFAULT_SIZES)])

    for index, (width, height) in enumerate(sizes, start=1):
        image = make_image(width, height, seed=index)
        path = OUT_DIR / f"test_{index}.jpg"
        image.save(path, format="JPEG", quality=85)
        print(f"wrote {path} ({width}x{height})")


if __name__ == "__main__":
    main()
