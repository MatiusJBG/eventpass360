"""Validadores y parsers de payload para API Facturación."""
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


def parse_positive_int(value, field_name: str) -> int:
    if isinstance(value, (bool, float)) or value is None:
        raise ValidationError(f"{field_name} debe ser un entero positivo")
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field_name} debe ser un entero positivo")
    if parsed < 1:
        raise ValidationError(f"{field_name} debe ser un entero positivo")
    return parsed


def parse_optional_positive_int(value, field_name: str) -> int | None:
    if value in (None, ""):
        return None
    return parse_positive_int(value, field_name)


def parse_emitir_factura_payload(raw) -> dict:
    data = parse_json_object(raw)
    require_fields(data, ["compra_id"])
    return {
        "compra_id": parse_positive_int(data.get("compra_id"), "compra_id"),
        "cliente": data.get("cliente") if data.get("cliente") is not None else {},
        "items": data.get("items") if data.get("items") is not None else [],
        "totales": data.get("totales") if data.get("totales") is not None else {},
    }
