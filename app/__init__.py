"""Flask application factory."""

import logging

from flask import Flask, jsonify

from app.api import register_blueprints
from app.cli import register_cli
from app.config import get_config
from app.errors import register_error_handlers
from app.extensions import cors, db, jwt, limiter
from app.logging_config import configure_logging
from app.services.upload_service import configure_cloudinary
from app.tasks.queue import init_task_queue

logger = logging.getLogger(__name__)


def create_app(config_object=None) -> Flask:
    app = Flask(__name__)
    app.config.from_object(config_object or get_config())

    configure_logging(app)

    db.init_app(app)
    jwt.init_app(app)
    limiter.init_app(app)
    cors.init_app(
        app,
        resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}},
        supports_credentials=True,
    )

    configure_cloudinary(app)
    _register_jwt_handlers()
    register_error_handlers(app)
    register_blueprints(app)
    register_cli(app)

    if not app.config.get("TESTING"):
        init_task_queue(app)

    @app.get("/")
    def root():
        return jsonify(
            {
                "service": "Dent Detection API",
                "version": "1.0.0",
                "docs": "/api/v1/health",
                "api_base": "/api/v1",
            }
        )

    app.logger.info(
        "Application started",
        extra={
            "extra_fields": {
                "env": app.config.get("ENV_NAME", "unknown"),
                "model_backend": app.config.get("MODEL_BACKEND"),
                "async_inference": app.config.get("RUN_INFERENCE_ASYNC"),
            }
        },
    )
    return app


def _register_jwt_handlers() -> None:
    """Make JWT rejections use the same error envelope as everything else."""

    @jwt.unauthorized_loader
    def _missing_token(reason: str):
        return (
            jsonify({"error": {"code": "AUTHORIZATION_REQUIRED", "message": reason}}),
            401,
        )

    @jwt.invalid_token_loader
    def _invalid_token(reason: str):
        return jsonify({"error": {"code": "INVALID_TOKEN", "message": reason}}), 401

    @jwt.expired_token_loader
    def _expired_token(_header, _payload):
        return (
            jsonify(
                {"error": {"code": "TOKEN_EXPIRED", "message": "The token has expired."}}
            ),
            401,
        )

    @jwt.revoked_token_loader
    def _revoked_token(_header, _payload):
        return (
            jsonify({"error": {"code": "TOKEN_REVOKED", "message": "The token was revoked."}}),
            401,
        )
