"""End-to-end smoke test against a running server.

Exercises the real flow: register -> signature -> create inspection -> poll ->
report, plus ownership isolation and the audit trail. Unlike the pytest suite
this hits a live API, the real PostgreSQL database and (unless MODEL_BACKEND is
mock) the real YOLO model.

    python scripts/smoke_test.py
    python scripts/smoke_test.py --base http://127.0.0.1:5000/api/v1
"""

import argparse
import sys
import time
import uuid

import requests

# Public read-only images on Cloudinary's demo account, so the test needs no
# upload into anyone's real account.
DEMO = "https://res.cloudinary.com/demo/image/upload"

#: One demo asset per view. Each URL must be distinct - the API rejects the same
#: photo being submitted as two different sides. All five are at least 320px on
#: the short side, which the loader now enforces after decoding; demo/car.jpg is
#: 674x308 and would legitimately be rejected.
IMAGES = {
    "front": f"{DEMO}/sample.jpg",
    "back": f"{DEMO}/sheep.jpg",
    "left": f"{DEMO}/bike.jpg",
    "right": f"{DEMO}/balloons.jpg",
    "top": f"{DEMO}/dog.jpg",
}

passed = 0
failed = 0


def check(label: str, condition: bool, detail: str = "") -> None:
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {label}" + (f" - {detail}" if detail else ""))
    else:
        failed += 1
        print(f"  [FAIL] {label}" + (f" - {detail}" if detail else ""))


