"""End-to-end API tests: auth, the inspection pipeline, history and ownership."""

import uuid

import pytest

from app.models import Inspection
from tests.conftest import (
    StubDetector,
    auth_headers,
    create_body,
    detection,
    image_map,
    image_url,
    make_prepared_image,
)


@pytest.fixture
def stub_model(monkeypatch):
    """Replace the model and the image download so tests need no network."""

    def _install(detections=None, raise_error=False):
        stub = StubDetector(detections=detections, raise_error=raise_error)
        monkeypatch.setattr("app.tasks.inspection_job.get_detector", lambda config: stub)
        monkeypatch.setattr(
            "app.tasks.inspection_job.load_image",
            lambda url, public_id, **kwargs: make_prepared_image(public_id),
        )
        return stub

    return _install


class TestHealth:
    def test_health_is_public(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200
        assert response.get_json()["status"] == "ok"

    def test_readiness_reports_checks(self, client):
        response = client.get("/api/v1/health/ready")
        body = response.get_json()
        assert response.status_code == 200
        assert body["checks"]["database"]["ok"] is True
        assert body["checks"]["model"]["ok"] is True

    def test_root_endpoint(self, client):
        assert client.get("/").status_code == 200


class TestAuth:
    def test_register_returns_tokens(self, client):
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "new@example.com", "password": "Passw0rd123"},
        )
        assert response.status_code == 201
        body = response.get_json()
        assert body["access_token"] and body["refresh_token"]
        assert body["user"]["email"] == "new@example.com"
        assert "password" not in body["user"]
        assert "password_hash" not in body["user"]

    def test_duplicate_email_is_rejected(self, client):
        client.post("/api/v1/auth/register", json={"email": "dup@example.com", "password": "Passw0rd123"})
        response = client.post(
            "/api/v1/auth/register", json={"email": "dup@example.com", "password": "Passw0rd123"}
        )
        assert response.status_code == 409
        assert response.get_json()["error"]["code"] == "CONFLICT"

    def test_weak_password_is_rejected(self, client):
        response = client.post(
            "/api/v1/auth/register", json={"email": "weak@example.com", "password": "12345678"}
        )
        assert response.status_code == 422
        assert response.get_json()["error"]["code"] == "VALIDATION_ERROR"

    def test_login_with_correct_password(self, client):
        client.post("/api/v1/auth/register", json={"email": "log@example.com", "password": "Passw0rd123"})
        response = client.post(
            "/api/v1/auth/login", json={"email": "log@example.com", "password": "Passw0rd123"}
        )
        assert response.status_code == 200

    def test_login_with_wrong_password(self, client):
        client.post("/api/v1/auth/register", json={"email": "log2@example.com", "password": "Passw0rd123"})
        response = client.post(
            "/api/v1/auth/login", json={"email": "log2@example.com", "password": "WrongPass1"}
        )
        assert response.status_code == 401

    def test_unknown_email_gives_same_error_as_wrong_password(self, client):
        """The response must not reveal whether an account exists."""
        response = client.post(
            "/api/v1/auth/login", json={"email": "ghost@example.com", "password": "Passw0rd123"}
        )
        assert response.status_code == 401
        assert response.get_json()["error"]["code"] == "AUTHENTICATION_FAILED"

    def test_me_requires_a_token(self, client):
        assert client.get("/api/v1/auth/me").status_code == 401

    def test_me_returns_the_user(self, client):
        headers = auth_headers(client)
        response = client.get("/api/v1/auth/me", headers=headers)
        assert response.status_code == 200
        assert response.get_json()["user"]["email"] == "driver@example.com"


class TestDamageTypes:
    def test_returns_the_six_model_classes(self, client):
        response = client.get("/api/v1/damage-types")
        body = response.get_json()
        assert response.status_code == 200
        assert body["total"] == 6

        keys = [item["class_key"] for item in body["items"]]
        assert keys == ["dent", "scratch", "crack", "glass_shatter", "lamp_broken", "tire_flat"]

    def test_includes_colours_for_the_frontend(self, client):
        items = client.get("/api/v1/damage-types").get_json()["items"]
        assert all(item["color_hex"].startswith("#") for item in items)

    def test_marks_critical_classes(self, client):
        items = client.get("/api/v1/damage-types").get_json()["items"]
        critical = {item["class_key"] for item in items if item["is_critical"]}
        assert critical == {"glass_shatter", "lamp_broken", "tire_flat"}


