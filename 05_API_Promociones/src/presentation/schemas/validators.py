"""Validadores y parsers de payload para API Promociones."""
from decimal import Decimal, InvalidOperation
import math
import re

from src.application.use_cases.promocion_use_cases import UNSET
from src.domain.exceptions import ValidationError

MAX_CANTIDAD = 1_000_000
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
            _assert_no_emojis_recursive(v, str(k))
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


def parse_strict_int(value, field: str, min_value: int = 1, max_value: int | None = None) -> int:
    if isinstance(value, (bool, float)) or value is None:
        raise ValidationError(f"{field} debe ser un entero válido")
    if isinstance(value, str):
        assert_no_emojis(value, field)
        s = value.strip()
        if not _DIGITS_RE.fullmatch(s):
            raise ValidationError(f"{field} debe ser un entero válido")
        parsed = int(s)
    elif isinstance(value, int):
        parsed = value
    else:
        raise ValidationError(f"{field} debe ser un entero válido")
    if parsed < min_value:
        raise ValidationError(f"{field} debe ser >= {min_value}")
    if max_value is not None and parsed > max_value:
        raise ValidationError(f"{field} debe ser <= {max_value}")
    return parsed


def parse_strict_decimal(
    value,
    field: str,
    min_value: Decimal | None = Decimal("0"),
    max_value: Decimal | None = None,
    max_decimals: int | None = None,
) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise ValidationError(f"{field} inválido")
    if isinstance(value, str):
        assert_no_emojis(value, field)
        s = value.strip()
        if not _DECIMAL_RE.fullmatch(s):
            raise ValidationError(f"{field} inválido")
        try:
            d = Decimal(s)
        except InvalidOperation:
            raise ValidationError(f"{field} inválido")
    elif isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise ValidationError(f"{field} inválido")
        d = Decimal(str(value))
    elif isinstance(value, (int, Decimal)):
        d = Decimal(str(value))
    else:
        raise ValidationError(f"{field} inválido")
    if not d.is_finite():
        raise ValidationError(f"{field} inválido")
    if min_value is not None and d < min_value:
        raise ValidationError(f"{field} no puede ser menor que {min_value}")
    if max_value is not None and d > max_value:
        raise ValidationError(f"{field} no puede ser mayor que {max_value}")
    if max_decimals is not None and d.as_tuple().exponent < -max_decimals:
        raise ValidationError(f"{field} admite máximo {max_decimals} decimales")
    return d


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
    _assert_no_emojis_recursive(data)
    require_fields(data, ["cantidad_min", "porcentaje"])
    cmin = parse_strict_int(data.get("cantidad_min"), "cantidad_min", min_value=1, max_value=MAX_CANTIDAD)
    raw_max = data.get("cantidad_max")
    if raw_max in (None, ""):
        cmax = None
    else:
        cmax = parse_strict_int(raw_max, "cantidad_max", min_value=cmin, max_value=MAX_CANTIDAD)
    pct = parse_strict_decimal(
        data.get("porcentaje"),
        "porcentaje",
        min_value=Decimal("0"),
        max_value=Decimal("100"),
        max_decimals=2,
    )
    return cmin, cmax, pct


def parse_update_promocion_payload(raw) -> dict:
    data = parse_json_object(raw)
    _assert_no_emojis_recursive(data)
    expected_version = parse_optional_row_version(data.get("row_version"))
    cantidad_min = (
        parse_strict_int(data["cantidad_min"], "cantidad_min", min_value=1, max_value=MAX_CANTIDAD)
        if "cantidad_min" in data
        else UNSET
    )
    if "cantidad_max" in data:
        raw_max = data["cantidad_max"]
        cantidad_max = (
            None
            if raw_max in (None, "")
            else parse_strict_int(raw_max, "cantidad_max", min_value=1, max_value=MAX_CANTIDAD)
        )
    else:
        cantidad_max = UNSET
    porcentaje = (
        parse_strict_decimal(
            data["porcentaje"],
            "porcentaje",
            min_value=Decimal("0"),
            max_value=Decimal("100"),
            max_decimals=2,
        )
        if "porcentaje" in data
        else UNSET
    )
    estado = data["estado"] if "estado" in data else UNSET
    return {
        "cantidad_min": cantidad_min,
        "cantidad_max": cantidad_max,
        "porcentaje": porcentaje,
        "estado": estado,
        "expected_version": expected_version,
    }


def parse_calcular_payload(raw) -> dict:
    data = parse_json_object(raw)
    _assert_no_emojis_recursive(data)
    if "items" in data and data["items"] is not None:
        items = data["items"]
        if not isinstance(items, list) or not items:
            raise ValidationError("items debe ser una lista no vacía")
        parsed_items = []
        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                raise ValidationError("Cada item debe ser un objeto")
            qty = parse_strict_int(item.get("cantidad"), f"items[{idx}].cantidad", min_value=1)
            precio = parse_strict_decimal(item.get("precio_unitario"), f"items[{idx}].precio_unitario", min_value=Decimal("0"))
            parsed_items.append({"cantidad": qty, "precio_unitario": precio})
        return {"items": parsed_items}
    require_fields(data, ["subtotal", "cantidad_total"])
    subtotal = parse_strict_decimal(data.get("subtotal"), "subtotal", min_value=Decimal("0"))
    cantidad_total = parse_strict_int(data.get("cantidad_total"), "cantidad_total", min_value=1)
    return {
        "subtotal": subtotal,
        "cantidad_total": cantidad_total,
    }