def create_body(images: dict, **extra) -> dict:
    return {"customer_name": "test", "vehicle_type": "suv", "images": images, **extra}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base", default="http://127.0.0.1:5055/api/v1")
    parser.add_argument("--timeout", type=int, default=180, help="Seconds to wait for inference")
    args = parser.parse_args()
    base = args.base.rstrip("/")

    unique = uuid.uuid4().hex[:8]
    session = requests.Session()

    print("\n=== 1. Health and readiness ===")
    health = session.get(f"{base}/health", timeout=30).json()
    check("liveness", health.get("status") == "ok")

    ready = session.get(f"{base}/health/ready", timeout=120).json()
    check("database ready", ready["checks"]["database"]["ok"] is True)
    check("model ready", ready["checks"]["model"]["ok"] is True,
          f"backend={ready['checks']['model'].get('backend')}")
    check("cloudinary configured", ready["checks"]["cloudinary"]["configured"] is True)

    print("\n=== 2. Damage types ===")
    types = session.get(f"{base}/damage-types", timeout=30).json()
    keys = [item["class_key"] for item in types["items"]]
    check("six classes seeded", types["total"] == 6, str(keys))
    check("critical flags set",
          {i["class_key"] for i in types["items"] if i["is_critical"]}
          == {"glass_shatter", "lamp_broken", "tire_flat"})

    print("\n=== 3. Auth ===")
    email = f"smoke-{unique}@example.com"
    register = session.post(
        f"{base}/auth/register",
        json={"email": email, "password": "Passw0rd123", "full_name": "Smoke Test"},
        timeout=30,
    )
    check("register returns 201", register.status_code == 201, str(register.status_code))
    body = register.json()
    check("no password in response", "password_hash" not in body["user"])
    token = body["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    login = session.post(
        f"{base}/auth/login", json={"email": email, "password": "Passw0rd123"}, timeout=30
    )
    check("login works", login.status_code == 200)

    bad_login = session.post(
        f"{base}/auth/login", json={"email": email, "password": "WrongPass1"}, timeout=30
    )
    check("wrong password rejected", bad_login.status_code == 401)
    check("unauthenticated request rejected",
          session.get(f"{base}/auth/me", timeout=30).status_code == 401)

    print("\n=== 4. Cloudinary signature ===")
    signature = session.post(f"{base}/uploads/signature", json={}, headers=headers, timeout=30)
    sig = signature.json()
    check("signature issued", signature.status_code == 200)
    check("signature is a sha1 hex digest", len(sig.get("signature", "")) == 40)
    check("api_secret NOT exposed", "api_secret" not in sig and "CLOUDINARY_API_SECRET" not in sig)
    check("upload folder is per-user", "/" in sig.get("folder", ""), sig.get("folder"))

    print("\n=== 5. Create inspection ===")
    idem = f"smoke-{unique}"
    create = session.post(
        f"{base}/inspections",
        json=create_body(IMAGES),
        headers={**headers, "Idempotency-Key": idem},
        timeout=60,
    )
    check("returns 202 Accepted", create.status_code == 202, str(create.status_code))
    created = create.json()
    inspection_id = created["id"]
    check("returns a usable id", bool(uuid.UUID(created["id"])), created["id"])
    check("queued immediately", created["status"] == "queued")

    replay = session.post(
        f"{base}/inspections",
        json=create_body({"front": IMAGES["front"]}),
        headers={**headers, "Idempotency-Key": idem},
        timeout=60,
    )
    check("idempotent replay returns 200", replay.status_code == 200)
    check("replay returns the same inspection", replay.json()["id"] == inspection_id)
    check("replay flagged as not created", replay.json()["created"] is False)

    print("\n=== 6. Validation ===")
    bad = session.post(
        f"{base}/inspections",
        json=create_body({"front": "http://insecure/a.jpg"}),
        headers=headers,
        timeout=30,
    )
    check("http URL rejected (422)", bad.status_code == 422)

    empty = session.post(f"{base}/inspections", json=create_body({}), headers=headers, timeout=30)
    check("empty image map rejected (422)", empty.status_code == 422)

    unknown = session.post(
        f"{base}/inspections",
        json=create_body({"bonnet": IMAGES["front"]}),
        headers=headers,
        timeout=30,
    )
    check("unknown view rejected (422)", unknown.status_code == 422)

    nameless = session.post(
        f"{base}/inspections",
        json={"vehicle_type": "suv", "images": {"front": IMAGES["front"]}},
        headers=headers,
        timeout=30,
    )
    check("missing customer_name rejected (422)", nameless.status_code == 422)

    print("\n=== 7. Waiting for real inference ===")
    started = time.time()
    status = {}
    while time.time() - started < args.timeout:
        status = session.get(
            f"{base}/inspections/{inspection_id}/status", headers=headers, timeout=30
        ).json()
        elapsed = int(time.time() - started)
        print(f"    t+{elapsed:>3}s  status={status['status']:<16} "
              f"detections={status['total_detections']} score={status['damage_score']}")
        if status.get("is_finished"):
            break
        time.sleep(3)

    check("inference finished", bool(status.get("is_finished")),
          f"after {int(time.time() - started)}s")
    check("status is a success state", status.get("status") in {"completed", "partial_success"},
          str(status.get("status")))

    print("\n=== 8. Report ===")
    detail = session.get(f"{base}/inspections/{inspection_id}", headers=headers, timeout=60).json()
    report = detail["report"]

    check("customer name stored", detail["customer_name"] == "test",
          str(detail["customer_name"]))
    check("vehicle type stored", detail["vehicle_type"] == "suv", str(detail["vehicle_type"]))
    check(f"all {len(IMAGES)} images analysed", report["images_analysed"] == len(IMAGES),
          f"{report['images_analysed']}/{len(IMAGES)}")
    check("views reported in canonical order",
          [img["view_angle"] for img in report["images"]] == list(IMAGES),
          str([img["view_angle"] for img in report["images"]]))
    check("summary covers all six classes", len(report["damage_summary"]) == 6)
    check("overall_status is valid",
          report["overall_status"] in {"damage_detected", "no_damage_detected"},
          report["overall_status"])
    check("damage score within 0-100", 0 <= report["damage_score"] <= 100,
          str(report["damage_score"]))
    check("model recorded on the report", bool(report["model"]["name"]),
          f"{report['model']['name']} v{report['model']['version']}")
    check("processing time recorded", (report["processing_ms"] or 0) > 0,
          f"{report['processing_ms']}ms")

    print("\n    Detections found:")
    any_detection = False
    for image in report["images"]:
        quality = image.get("quality") or {}
        print(f"      {image['view_angle']:<6} status={image['status']:<10} "
              f"blur={quality.get('blur_score')} bright={quality.get('brightness')} "
              f"detections={len(image['detections'])}")
        for found in image["detections"]:
            any_detection = True
            print(f"        - {found['label']:<14} conf={found['confidence']:.3f} "
                  f"severity={found['severity']:<9} bbox={found['bbox']}")

    print(f"\n    damage_score = {report['damage_score']}/100  "
          f"severity = {report['overall_severity']}  "
          f"total_area = {report['total_area_percent']}%")
    if report["image_quality_warnings"]:
        print("    photo quality warnings:")
        for warning in report["image_quality_warnings"]:
            print(f"      image {warning['sequence_no']}: {warning['warning']}")

    if any_detection:
        check("detections carry a class label and severity", True)

    print("\n=== 9. History ===")
    history = session.get(f"{base}/inspections", headers=headers, timeout=30).json()
    check("history lists the inspection", history["total"] >= 1, f"total={history['total']}")
    check("history rows are compact", "report" not in history["items"][0])

    paged = session.get(f"{base}/inspections?page=1&page_size=1", headers=headers, timeout=30).json()
    check("pagination works", len(paged["items"]) == 1 and paged["page_size"] == 1)

    bad_filter = session.get(f"{base}/inspections?status=nonsense", headers=headers, timeout=30)
    check("unknown status filter rejected (422)", bad_filter.status_code == 422)

    print("\n=== 10. Ownership isolation ===")
    other = session.post(
        f"{base}/auth/register",
        json={"email": f"intruder-{unique}@example.com", "password": "Passw0rd123"},
        timeout=30,
    ).json()
    other_headers = {"Authorization": f"Bearer {other['access_token']}"}

    check("other user gets 404 on read",
          session.get(f"{base}/inspections/{inspection_id}", headers=other_headers,
                      timeout=30).status_code == 404)
    check("other user gets 404 on delete",
          session.delete(f"{base}/inspections/{inspection_id}", headers=other_headers,
                         timeout=30).status_code == 404)
    check("other user's history is empty",
          session.get(f"{base}/inspections", headers=other_headers, timeout=30).json()["total"] == 0)

    print("\n=== 11. Stats and soft delete ===")
    stats = session.get(f"{base}/stats/summary", headers=headers, timeout=30).json()
    check("stats report inspections", stats["total_inspections"] >= 1)

    deleted = session.delete(f"{base}/inspections/{inspection_id}", headers=headers, timeout=30)
    check("owner can delete", deleted.status_code == 200)
    check("deleted inspection is hidden",
          session.get(f"{base}/inspections/{inspection_id}", headers=headers,
                      timeout=30).status_code == 404)

    print("\n" + "=" * 62)
    print(f"  {passed} passed, {failed} failed")
    print("=" * 62)
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except requests.ConnectionError as exc:
        print(f"\nCould not reach the API: {exc}")
        print("Start it first:  python -m waitress --port=5055 wsgi:app")
        sys.exit(2)