class TestVehicleTypes:
    def test_lists_car_body_styles_publicly(self, client):
        """Public so the submission form can be built before a user logs in."""
        response = client.get("/api/v1/vehicle-types")
        body = response.get_json()
        assert response.status_code == 200

        keys = [item["key"] for item in body["items"]]
        assert keys[:3] == ["hatchback", "sedan", "suv"]
        assert "other" in keys
        # These are body styles, not vehicle categories.
        assert "car" not in keys
        assert body["total"] == len(keys)
        assert all(item["label"] for item in body["items"])

    def test_every_listed_type_is_accepted_by_the_api(self, client, stub_model):
        """The list the UI is given must match what the schema will allow."""
        stub_model([])
        headers = auth_headers(client)
        for item in client.get("/api/v1/vehicle-types").get_json()["items"]:
            response = client.post(
                "/api/v1/inspections",
                json=create_body(vehicle_type=item["key"], prefix=item["key"]),
                headers=headers,
            )
            assert response.status_code == 202, (item["key"], response.get_json())


class TestCreateInspection:
    def test_requires_authentication(self, client):
        response = client.post("/api/v1/inspections", json=create_body())
        assert response.status_code == 401

    def test_rejects_an_empty_image_map(self, client):
        headers = auth_headers(client)
        body = create_body()
        body["images"] = {}
        response = client.post("/api/v1/inspections", json=body, headers=headers)
        assert response.status_code == 422

    def test_rejects_non_https_urls(self, client):
        headers = auth_headers(client)
        body = create_body()
        body["images"] = {"front": "http://insecure.example.com/a.jpg"}
        response = client.post("/api/v1/inspections", json=body, headers=headers)
        assert response.status_code == 422

    def test_rejects_the_same_url_for_two_views(self, client):
        headers = auth_headers(client)
        body = create_body()
        body["images"] = {"front": image_url("same"), "back": image_url("same")}
        response = client.post("/api/v1/inspections", json=body, headers=headers)
        assert response.status_code == 422

    def test_rejects_an_unknown_view(self, client):
        headers = auth_headers(client)
        body = create_body()
        body["images"] = {"bonnet": image_url("a")}
        response = client.post("/api/v1/inspections", json=body, headers=headers)
        assert response.status_code == 422
        assert "bonnet" in str(response.get_json()["error"])

    @pytest.mark.parametrize("missing", ["customer_name", "vehicle_type"])
    def test_requires_customer_name_and_vehicle_type(self, client, missing):
        headers = auth_headers(client)
        body = create_body()
        del body[missing]
        response = client.post("/api/v1/inspections", json=body, headers=headers)
        assert response.status_code == 422

    @pytest.mark.parametrize("blank", ["", "   "])
    def test_rejects_a_blank_customer_name(self, client, blank):
        headers = auth_headers(client)
        response = client.post(
            "/api/v1/inspections", json=create_body(customer_name=blank), headers=headers
        )
        assert response.status_code == 422

    @pytest.mark.parametrize("body_style", ["hatchback", "sedan", "suv", "muv", "van", "other"])
    def test_accepts_every_body_style(self, client, stub_model, body_style):
        stub_model([])
        headers = auth_headers(client)
        response = client.post(
            "/api/v1/inspections", json=create_body(vehicle_type=body_style), headers=headers
        )
        assert response.status_code == 202
        assert response.get_json()["vehicle_type"] == body_style

    @pytest.mark.parametrize("rejected", ["car", "bike", "truck", "bus", "spaceship"])
    def test_rejects_a_category_instead_of_a_body_style(self, client, rejected):
        """vehicle_type is the car's shape, so "car" itself is not a valid value."""
        headers = auth_headers(client)
        response = client.post(
            "/api/v1/inspections", json=create_body(vehicle_type=rejected), headers=headers
        )
        assert response.status_code == 422
        assert "vehicle_type" in str(response.get_json()["error"])

    def test_accepts_all_five_views_and_returns_202(self, client, stub_model):
        stub_model([detection("dent")])
        headers = auth_headers(client)

        response = client.post(
            "/api/v1/inspections",
            json=create_body("front", "back", "left", "right", "top"),
            headers=headers,
        )
        body = response.get_json()

        assert response.status_code == 202
        assert body["created"] is True
        assert body["image_count"] == 5
        # The id is the only handle a client gets, so it must be usable as one.
        assert uuid.UUID(body["id"])

    def test_views_are_stored_in_canonical_order(self, client, stub_model):
        """sequence_no must not depend on the order the JSON keys arrived in."""
        stub_model([])
        headers = auth_headers(client)

        body = create_body()
        body["images"] = {
            view: image_url(view) for view in ("top", "left", "front", "right", "back")
        }
        created = client.post("/api/v1/inspections", json=body, headers=headers).get_json()

        report = client.get(
            f"/api/v1/inspections/{created['id']}", headers=headers
        ).get_json()["report"]
        assert [image["view_angle"] for image in report["images"]] == [
            "front",
            "back",
            "left",
            "right",
            "top",
        ]

    def test_idempotency_key_prevents_a_duplicate(self, client, stub_model):
        stub_model([detection("dent")])
        headers = {**auth_headers(client), "Idempotency-Key": "submit-once-abc"}
        payload = create_body()

        first = client.post("/api/v1/inspections", json=payload, headers=headers)
        second = client.post("/api/v1/inspections", json=payload, headers=headers)

        assert first.status_code == 202
        assert second.status_code == 200
        assert second.get_json()["created"] is False
        assert first.get_json()["id"] == second.get_json()["id"]

    def test_stores_customer_name_and_vehicle_type(self, client, stub_model):
        stub_model([])
        headers = auth_headers(client)
        response = client.post(
            "/api/v1/inspections",
            json=create_body(customer_name="  test   kumar ", vehicle_type="SUV"),
            headers=headers,
        )
        created = response.get_json()

        # Whitespace is collapsed, and the type lower-cased so it groups in stats.
        assert created["customer_name"] == "test kumar"
        assert created["vehicle_type"] == "suv"

        detail = client.get(
            f"/api/v1/inspections/{created['id']}", headers=headers
        ).get_json()
        assert detail["customer_name"] == "test kumar"
        assert detail["vehicle_type"] == "suv"

        report = client.get(
            f"/api/v1/inspections/{created['id']}/report", headers=headers
        ).get_json()
        assert report["customer_name"] == "test kumar"
        assert report["vehicle_type"] == "suv"


