"""Pydantic request schemas and the decorator that applies them."""

from functools import wraps

from flask import request
from pydantic import BaseModel, ValidationError as PydanticValidationError

from app.errors import ValidationError


def validate_body(schema: type[BaseModel]):
    """Parse and validate the JSON body, passing the model in as `payload`.

    Keeps validation out of the view functions and guarantees a uniform 422
    error shape for every endpoint.
    """

    def decorator(view):
        @wraps(view)
        def wrapper(*args, **kwargs):
            body = request.get_json(silent=True)
            if body is None:
                raise ValidationError("A JSON request body is required.")
            try:
                payload = schema.model_validate(body)
            except PydanticValidationError as exc:
                raise ValidationError(
                    "The request payload is invalid.",
                    details={
                        "fields": [
                            {
                                "field": ".".join(str(part) for part in error["loc"]),
                                "message": error["msg"],
                            }
                            for error in exc.errors()
                        ]
                    },
                ) from exc
            return view(*args, payload=payload, **kwargs)

        return wrapper

    return decorator
