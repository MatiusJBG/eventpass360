"""Validadores y parsers de payload para API Compras."""
import re

from src.domain.exceptions import ValidationError

MAX_CANTIDAD = 10_000
_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U00002300-\U000023FF"
    "\U00002B00-\U00002BFF\uFE00-\uFE0F\u200D\u20E3\U0001F1E6-\U0001F1FF]"
)
_DIGITS_RE = re.compile(r"^[0-9]+$")
_SOLICITUD_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,100}$")


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


def _parse_strict_positive_int(value, field: str, max_value: int | None = None) -> int:
    if isinstance(value, (bool, float)) or value is None:
        raise ValidationError(f"{field} debe ser un entero positivo")
    if isinstance(value, str):
        assert_no_emojis(value, field)
        s = value.strip()
        if not _DIGITS_RE.fullmatch(s):
            raise ValidationError(f"{field} debe ser un entero positivo")
        parsed = int(s)
    elif isinstance(value, int):
        parsed = value
    else:
        raise ValidationError(f"{field} debe ser un entero positivo")
    if parsed < 1:
        raise ValidationError(f"{field} debe ser mayor a 0")
    if max_value is not None and parsed > max_value:
        raise ValidationError(f"{field} no puede superar {max_value}")
    return parsed


def _validate_items_list(items) -> list[dict]:
    if not isinstance(items, list) or not items:
        raise ValidationError("Se requiere una lista no vacía de items")
    validated = []
    for idx, it in enumerate(items):
        if not isinstance(it, dict):
            raise ValidationError("Cada item debe ser un objeto")
        tid = _parse_strict_positive_int(it.get("tipo_entrada_id"), f"items[{idx}].tipo_entrada_id")
        qty = _parse_strict_positive_int(it.get("cantidad"), f"items[{idx}].cantidad", max_value=MAX_CANTIDAD)
        validated.append({"tipo_entrada_id": tid, "cantidad": qty})
    return validated


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
    _assert_no_emojis_recursive(data)
    require_fields(data, ["items"])
    return _validate_items_list(data["items"])


def parse_crear_compra_payload(raw) -> tuple[str, list]:
    data = parse_json_object(raw)
    _assert_no_emojis_recursive(data)
    require_fields(data, ["solicitud_id", "items"])
    solicitud_id = data["solicitud_id"]
    if not isinstance(solicitud_id, str) or not solicitud_id.strip():
        raise ValidationError("solicitud_id debe ser una cadena no vacía")
    assert_no_emojis(solicitud_id, "solicitud_id")
    solicitud_id = solicitud_id.strip()
    if not _SOLICITUD_ID_RE.fullmatch(solicitud_id):
        raise ValidationError("solicitud_id debe tener entre 1 y 100 caracteres alfanuméricos, '-' o '_'")
    items = _validate_items_list(data["items"])
    return solicitud_id, items


def parse_anular_compra_payload(raw) -> int | None:
    if raw is None:
        return None
    data = parse_json_object(raw)
    _assert_no_emojis_recursive(data)
    return parse_optional_row_version(data.get("row_version"))


def extract_auth_header(headers) -> str:
    return headers.get("Authorization", "")
