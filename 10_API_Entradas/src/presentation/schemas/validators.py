"""Validadores de payload de entrada."""
from src.domain.exceptions import ValidationError
from src.domain.validators import validate_positive_int


def _require_body(data):
    if not isinstance(data, dict):
        raise ValidationError("Cuerpo JSON inválido")
    return data


def parse_generar_payload(data):
    data = _require_body(data)
    compra_id = data.get("compra_id")
    if compra_id is None:
        raise ValidationError("compra_id es obligatorio")
    return {"compra_id": compra_id}


def parse_validar_payload(data):
    data = _require_body(data)
    codigo = data.get("codigo")
    evento_id = data.get("evento_id")
    if codigo is None:
        raise ValidationError("codigo es obligatorio")
    if evento_id is None:
        raise ValidationError("evento_id es obligatorio")
    return {"codigo": codigo, "evento_id": evento_id}


def parse_optional_positive_int(value, field_name):
    if value is None or value == "":
        return None
    return validate_positive_int(value, field_name)