class TestReport:
    def test_report_contains_detections_and_score(self, client, stub_model):
        stub_model([detection("dent", 0.9), detection("tire flat", 0.8, bbox=(500, 500, 80, 80))])
        headers = auth_headers(client)

        created = client.post(
            "/api/v1/inspections", json=create_body(), headers=headers
        ).get_json()
        detail = client.get(f"/api/v1/inspections/{created['id']}", headers=headers).get_json()

        report = detail["report"]
        assert detail["status"] == "completed"
        assert report["overall_status"] == "damage_detected"
        assert report["total_detections"] == 2
        # tire_flat is critical: 25 + (2 * 8) + area = at least 41
        assert report["damage_score"] >= 41
        assert report["overall_severity"] in {"minor", "moderate", "severe"}

    def test_summary_lists_all_six_classes_including_zeroes(self, client, stub_model):
        """A user needs to see "no glass shatter", not just an absent key."""
        stub_model([detection("scratch")])
        headers = auth_headers(client)

        created = client.post(
            "/api/v1/inspections", json=create_body(), headers=headers
        ).get_json()
        report = client.get(
            f"/api/v1/inspections/{created['id']}/report", headers=headers
        ).get_json()["report"]

        summary = {row["class_key"]: row["count"] for row in report["damage_summary"]}
        assert len(summary) == 6
        assert summary["scratch"] == 1
        assert summary["glass_shatter"] == 0

    def test_clean_car_is_not_an_error(self, client, stub_model):
        stub_model([])
        headers = auth_headers(client)

        created = client.post(
            "/api/v1/inspections", json=create_body(), headers=headers
        ).get_json()
        detail = client.get(f"/api/v1/inspections/{created['id']}", headers=headers).get_json()

        assert detail["status"] == "completed"
        assert detail["report"]["overall_status"] == "no_damage_detected"
        assert detail["report"]["damage_score"] == 0
        assert detail["report"]["overall_severity"] == "none"

    def test_detection_includes_bbox_and_area(self, client, stub_model):
        stub_model([detection("dent", 0.9, bbox=(10, 20, 100, 50))])
        headers = auth_headers(client)

        created = client.post(
            "/api/v1/inspections", json=create_body(), headers=headers
        ).get_json()
        detail = client.get(f"/api/v1/inspections/{created['id']}", headers=headers).get_json()

        found = detail["report"]["images"][0]["detections"][0]
        assert found["bbox"] == {"x": 10, "y": 20, "width": 100, "height": 50}
        assert found["class_key"] == "dent"
        assert found["label"] == "Dent"
        assert found["area_ratio"] > 0

    def test_bboxes_match_the_dimensions_the_report_advertises(self, client, monkeypatch):
        """Boxes and `dimensions` must describe the same coordinate space.

        The request carries only a URL, so the size the model analysed is the
        only size known - and it is what the UI uses as its SVG viewBox. If the
        two disagreed the overlay would be drawn at the wrong scale.
        """
        stub = StubDetector(detections=[detection("dent", 0.9, bbox=(100, 50, 200, 100))])
        monkeypatch.setattr("app.tasks.inspection_job.get_detector", lambda config: stub)
        # The model sees a downscaled copy of the Cloudinary original.
        monkeypatch.setattr(
            "app.tasks.inspection_job.load_image",
            lambda url, public_id, **kwargs: make_prepared_image(public_id, 960, 540),
        )

        headers = auth_headers(client)
        created = client.post(
            "/api/v1/inspections", json=create_body(), headers=headers
        ).get_json()
        report = client.get(
            f"/api/v1/inspections/{created['id']}", headers=headers
        ).get_json()["report"]

        box = report["images"][0]["detections"][0]["bbox"]
        assert box == {"x": 100, "y": 50, "width": 200, "height": 100}

        # Reported dimensions are the analysed ones, and the box fits inside them.
        dimensions = report["images"][0]["dimensions"]
        assert dimensions == {"width": 960, "height": 540}
        assert box["x"] + box["width"] <= dimensions["width"]
        assert box["y"] + box["height"] <= dimensions["height"]

    def test_area_ratio_is_unaffected_by_scaling(self, client, monkeypatch):
        """area_ratio is a proportion, so downscaling must not change it."""
        stub = StubDetector(detections=[detection("dent", 0.9, bbox=(0, 0, 480, 270))])
        monkeypatch.setattr("app.tasks.inspection_job.get_detector", lambda config: stub)
        monkeypatch.setattr(
            "app.tasks.inspection_job.load_image",
            lambda url, public_id, **kwargs: make_prepared_image(public_id, 960, 540),
        )

        headers = auth_headers(client)
        created = client.post(
            "/api/v1/inspections",
            json=create_body(),
            headers=headers,
        ).get_json()
        report = client.get(
            f"/api/v1/inspections/{created['id']}", headers=headers
        ).get_json()["report"]

        # 480x270 of 960x540 is a quarter of the frame, at either scale.
        assert report["images"][0]["detections"][0]["area_ratio"] == pytest.approx(0.25)

    def test_area_percent_cannot_exceed_100_across_images(self, client, stub_model):
        """Averaged, not summed: five images of 60% damage each is 60%, not 300%."""
        stub_model([detection("dent", 0.9, bbox=(0, 0, 900, 700))])
        headers = auth_headers(client)

        created = client.post(
            "/api/v1/inspections",
            json=create_body("front", "back", "left", "right", "top"),
            headers=headers,
        ).get_json()
        report = client.get(
            f"/api/v1/inspections/{created['id']}", headers=headers
        ).get_json()["report"]

        assert 0 <= report["total_area_percent"] <= 100
        for row in report["damage_summary"]:
            assert 0 <= row["total_area_percent"] <= 100

    def test_status_endpoint_is_lightweight(self, client, stub_model):
        stub_model([detection("dent")])
        headers = auth_headers(client)

        created = client.post(
            "/api/v1/inspections", json=create_body(), headers=headers
        ).get_json()
        status = client.get(
            f"/api/v1/inspections/{created['id']}/status", headers=headers
        ).get_json()

        assert status["is_finished"] is True
        assert status["status"] == "completed"
        assert "report" not in status


