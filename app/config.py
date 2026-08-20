"""Application configuration. All values come from the environment (12-factor)."""

import os
from datetime import timedelta
from pathlib import Path

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")


def _int(key: str, default: int) -> int:
    raw = os.getenv(key, "")
    return int(raw) if raw.strip() else default


def _float(key: str, default: float) -> float:
    raw = os.getenv(key, "")
    return float(raw) if raw.strip() else default


def _bool(key: str, default: bool) -> bool:
    raw = os.getenv(key, "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}


def _csv(key: str, default: str = "") -> list[str]:
    return [item.strip() for item in os.getenv(key, default).split(",") if item.strip()]


def _database_url() -> str:
    """Build the SQLAlchemy URL from the individual DB_* variables.

    A full DATABASE_URL wins if it is set, which is what most hosting
    providers inject.
    """
    explicit = os.getenv("DATABASE_URL", "").strip()
    if explicit:
        # Providers hand out the legacy postgres:// scheme; psycopg3 needs its own.
        if explicit.startswith("postgres://"):
            explicit = explicit.replace("postgres://", "postgresql+psycopg://", 1)
        elif explicit.startswith("postgresql://"):
            explicit = explicit.replace("postgresql://", "postgresql+psycopg://", 1)
        return explicit

    from urllib.parse import quote_plus

    user = os.getenv("DB_USER", "postgres")
    password = quote_plus(os.getenv("DB_PASSWORD", ""))
    host = os.getenv("DB_HOST", "localhost")
    port = os.getenv("DB_PORT", "5432")
    name = os.getenv("DB_NAME", "dent_detection")
    return f"postgresql+psycopg://{user}:{password}@{host}:{port}/{name}"


class BaseConfig:
    # --- Core ---
    ENV_NAME = os.getenv("APP_ENV", "development")
    SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me")
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
    JSON_SORT_KEYS = False

    # --- Database ---
    SQLALCHEMY_DATABASE_URI = _database_url()
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {"pool_pre_ping": True, "pool_recycle": 1800}

    # --- JWT ---
    JWT_SECRET_KEY = os.getenv("JWT_SECRET_KEY") or SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(minutes=_int("JWT_ACCESS_TOKEN_MINUTES", 60))
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=_int("JWT_REFRESH_TOKEN_DAYS", 30))

    # --- Cloudinary ---
    CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME", "")
    CLOUDINARY_API_KEY = os.getenv("CLOUDINARY_API_KEY", "")
    CLOUDINARY_API_SECRET = os.getenv("CLOUDINARY_API_SECRET", "")
    CLOUDINARY_UPLOAD_FOLDER = os.getenv("CLOUDINARY_UPLOAD_FOLDER", "dent-inspections")

    # --- Model ---
    # imgsz 640 and the TTA fallback off by default match the faster
    # `dent-detection` sibling project - see test-model/README.md for the
    # benchmark. Same YOLO11m weights either way; this only trades some recall
    # on faint damage for roughly 2.5-3x faster inference.
    MODEL_BACKEND = os.getenv("MODEL_BACKEND", "mock").lower()
    MODEL_PATH = os.getenv("MODEL_PATH", "")
    MODEL_NAME = os.getenv("MODEL_NAME", "autodent-yolo11m")
    MODEL_VERSION = os.getenv("MODEL_VERSION", "1.0.0")
    MODEL_CONFIDENCE_THRESHOLD = _float("MODEL_CONFIDENCE_THRESHOLD", 0.35)
    MODEL_IOU_THRESHOLD = _float("MODEL_IOU_THRESHOLD", 0.45)
    MODEL_INPUT_SIZE = _int("MODEL_INPUT_SIZE", 640)

    # Enhancement 3: CLAHE contrast pass. Off by default - it helps on glare and
    # shadow but changes pixels the model was not trained on, so it is opt-in.
    MODEL_USE_CLAHE = _bool("MODEL_USE_CLAHE", False)

    # Enhancement 2: retry with TTA when the first pass finds nothing at all.
    # Off by default (was on) - it roughly doubles inference time on every image
    # with no obvious damage. Still available per-inspection via `settings`.
    MODEL_FALLBACK_ENABLED = _bool("MODEL_FALLBACK_ENABLED", False)
    MODEL_FALLBACK_MIN_CONF = _float("MODEL_FALLBACK_MIN_CONF", 0.15)

    # Test-time augmentation. Roughly triples inference time, so off by default.
    MODEL_AUGMENT = _bool("MODEL_AUGMENT", False)

    # The model always runs at this floor and the backend filters afterwards.
    # Ultralytics applies `conf` after the forward pass, so a lower floor is free
    # and it lets the report say how many findings sat below the threshold.
    MODEL_DETECTION_FLOOR = _float("MODEL_DETECTION_FLOOR", 0.15)

    # The three modes from DOCUMENTATION.md section 4. A client sends a preset
    # name (or explicit values) per inspection.
    DETECTION_PRESETS = {
        "balanced": {
            "confidence": 0.35,
            "iou": 0.45,
            "input_size": 640,
            "augment": False,
            "label": "Balanced",
            "description": "Standard for good-quality photos.",
        },
        "sensitive": {
            "confidence": 0.22,
            "iou": 0.45,
            "input_size": 640,
            "augment": False,
            "label": "Sensitive",
            "description": "Finds faint scratches and shallow dents. More false positives.",
        },
        "strict": {
            "confidence": 0.50,
            "iou": 0.45,
            "input_size": 640,
            "augment": False,
            "label": "Strict",
            "description": "Minimises false positives for formal claims.",
        },
    }
    DEFAULT_DETECTION_PRESET = os.getenv("DEFAULT_DETECTION_PRESET", "balanced")

    # --- Images / inference ---
    MAX_IMAGES_PER_INSPECTION = _int("MAX_IMAGES_PER_INSPECTION", 10)
    MAX_IMAGE_BYTES = _int("MAX_IMAGE_BYTES", 10 * 1024 * 1024)
    IMAGE_DOWNLOAD_TIMEOUT = _int("IMAGE_DOWNLOAD_TIMEOUT", 20)
    INFERENCE_MAX_RETRIES = _int("INFERENCE_MAX_RETRIES", 3)
    INFERENCE_WORKERS = _int("INFERENCE_WORKERS", 2)

    # --- Config files ---
    SEVERITY_RULES_PATH = BASE_DIR / "config" / "severity_rules.json"
    CLASS_MAPPING_PATH = BASE_DIR / "config" / "class_mapping.json"

    # --- CORS / rate limiting ---
    CORS_ORIGINS = _csv("CORS_ORIGINS", "http://localhost:3000,http://localhost:5173")
    RATELIMIT_STORAGE_URI = os.getenv("RATELIMIT_STORAGE_URI", "memory://")
    RATELIMIT_DEFAULT = os.getenv("RATELIMIT_DEFAULT", "300 per hour")
    RATELIMIT_ENABLED = True

    # Run inference in a background thread (False = inline, useful for tests).
    RUN_INFERENCE_ASYNC = True


class DevelopmentConfig(BaseConfig):
    DEBUG = True


class TestingConfig(BaseConfig):
    TESTING = True
    # Tests run against in-memory SQLite; the models avoid Postgres-only types
    # so the same schema works on both.
    SQLALCHEMY_DATABASE_URI = "sqlite+pysqlite:///:memory:"
    SQLALCHEMY_ENGINE_OPTIONS = {}
    MODEL_BACKEND = "mock"
    RUN_INFERENCE_ASYNC = False  # deterministic: job finishes before the response
    RATELIMIT_ENABLED = False
    # At least 32 bytes, or PyJWT warns on every single token it signs.
    JWT_SECRET_KEY = "testing-secret-key-not-used-in-production-0123456789"


class ProductionConfig(BaseConfig):
    DEBUG = False


_CONFIGS = {
    "development": DevelopmentConfig,
    "testing": TestingConfig,
    "production": ProductionConfig,
}


def get_config(env: str | None = None):
    env = (env or os.getenv("APP_ENV", "development")).lower()
    return _CONFIGS.get(env, DevelopmentConfig)
