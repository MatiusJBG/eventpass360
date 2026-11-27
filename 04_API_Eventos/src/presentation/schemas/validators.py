"""Validadores centralizados de payload y query params (-> HTTP 400)."""
from decimal import Decimal

from src.domain.exceptions import ValidationError
from src.domain.validators import (
    assert_no_emojis,
    validate_categoria_descripcion,
    validate_categoria_nombre,
    validate_evento_descripcion,
    validate_evento_fecha,
    validate_evento_imagen_url,
    validate_evento_lugar,
    validate_evento_nombre,
    validate_positive_int,
    validate_precio,
    validate_search_query,
    validate_stock,
    validate_tipo_entrada_tipo,
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


def optional_str(value, field: str) -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValidationError(f"{field} debe ser texto")
    assert_no_emojis(value, field)
    return value


def require_categoria_nombre(value) -> str:
    return validate_categoria_nombre(value)


def optional_categoria_nombre(value) -> str | None:
    if value is None:
        return None
    return validate_categoria_nombre(value)


def optional_categoria_descripcion(value) -> str | None:
    if value is None:
        return None
    return validate_categoria_descripcion(value)


def require_evento_nombre(value) -> str:
    return validate_evento_nombre(value)


def optional_evento_nombre(value) -> str | None:
    if value is None:
        return None
    return validate_evento_nombre(value)


def require_evento_descripcion(value) -> str:
    return validate_evento_descripcion(value)


def optional_evento_descripcion(value) -> str | None:
    if value is None:
        return None
    return validate_evento_descripcion(value)


def require_evento_lugar(value) -> str:
    return validate_evento_lugar(value)


def optional_evento_lugar(value) -> str | None:
    if value is None:
        return None
    return validate_evento_lugar(value)


def require_evento_fecha(value):
    return validate_evento_fecha(value)


def optional_evento_fecha(value):
    if value is None:
        return None
    return validate_evento_fecha(value)


def require_evento_imagen_url(value) -> str:
    return validate_evento_imagen_url(value)


def optional_evento_imagen_url(value) -> str | None:
    if value is None:
        return None
    return validate_evento_imagen_url(value)


def require_tipo_entrada_tipo(value) -> str:
    return validate_tipo_entrada_tipo(value)


def optional_tipo_entrada_tipo(value) -> str | None:
    if value is None:
        return None
    return validate_tipo_entrada_tipo(value)


def require_precio(value) -> Decimal:
    return validate_precio(value, "precio")


def optional_precio(value) -> Decimal | None:
    if value is None:
        return None
    return validate_precio(value, "precio")


def require_positive_int(value, field: str) -> int:
    return validate_positive_int(value, field)


def optional_positive_int(value, field: str) -> int | None:
    if value is None:
        return None
    return validate_positive_int(value, field)


def optional_non_negative_int(value, field: str) -> int | None:
    if value is None:
        return None
    return validate_stock(value, field)


def parse_optional_query_positive_int(value, field: str) -> int | None:
    if value in (None, ""):
        return None
    if isinstance(value, bool):
        raise ValidationError(f"{field} debe ser un entero positivo")
    if isinstance(value, str):
        assert_no_emojis(value, field)
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


def optional_search_query(value, field: str = "q") -> str | None:
    return validate_search_query(value, field)


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