class TestSensitivity:
    """Per-inspection sensitivity - the fix for damage being silently dropped."""

    def test_presets_endpoint_lists_the_three_modes(self, client):
        body = client.get('/api/v1/detection-presets').get_json()
        keys = {item['key']: item for item in body['items']}
        assert set(keys) == {'balanced', 'sensitive', 'strict'}
        assert keys['balanced']['confidence'] == 0.35
        assert keys['sensitive']['confidence'] == 0.22
        assert keys['strict']['confidence'] == 0.50
        assert body['default'] == 'balanced'

    def test_default_preset_is_recorded(self, client, stub_model):
        stub_model([detection('dent')])
        headers = auth_headers(client)
        created = client.post(
            '/api/v1/inspections', json=create_body(), headers=headers
        ).get_json()
        assert created['detection_preset'] == 'balanced'
        assert created['detection_settings']['confidence'] == 0.35

    def test_sensitive_preset_is_passed_to_the_model(self, client, stub_model):
        stub = stub_model([detection('dent')])
        headers = auth_headers(client)
        client.post(
            '/api/v1/inspections',
            json=create_body(settings={'preset': 'sensitive'}),
            headers=headers,
        )
        assert stub.last_options.confidence == 0.22

    def test_sensitive_preset_keeps_findings_balanced_would_drop(self, client, stub_model):
        """A 0.28-confidence dent: invisible at 0.35, reported at 0.22.

        This is the reported bug - damage present in the photo but missing from
        the report.
        """
        stub_model([detection('dent', 0.28), detection('scratch', 0.80, bbox=(400, 300, 90, 60))])
        headers = auth_headers(client)

        balanced = client.post(
            '/api/v1/inspections',
            json=create_body(prefix='b', settings={'preset': 'balanced'}),
            headers=headers,
        ).get_json()
        sensitive = client.post(
            '/api/v1/inspections',
            json=create_body(prefix='s', settings={'preset': 'sensitive'}),
            headers=headers,
        ).get_json()

        def classes_found(inspection_id):
            report = client.get(
                f"/api/v1/inspections/{inspection_id}", headers=headers
            ).get_json()['report']
            return {
                row['class_key'] for row in report['damage_summary'] if row['count'] > 0
            }, report

        balanced_classes, balanced_report = classes_found(balanced['id'])
        sensitive_classes, sensitive_report = classes_found(sensitive['id'])

        assert balanced_classes == {'scratch'}
        assert sensitive_classes == {'scratch', 'dent'}

        # And the balanced run must say something was withheld, not stay silent.
        assert balanced_report['below_threshold_count'] == 1
        assert sensitive_report['below_threshold_count'] == 0

    def test_explicit_confidence_overrides_the_preset(self, client, stub_model):
        stub = stub_model([detection('dent')])
        headers = auth_headers(client)
        created = client.post(
            '/api/v1/inspections',
            json={
                'customer_name': 'test',
                'vehicle_type': 'suv',
                'images': image_map(),
                'settings': {'preset': 'strict', 'confidence': 0.4},
            },
            headers=headers,
        ).get_json()

        assert stub.last_options.confidence == 0.4
        assert stub.last_options.iou == 0.45  # untouched by the override
        assert created['detection_preset'] == 'strict+custom'

    def test_unknown_preset_is_rejected(self, client):
        headers = auth_headers(client)
        response = client.post(
            '/api/v1/inspections',
            json=create_body(settings={'preset': 'paranoid'}),
            headers=headers,
        )
        assert response.status_code == 422

    def test_input_size_must_be_a_multiple_of_32(self, client):
        headers = auth_headers(client)
        response = client.post(
            '/api/v1/inspections',
            json=create_body(settings={'input_size': 1000}),
            headers=headers,
        )
        assert response.status_code == 422

    def test_out_of_range_confidence_is_rejected(self, client):
        headers = auth_headers(client)
        response = client.post(
            '/api/v1/inspections',
            json=create_body(settings={'confidence': 1.5}),
            headers=headers,
        )
        assert response.status_code == 422

    def test_settings_are_stored_on_the_report(self, client, stub_model):
        stub_model([detection('dent')])
        headers = auth_headers(client)
        created = client.post(
            '/api/v1/inspections',
            json=create_body(settings={'preset': 'sensitive'}),
            headers=headers,
        ).get_json()

        report = client.get(
            f"/api/v1/inspections/{created['id']}", headers=headers
        ).get_json()['report']

        assert report['detection_preset'] == 'sensitive'
        assert report['detection_settings']['confidence'] == 0.22
        assert report['detection_settings']['iou'] == 0.45


