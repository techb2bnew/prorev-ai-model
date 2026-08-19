"""Reproduce exactly what the React UI does, through the Vite dev proxy.

Same sequence as the browser: signature -> direct Cloudinary upload -> create
inspection -> poll -> read report. Its real purpose is checking that the
bounding boxes line up with the image dimensions the report advertises, which is
what the overlay in the UI depends on and what a browser test would show.

    python scripts/verify_frontend_flow.py path/to/car.jpg

NOTE: this uploads the file to the Cloudinary account in .env, exactly as the
frontend would.
"""

import argparse
import sys
import time
from pathlib import Path

import requests

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

passed = 0
failed = 0


def check(label, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {label}" + (f" - {detail}" if detail else ""))
    else:
        failed += 1
        print(f"  [FAIL] {label}" + (f" - {detail}" if detail else ""))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("image", nargs="?", default="docs/car/car/frontend/src/assets/hero.png")
    # Through the Vite proxy by default, which is the path the browser takes.
    parser.add_argument("--base", default="http://localhost:5173/api/v1")
    args = parser.parse_args()

    path = Path(args.image)
    if not path.exists():
        print(f"No such file: {path}")
        return 1

    base = args.base.rstrip("/")
    session = requests.Session()
    unique = str(int(time.time()))

    print(f"\nUI flow against {base}")
    print(f"Uploading: {path.name}\n")

    print("=== 1. Sign in (as the UI's login form does) ===")
    register = session.post(
        f"{base}/auth/register",
        json={"email": f"ui-{unique}@example.com", "password": "Passw0rd123", "full_name": "UI Flow"},
        timeout=30,
    )
    check("registered", register.status_code == 201, str(register.status_code))
    headers = {"Authorization": f"Bearer {register.json()['access_token']}"}

    print("\n=== 2. Ask the backend for a Cloudinary signature ===")
    signature = session.post(f"{base}/uploads/signature", json={}, headers=headers, timeout=30).json()
    check("signature received", len(signature.get("signature", "")) == 40)
    check("api_secret not exposed", "api_secret" not in signature)
    print(f"    folder: {signature['folder']}")

    print("\n=== 3. Upload straight to Cloudinary (browser does this, not the backend) ===")
    with path.open("rb") as handle:
        upload = requests.post(
            signature["upload_url"],
            data={
                "api_key": signature["api_key"],
                "timestamp": signature["timestamp"],
                "signature": signature["signature"],
                "folder": signature["folder"],
            },
            files={"file": (path.name, handle)},
            timeout=120,
        )

    check("cloudinary accepted the signed upload", upload.status_code == 200,
          f"HTTP {upload.status_code}")
    if upload.status_code != 200:
        print(f"    {upload.text[:400]}")
        return 1

    asset = upload.json()
    print(f"    public_id : {asset['public_id']}")
    print(f"    dimensions: {asset['width']}x{asset['height']}")

    print("\n=== 4. Create the inspection with the returned references ===")
    created = session.post(
        f"{base}/inspections",
        json={
            "customer_name": f"UI Test {unique[-6:]}",
            "vehicle_type": "suv",
            # URLs only, keyed by view. The backend derives the public id from
            # the URL, so nothing else about the upload needs sending.
            "images": {"front": asset["secure_url"]},
        },
        headers={**headers, "Idempotency-Key": f"ui-{unique}"},
        timeout=60,
    )
    check("returns 202", created.status_code == 202, str(created.status_code))
    inspection_id = created.json()["id"]
    print(f"    {inspection_id}")

    print("\n=== 5. Poll until the model finishes ===")
    started = time.time()
    status = {}
    while time.time() - started < 240:
        status = session.get(
            f"{base}/inspections/{inspection_id}/status", headers=headers, timeout=30
        ).json()
        print(f"    t+{int(time.time() - started):>3}s  {status['status']:<12} "
              f"detections={status['total_detections']}")
        if status["is_finished"]:
            break
        time.sleep(2)
    check("finished", status.get("is_finished") is True)

    print("\n=== 6. Report, and the geometry the overlay relies on ===")
    report = session.get(f"{base}/inspections/{inspection_id}", headers=headers, timeout=60).json()["report"]
    image = report["images"][0]
    dimensions = image["dimensions"]

    # The request carries only a URL, so the size the model analysed is the only
    # size the backend knows - and boxes are stored in that space. What matters
    # is that `dimensions` describes the same space as the boxes, and that it is
    # never larger than the original.
    check("report dimensions never exceed the uploaded original",
          dimensions["width"] <= asset["width"] and dimensions["height"] <= asset["height"],
          f"{dimensions['width']}x{dimensions['height']} vs {asset['width']}x{asset['height']}")
    check("aspect ratio preserved by the downscale",
          abs(dimensions["width"] / dimensions["height"] - asset["width"] / asset["height"]) < 0.02,
          f"{dimensions['width']}x{dimensions['height']}")

    print(f"    {len(image['detections'])} detection(s):")
    all_inside = True
    for found in image["detections"]:
        box = found["bbox"]
        inside = (
            box["x"] >= 0
            and box["y"] >= 0
            and box["x"] + box["width"] <= dimensions["width"] + 1
            and box["y"] + box["height"] <= dimensions["height"] + 1
        )
        all_inside = all_inside and inside
        print(f"      - {found['label']:<14} conf={found['confidence']:.3f} "
              f"severity={found['severity']:<9} bbox=({box['x']},{box['y']},"
              f"{box['width']},{box['height']}) inside={inside}")

    if image["detections"]:
        check("every box sits inside the reported image bounds", all_inside,
              "this is what keeps the UI overlay aligned")
        # A box occupying a plausible share of the frame indicates the boxes and
        # the reported dimensions agree; boxes squeezed into the top-left corner
        # are the failure mode a scale mismatch would produce.
        widest = max(f["bbox"]["width"] / dimensions["width"] for f in image["detections"])
        check("boxes span a plausible share of the reported frame",
              widest > 0.05, f"widest box spans {widest * 100:.1f}% of the frame")
    else:
        print("    (no detections on this image - geometry checks skipped)")

    print(f"\n    damage_score={report['damage_score']} severity={report['overall_severity']} "
          f"area={report['total_area_percent']}%")

    print("\n=== 7. History shows it ===")
    history = session.get(f"{base}/inspections", headers=headers, timeout=30).json()
    check("appears in history", history["total"] == 1)
    check("thumbnail url present for the list view",
          bool(history["items"][0].get("thumbnail_url")))

    print("\n" + "=" * 60)
    print(f"  {passed} passed, {failed} failed")
    print(f"  Cloudinary asset left behind: {asset['public_id']}")
    print("=" * 60)
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except requests.ConnectionError as exc:
        print(f"\nCould not reach {exc.request.url if exc.request else 'the server'}")
        print("Both servers must be running: waitress on 5055 and npm run dev on 5173.")
        sys.exit(2)
