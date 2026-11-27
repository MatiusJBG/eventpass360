"""Validadores y parsers de payload para API Compras."""
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


def parse_previsualizar_payload(raw) -> list:
    data = parse_json_object(raw)
    require_fields(data, ["items"])
    return data["items"]


def parse_crear_compra_payload(raw) -> tuple[str, list]:
    data = parse_json_object(raw)
    require_fields(data, ["solicitud_id", "items"])
    solicitud_id = data["solicitud_id"]
    if not isinstance(solicitud_id, str) or not solicitud_id.strip():
        raise ValidationError("solicitud_id debe ser una cadena no vacía")
    return solicitud_id.strip(), data["items"]


def extract_auth_header(headers) -> str:
    return headers.get("Authorization", "")
