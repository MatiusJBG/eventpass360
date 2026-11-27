"""Middleware JWT (401) y rol (403)."""
from functools import wraps

import jwt
from flask import current_app, g, request

from src.domain.exceptions import ForbiddenError, UnauthorizedError


def _decode_token() -> dict:
    header = request.headers.get("Authorization", "")
    if not header.startswith("Bearer "):
        raise UnauthorizedError("Token ausente o malformado")
    token = header[7:]
    secret = current_app.config["SETTINGS"].jwt_secret_key
    try:
        return jwt.decode(token, secret, algorithms=["HS256"])
    except jwt.ExpiredSignatureError:
        raise UnauthorizedError("Token expirado")
    except jwt.InvalidTokenError:
        raise UnauthorizedError("Token inválido")


def require_auth(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        g.current_user = _decode_token()
        return fn(*args, **kwargs)
    return wrapper


def require_role(role: str):
    def decorator(fn):
        @wraps(fn)
        @require_auth
        def wrapper(*args, **kwargs):
            if g.current_user.get("rol") != role:
                raise ForbiddenError("Acceso denegado: se requiere rol " + role)
            return fn(*args, **kwargs)
        return wrapper
    return decorator
