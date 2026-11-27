"""Validadores y parsers de payload para API Facturación."""
from decimal import Decimal, InvalidOperation
import math
import re

from src.domain.exceptions import ValidationError

_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U00002300-\U000023FF"
    "\U00002B00-\U00002BFF\uFE00-\uFE0F\u200D\u20E3\U0001F1E6-\U0001F1FF]"
)
_DIGITS_RE = re.compile(r"^[0-9]+$")
_DECIMAL_RE = re.compile(r"^[+-]?\d+(?:\.\d+)?$")


def assert_no_emojis(value: str, field: str) -> None:
    if isinstance(value, str) and _EMOJI_RE.search(value):
        raise ValidationError(f"No se permiten emojis en el campo '{field}'")


def _assert_no_emojis_recursive(obj, field: str = "body") -> None:
    if isinstance(obj, str):
        assert_no_emojis(obj, field)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(k, str):
                assert_no_emojis(k, k)
            child_field = f"{field}.{k}" if field != "body" else str(k)
            _assert_no_emojis_recursive(v, child_field)
    elif isinstance(obj, list):
        for idx, item in enumerate(obj):
            _assert_no_emojis_recursive(item, f"{field}[{idx}]")


def parse_optional_row_version(value) -> int | None:
    if value is None:
        return None
    if isinstance(value, (bool, float)):
        raise ValidationError("row_version debe ser un entero positivo")
    if isinstance(value, str):
        assert_no_emojis(value, "row_version")
        s = value.strip()
        if not _DIGITS_RE.fullmatch(s):
            raise ValidationError("row_version debe ser un entero positivo")
        parsed = int(s)
    elif isinstance(value, int):
        parsed = value
    else:
        raise ValidationError("row_version debe ser un entero positivo")
    if parsed < 1:
        raise ValidationError("row_version debe ser un entero positivo")
    return parsed


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
    if isinstance(value, str):
        assert_no_emojis(value, field_name)
        s = value.strip()
        if not _DIGITS_RE.fullmatch(s):
            raise ValidationError(f"{field_name} debe ser un entero positivo")
        parsed = int(s)
    elif isinstance(value, int):
        parsed = value
    else:
        raise ValidationError(f"{field_name} debe ser un entero positivo")
    if parsed < 1:
        raise ValidationError(f"{field_name} debe ser un entero positivo")
    return parsed


def parse_optional_positive_int(value, field_name: str) -> int | None:
    if value in (None, ""):
        return None
    return parse_positive_int(value, field_name)


def parse_non_negative_decimal(value, field_name: str) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise ValidationError(f"{field_name} debe ser un monto válido >= 0")
    if isinstance(value, str):
        assert_no_emojis(value, field_name)
        s = value.strip()
        if not _DECIMAL_RE.fullmatch(s):
            raise ValidationError(f"{field_name} debe ser un monto válido >= 0")
        try:
            d = Decimal(s)
        except InvalidOperation:
            raise ValidationError(f"{field_name} debe ser un monto válido >= 0")
    elif isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise ValidationError(f"{field_name} debe ser un monto válido >= 0")
        d = Decimal(str(value))
    elif isinstance(value, (int, Decimal)):
        d = Decimal(str(value))
    else:
        raise ValidationError(f"{field_name} debe ser un monto válido >= 0")
    if not d.is_finite() or d < 0:
        raise ValidationError(f"{field_name} debe ser un monto válido >= 0")
    return d


def parse_emitir_factura_payload(raw) -> dict:
    data = parse_json_object(raw)
    _assert_no_emojis_recursive(data)
    require_fields(data, ["compra_id"])
    compra_id = parse_positive_int(data.get("compra_id"), "compra_id")

    cliente = data.get("cliente") if data.get("cliente") is not None else {}
    if not isinstance(cliente, dict):
        raise ValidationError("cliente debe ser un objeto")
    for field in ("nombre", "correo"):
        val = cliente.get(field)
        if val is not None:
            if not isinstance(val, str):
                raise ValidationError(f"cliente.{field} debe ser una cadena")
            assert_no_emojis(val, f"cliente.{field}")
    if "id" in cliente and cliente["id"] is not None:
        parse_positive_int(cliente["id"], "cliente.id")

    items = data.get("items") if data.get("items") is not None else []
    if not isinstance(items, list) or not items:
        raise ValidationError("items no puede estar vacío")
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValidationError("Cada item debe ser un objeto")
        desc = item.get("descripcion")
        if desc is not None:
            if not isinstance(desc, str):
                raise ValidationError(f"items[{idx}].descripcion debe ser una cadena")
            assert_no_emojis(desc, f"items[{idx}].descripcion")
        parse_positive_int(item.get("cantidad"), f"items[{idx}].cantidad")
        if "precio_unitario" in item:
            parse_non_negative_decimal(item["precio_unitario"], f"items[{idx}].precio_unitario")
        if "subtotal" in item:
            parse_non_negative_decimal(item["subtotal"], f"items[{idx}].subtotal")

    totales = data.get("totales") if data.get("totales") is not None else {}
    if not isinstance(totales, dict):
        raise ValidationError("totales debe ser un objeto")
    for key in ("subtotal", "descuento", "base_imponible", "iva", "total"):
        if key in totales:
            parse_non_negative_decimal(totales[key], f"totales.{key}")

    return {
        "compra_id": compra_id,
        "cliente": cliente,
        "items": items,
        "totales": totales,
    }


def parse_anular_factura_payload(raw) -> int | None:
    if raw is None:
        return None
    data = parse_json_object(raw)
    _assert_no_emojis_recursive(data)
    return parse_optional_row_version(data.get("row_version"))