class TestFailureHandling:
    def test_one_bad_image_does_not_fail_the_inspection(self, client, monkeypatch):
        """The documented behaviour: carry on with the images that did work."""
        from app.errors import ImageUnreachableError

        stub = StubDetector(detections=[detection("dent")])
        monkeypatch.setattr("app.tasks.inspection_job.get_detector", lambda config: stub)

        def flaky_loader(url, public_id, **kwargs):
            # public_id is derived from the URL, so the back shot ends in "-back".
            if public_id.endswith("-back"):
                raise ImageUnreachableError("Could not download image: simulated 404")
            return make_prepared_image(public_id)

        monkeypatch.setattr("app.tasks.inspection_job.load_image", flaky_loader)

        headers = auth_headers(client)
        created = client.post(
            "/api/v1/inspections",
            json=create_body("front", "back", "left"),
            headers=headers,
        ).get_json()
        detail = client.get(f"/api/v1/inspections/{created['id']}", headers=headers).get_json()

        assert detail["status"] == "partial_success"
        assert detail["report"]["partial_success"] is True
        assert detail["report"]["images_analysed"] == 2
        assert detail["report"]["images_submitted"] == 3

        failed = [img for img in detail["report"]["images"] if img["status"] == "failed"]
        assert len(failed) == 1
        assert "simulated 404" in failed[0]["failure_reason"]

    def test_all_images_failing_fails_the_inspection(self, client, monkeypatch):
        from app.errors import ImageUnreachableError

        stub = StubDetector(detections=[])
        monkeypatch.setattr("app.tasks.inspection_job.get_detector", lambda config: stub)
        monkeypatch.setattr(
            "app.tasks.inspection_job.load_image",
            lambda url, public_id, **kwargs: (_ for _ in ()).throw(
                ImageUnreachableError("all broken")
            ),
        )

        headers = auth_headers(client)
        created = client.post(
            "/api/v1/inspections", json=create_body(), headers=headers
        ).get_json()
        detail = client.get(f"/api/v1/inspections/{created['id']}", headers=headers).get_json()

        assert detail["status"] == "failed"
        assert detail["error"]["code"] == "ALL_IMAGES_FAILED"

    def test_model_errors_are_retried_then_recorded(self, client, monkeypatch, app):
        app.config["INFERENCE_MAX_RETRIES"] = 2
        monkeypatch.setattr("app.tasks.inspection_job.time.sleep", lambda seconds: None)

        stub = StubDetector(raise_error=True)
        monkeypatch.setattr("app.tasks.inspection_job.get_detector", lambda config: stub)
        monkeypatch.setattr(
            "app.tasks.inspection_job.load_image",
            lambda url, public_id, **kwargs: make_prepared_image(public_id),
        )

        headers = auth_headers(client)
        created = client.post(
            "/api/v1/inspections", json=create_body(), headers=headers
        ).get_json()
        detail = client.get(f"/api/v1/inspections/{created['id']}", headers=headers).get_json()

        assert stub.calls == 2  # retried before giving up
        assert detail["status"] == "failed"


