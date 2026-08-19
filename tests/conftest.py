"""Shared test fixtures.

Tests run against in-memory SQLite with the mock model and no network access -
image downloads are stubbed, so the suite is fast and deterministic.
"""

import pytest
from PIL import Image

from app import create_app
from app.config import TestingConfig
from app.extensions import db as _db
from app.inference.base import InferenceResult, PreparedImage, RawDetection
from app.inference.registry import reset_detector
from app.seed import seed_damage_types


@pytest.fixture
def app():
    application = create_app(TestingConfig)
    with application.app_context():
        _db.create_all()
        seed_damage_types(application)
        yield application
        _db.session.remove()
        _db.drop_all()
    reset_detector()


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def db(app):
    return _db


def auth_headers(client, email="driver@example.com", password="Passw0rd123"):
    """Register a user and return ready-to-use Authorization headers."""
    response = client.post(
        "/api/v1/auth/register",
        json={"email": email, "password": password, "full_name": "Test Driver"},
    )
    assert response.status_code == 201, response.get_json()
    token = response.get_json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


def make_prepared_image(public_id="test/img1", width=1200, height=800) -> PreparedImage:
    return PreparedImage(
        image=Image.new("RGB", (width, height), color=(120, 120, 120)),
        width=width,
        height=height,
        source_url=f"https://res.cloudinary.com/demo/image/upload/{public_id}.jpg",
        public_id=public_id,
    )


class StubDetector:
    """Detector that returns exactly the detections a test asks for."""

    backend_name = "stub"

    def __init__(self, detections=None, raise_error=False):
        self._detections = detections or []
        self._raise_error = raise_error
        self.model_path = ""
        self.calls = 0

    def describe(self):
        return {"backend": self.backend_name, "loaded": True}

    def predict(self, image: PreparedImage, options=None) -> InferenceResult:
        self.calls += 1
        self.last_options = options
        if self._raise_error:
            raise RuntimeError("stub model failure")
        return InferenceResult(
            detections=list(self._detections),
            raw_output={"backend": self.backend_name, "detections": len(self._detections)},
            duration_ms=5,
            image_quality={"blur_score": 150.0, "brightness": 128.0, "is_blurry": False, "warnings": []},
            # Mirrors the real adapter: report the threshold the caller asked for.
            effective_confidence=options.confidence if options else 0.35,
        )


def detection(label, confidence=0.9, bbox=(10, 10, 100, 100)):
    return RawDetection(label=label, confidence=confidence, bbox=bbox)


def image_url(name="img1"):
    """A Cloudinary-shaped URL, which is all the API takes per image."""
    return f"https://res.cloudinary.com/demo/image/upload/v1787118301/test/{name}.jpg"


def image_map(*views, prefix="shot"):
    """The `images` block: one URL per view, defaulting to the front only."""
    return {view: image_url(f"{prefix}-{view}") for view in (views or ("front",))}


def create_body(*views, customer_name="test", vehicle_type="suv", prefix="shot", **extra):
    """A full `POST /inspections` body. Extra keys (e.g. settings) pass through."""
    return {
        "customer_name": customer_name,
        "vehicle_type": vehicle_type,
        "images": image_map(*views, prefix=prefix),
        **extra,
    }   
