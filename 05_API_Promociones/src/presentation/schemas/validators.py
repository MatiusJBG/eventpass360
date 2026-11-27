"""Validadores y parsers de payload para API Promociones."""
from src.application.use_cases.promocion_use_cases import UNSET
from src.domain.exceptions import ValidationError


def require_fields(data: dict, required: list[str]) -> None:
    for field in required:
        value = data.get(field)
        if value is None or (isinstance(value, str) and value.strip() == ""):
            raise ValidationError(f"Campo obligatorio: {field}")


def parse_json_object(raw) -> dict:
    if raw is None:
        return {}
    if not isinstance(raw, dict):
        raise ValidationError("El cuerpo JSON debe ser un objeto")
    return raw


def parse_create_promocion_payload(raw) -> tuple:
    data = parse_json_object(raw)
    require_fields(data, ["cantidad_min", "porcentaje"])
    return data.get("cantidad_min"), data.get("cantidad_max"), data.get("porcentaje")


def parse_update_promocion_payload(raw) -> dict:
    data = parse_json_object(raw)
    return {
        "cantidad_min": data["cantidad_min"] if "cantidad_min" in data else UNSET,
        "cantidad_max": data["cantidad_max"] if "cantidad_max" in data else UNSET,
        "porcentaje": data["porcentaje"] if "porcentaje" in data else UNSET,
        "estado": data["estado"] if "estado" in data else UNSET,
    }


def parse_calcular_payload(raw) -> dict:
    data = parse_json_object(raw)
    if "items" in data and data["items"] is not None:
        return {"items": data["items"]}
    require_fields(data, ["subtotal", "cantidad_total"])
    return {
        "subtotal": data.get("subtotal"),
        "cantidad_total": data.get("cantidad_total"),
    }
