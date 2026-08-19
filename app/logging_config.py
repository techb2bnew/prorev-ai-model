"""Structured JSON logging with a per-request correlation id.

The correlation id is generated on each request and carried into the
background inference job, so one inspection can be traced end to end.
"""

import json
import logging
import sys
import uuid
from contextvars import ContextVar

from flask import g, has_request_context, request

_correlation_id: ContextVar[str | None] = ContextVar("correlation_id", default=None)


def set_correlation_id(value: str | None = None) -> str:
    cid = value or uuid.uuid4().hex[:12]
    _correlation_id.set(cid)
    return cid


def get_correlation_id() -> str | None:
    return _correlation_id.get()


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "timestamp": self.formatTime(record, "%Y-%m-%dT%H:%M:%S%z"),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        cid = get_correlation_id()
        if cid:
            entry["correlation_id"] = cid

        if has_request_context():
            entry["method"] = request.method
            entry["path"] = request.path

        # Anything passed via logger.info(..., extra={"extra_fields": {...}}).
        extra = getattr(record, "extra_fields", None)
        if isinstance(extra, dict):
            entry.update(extra)

        if record.exc_info:
            entry["exception"] = self.formatException(record.exc_info)

        return json.dumps(entry, default=str)


def configure_logging(app) -> None:
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(JsonFormatter())

    level = getattr(logging, app.config.get("LOG_LEVEL", "INFO").upper(), logging.INFO)

    root = logging.getLogger()
    root.handlers = [handler]
    root.setLevel(level)

    # app.logger propagates to root, so giving it its own copy of the handler
    # would print every line twice. Set the level only and let root emit.
    app.logger.handlers = []
    app.logger.setLevel(level)

    # Werkzeug's own access log is noisy next to our structured lines.
    logging.getLogger("werkzeug").setLevel(logging.WARNING)

    @app.before_request
    def _start_request():
        incoming = request.headers.get("X-Correlation-Id")
        g.correlation_id = set_correlation_id(incoming)

    @app.after_request
    def _tag_response(response):
        cid = get_correlation_id()
        if cid:
            response.headers["X-Correlation-Id"] = cid
        return response
