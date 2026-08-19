"""HTTP layer. Routes validate input, call a service, and serialise the result."""

from app.api.v1 import bp as v1_bp


def register_blueprints(app) -> None:
    app.register_blueprint(v1_bp)
