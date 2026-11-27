"""Validadores y extracción de payload de entrada (-> HTTP 400 si inválido)."""
from src.domain.exceptions import ValidationError


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
    return value.strip()


def optional_non_empty_str(value, field: str) -> str | None:
    if value is None:
        return None
    return require_non_empty_str(value, field)


def require_email(value) -> str:
    if not isinstance(value, str):
        raise ValidationError("Correo inválido")
    normalized = value.strip().lower()
    if not normalized or "@" not in normalized:
        raise ValidationError("Correo inválido")
    return normalized


def require_positive_int(value, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValidationError(f"{field} debe ser un entero positivo")
    return value


def optional_positive_int(value, field: str) -> int | None:
    if value is None:
        return None
    return require_positive_int(value, field)


def optional_bool(value, field: str) -> bool | None:
    if value is None:
        return None
    if not isinstance(value, bool):
        raise ValidationError(f"{field} debe ser booleano")
    return value


def optional_password(value) -> str | None:
    if value is None or value == "":
        return None
    if not isinstance(value, str):
        raise ValidationError("password debe ser texto")
    return value
