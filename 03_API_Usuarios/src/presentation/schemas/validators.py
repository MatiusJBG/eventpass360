"""Validadores y extracción de payload de entrada (-> HTTP 400 si inválido)."""
from src.domain.exceptions import ValidationError
from src.domain.validators import (
    assert_no_emojis,
    validate_correo,
    validate_nombre_rol,
    validate_nombre_usuario,
    validate_password_login,
    validate_password_strict,
    validate_positive_int,
    validate_search_query,
)


def get_json_body(request_obj) -> dict:
    data = request_obj.get_json(silent=True)
    if data is None:
        return {}
    if not isinstance(data, dict):
        raise ValidationError("El cuerpo JSON debe ser un objeto")
    return data


def require_fields(data: dict, required: list[str]) -> None:
    for field in required:
        value = data.get(field)
        if value is None or (isinstance(value, str) and value.strip() == ""):
            raise ValidationError(f"Campo obligatorio: {field}")


def require_non_empty_str(value, field: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field} debe ser un texto no vacío")
    assert_no_emojis(value, field)
    return value.strip()


def optional_non_empty_str(value, field: str) -> str | None:
    if value is None:
        return None
    return require_non_empty_str(value, field)


def require_nombre_usuario(value, field: str = "nombre") -> str:
    return validate_nombre_usuario(value, field)


def optional_nombre_usuario(value, field: str = "nombre") -> str | None:
    if value is None:
        return None
    return validate_nombre_usuario(value, field)


def require_nombre_rol(value, field: str = "nombre") -> str:
    return validate_nombre_rol(value, field)


def optional_nombre_rol(value, field: str = "nombre") -> str | None:
    if value is None:
        return None
    return validate_nombre_rol(value, field)


def require_email(value) -> str:
    return validate_correo(value, "correo")


def optional_email(value) -> str | None:
    if value is None:
        return None
    return validate_correo(value, "correo")


def require_positive_int(value, field: str) -> int:
    return validate_positive_int(value, field)


def optional_positive_int(value, field: str) -> int | None:
    if value is None:
        return None
    return validate_positive_int(value, field)


def optional_bool(value, field: str) -> bool | None:
    if value is None:
        return None
    if not isinstance(value, bool):
        raise ValidationError(f"{field} debe ser booleano")
    return value


def require_password_login(value) -> str:
    return validate_password_login(value, "password")


def require_password(value) -> str:
    return validate_password_strict(value, "password")


def optional_password(value) -> str | None:
    if value is None or value == "":
        return None
    return validate_password_strict(value, "password")


def optional_search_query(value, field: str = "q") -> str | None:
    return validate_search_query(value, field)