class TestHistoryAndOwnership:
    def test_history_lists_the_users_inspections(self, client, stub_model):
        stub_model([detection("dent")])
        headers = auth_headers(client)

        for i in range(3):
            client.post(
                "/api/v1/inspections", json=create_body(prefix=f"h{i}"), headers=headers
            )

        body = client.get("/api/v1/inspections", headers=headers).get_json()
        assert body["total"] == 3
        assert len(body["items"]) == 3
        assert body["page"] == 1

    def test_history_is_paginated(self, client, stub_model):
        stub_model([])
        headers = auth_headers(client)
        for i in range(5):
            client.post(
                "/api/v1/inspections", json=create_body(prefix=f"p{i}"), headers=headers
            )

        body = client.get("/api/v1/inspections?page=1&page_size=2", headers=headers).get_json()
        assert len(body["items"]) == 2
        assert body["total"] == 5
        assert body["total_pages"] == 3
        assert body["has_next"] is True

    def test_history_filters_by_damage_type(self, client, stub_model):
        stub_model([detection("scratch")])
        headers = auth_headers(client)
        client.post("/api/v1/inspections", json=create_body(), headers=headers)

        matching = client.get("/api/v1/inspections?damage_type=scratch", headers=headers).get_json()
        other = client.get("/api/v1/inspections?damage_type=tire_flat", headers=headers).get_json()

        assert matching["total"] == 1
        assert other["total"] == 0

    def test_unknown_filter_is_rejected(self, client):
        headers = auth_headers(client)
        response = client.get("/api/v1/inspections?status=not_a_status", headers=headers)
        assert response.status_code == 422

    def test_a_user_cannot_read_another_users_inspection(self, client, stub_model):
        stub_model([detection("dent")])

        owner = auth_headers(client, email="owner@example.com")
        created = client.post(
            "/api/v1/inspections", json=create_body(), headers=owner
        ).get_json()

        intruder = auth_headers(client, email="intruder@example.com")
        response = client.get(f"/api/v1/inspections/{created['id']}", headers=intruder)

        # 404 rather than 403, so the API does not confirm the id exists.
        assert response.status_code == 404

    def test_a_user_cannot_delete_another_users_inspection(self, client, stub_model):
        stub_model([])
        owner = auth_headers(client, email="owner2@example.com")
        created = client.post(
            "/api/v1/inspections", json=create_body(), headers=owner
        ).get_json()

        intruder = auth_headers(client, email="intruder2@example.com")
        assert client.delete(f"/api/v1/inspections/{created['id']}", headers=intruder).status_code == 404

    def test_another_users_inspection_is_absent_from_history(self, client, stub_model):
        stub_model([])
        owner = auth_headers(client, email="owner3@example.com")
        client.post("/api/v1/inspections", json=create_body(), headers=owner)

        other = auth_headers(client, email="other3@example.com")
        assert client.get("/api/v1/inspections", headers=other).get_json()["total"] == 0

    def test_soft_delete_hides_but_keeps_the_row(self, client, stub_model, db):
        stub_model([])
        headers = auth_headers(client)
        created = client.post(
            "/api/v1/inspections", json=create_body(), headers=headers
        ).get_json()

        assert client.delete(f"/api/v1/inspections/{created['id']}", headers=headers).status_code == 200
        assert client.get(f"/api/v1/inspections/{created['id']}", headers=headers).status_code == 404

        # The history record itself survives - deletion is a flag, not a DELETE.
        row = db.session.get(Inspection, uuid.UUID(created["id"]))
        assert row is not None
        assert row.deleted_at is not None

    def test_unknown_inspection_id_is_404(self, client):
        headers = auth_headers(client)
        assert client.get("/api/v1/inspections/not-a-uuid", headers=headers).status_code == 404


