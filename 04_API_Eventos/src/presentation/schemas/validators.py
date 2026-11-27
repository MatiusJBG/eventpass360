"""Validadores centralizados de payload y query params (-> HTTP 400)."""
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


def optional_str(value, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValidationError(f"{field} debe ser texto")
    return value


def require_positive_int(value, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValidationError(f"{field} debe ser un entero positivo")
    return value


def optional_positive_int(value, field: str) -> int | None:
    if value is None:
        return None
    return require_positive_int(value, field)


def optional_non_negative_int(value, field: str) -> int | None:
    if value is None:
        return None
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValidationError(f"{field} debe ser un entero mayor o igual a 0")
    return value


def parse_optional_query_positive_int(value, field: str) -> int | None:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        raise ValidationError(f"{field} debe ser un entero positivo")
    if isinstance(value, str):
        raw = value.strip()
        if not raw.isdigit():
            raise ValidationError(f"{field} debe ser un entero positivo")
        parsed = int(raw)
    elif isinstance(value, int):
        parsed = value
    else:
        raise ValidationError(f"{field} debe ser un entero positivo")
    if parsed <= 0:
        raise ValidationError(f"{field} debe ser un entero positivo")
    return parsed


def optional_bool(value, field: str) -> bool | None:
    if value is None:
        return None
    if not isinstance(value, bool):
        raise ValidationError(f"{field} debe ser booleano")
    return value


def parse_query_bool(value) -> bool:
    return str(value).lower() in ("true", "1", "yes")


def require_items_list(data: dict) -> list:
    items = data.get("items")
    if not isinstance(items, list) or not items:
        raise ValidationError("Se requiere una lista no vacía de items")
    return items
