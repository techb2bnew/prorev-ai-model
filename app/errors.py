"""Application error types and the handlers that turn them into a uniform envelope.

Every error response looks the same:
    {"error": {"code": "...", "message": "...", "details": {...}}}
"""

import logging

from flask import jsonify
from werkzeug.exceptions import HTTPException

logger = logging.getLogger(__name__)


class AppError(Exception):
    """Base class for errors we raise deliberately."""

    status_code = 400
    code = "BAD_REQUEST"
    message = "Request could not be processed."

    def __init__(self, message: str | None = None, details: dict | None = None):
        super().__init__(message or self.message)
        if message:
            self.message = message
        self.details = details or {}

    def to_response(self):
        payload = {"error": {"code": self.code, "message": self.message}}
        if self.details:
            payload["error"]["details"] = self.details
        return jsonify(payload), self.status_code


class ValidationError(AppError):
    status_code = 422
    code = "VALIDATION_ERROR"
    message = "The request payload is invalid."


class AuthenticationError(AppError):
    status_code = 401
    code = "AUTHENTICATION_FAILED"
    message = "Invalid email or password."


class PermissionDeniedError(AppError):
    status_code = 403
    code = "PERMISSION_DENIED"
    message = "You do not have access to this resource."


class NotFoundError(AppError):
    status_code = 404
    code = "NOT_FOUND"
    message = "Resource not found."


class ConflictError(AppError):
    status_code = 409
    code = "CONFLICT"
    message = "Resource already exists."


class ConfigurationError(AppError):
    status_code = 500
    code = "CONFIGURATION_ERROR"
    message = "The server is not configured correctly."


class ImageUnreachableError(AppError):
    status_code = 422
    code = "IMAGE_UNREACHABLE"
    message = "The image could not be downloaded or decoded."


class InferenceError(AppError):
    status_code = 500
    code = "INFERENCE_FAILED"
    message = "The damage detection model failed to process the image."


def register_error_handlers(app) -> None:
    @app.errorhandler(AppError)
    def _handle_app_error(exc: AppError):
        return exc.to_response()

    @app.errorhandler(HTTPException)
    def _handle_http_error(exc: HTTPException):
        code = (exc.name or "HTTP_ERROR").upper().replace(" ", "_")
        return (
            jsonify({"error": {"code": code, "message": exc.description}}),
            exc.code or 500,
        )

    @app.errorhandler(Exception)
    def _handle_unexpected(exc: Exception):
        logger.exception("Unhandled exception: %s", exc)
        return (
            jsonify(
                {
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "An unexpected error occurred.",
                    }
                }
            ),
            500,
        )