class TestProvenance:
    def test_model_that_produced_the_findings_is_recorded(self, client, stub_model, db):
        """A report has to be able to say which model produced it."""
        stub_model([detection("dent")])
        headers = auth_headers(client)
        created = client.post(
            "/api/v1/inspections",
            json=create_body("front", "back", "left"),
            headers=headers,
        ).get_json()

        row = db.session.get(Inspection, uuid.UUID(created["id"]))
        assert row.model_backend == StubDetector.backend_name
        assert row.model_name and row.model_version

        report = client.get(
            f"/api/v1/inspections/{created['id']}/report", headers=headers
        ).get_json()["report"]
        assert report["model"] == {
            "name": row.model_name,
            "version": row.model_version,
            "backend": StubDetector.backend_name,
        }


class TestStats:
    def test_summary_counts_by_class_and_severity(self, client, stub_model):
        stub_model([detection("dent"), detection("scratch", bbox=(400, 400, 60, 60))])
        headers = auth_headers(client)
        client.post("/api/v1/inspections", json=create_body(), headers=headers)

        body = client.get("/api/v1/stats/summary", headers=headers).get_json()
        assert body["total_inspections"] == 1
        counts = {row["class_key"]: row["count"] for row in body["by_damage_type"]}
        assert counts["dent"] == 1
        assert counts["scratch"] == 1
        assert sum(body["by_severity"].values()) == 2
