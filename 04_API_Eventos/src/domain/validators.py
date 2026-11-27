"""Validadores puros del dominio de Eventos (sin dependencias externas)."""
from datetime import datetime
from decimal import Decimal, InvalidOperation
import re
from urllib.parse import urlparse

from src.domain.exceptions import ValidationError

EMOJI_PATTERN = re.compile(
    r"[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U00002300-\U000023FF"
    r"\U00002B00-\U00002BFF\uFE00-\uFE0F\u200D\u20E3\U0001F1E6-\U0001F1FF]"
)

ISO_DATE_PREFIX = re.compile(r"^\d{4}-\d{2}-\d{2}")

MAX_PRECIO = Decimal("999999.99")
MAX_STOCK = 1_000_000


def assert_no_emojis(value: str, field: str) -> str:
    if EMOJI_PATTERN.search(value):
        raise ValidationError(f"No se permiten emojis en el campo '{field}'")
    return value


def validate_positive_int(value, field: str) -> int:
    if isinstance(value, str):
        assert_no_emojis(value, field)
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValidationError(f"{field} debe ser un entero positivo")
    return value


def validate_stock(value, field: str = "stock") -> int:
    if isinstance(value, str):
        assert_no_emojis(value, field)
    if isinstance(value, bool) or not isinstance(value, int) or value < 0 or value > MAX_STOCK:
        raise ValidationError(f"{field} debe ser un entero entre 0 y {MAX_STOCK}")
    return value


def validate_precio(value, field: str = "precio") -> Decimal:
    if isinstance(value, str):
        assert_no_emojis(value, field)
        raw = value.strip()
        if not raw:
            raise ValidationError(f"{field} inválido")
    elif isinstance(value, bool) or value is None or not isinstance(value, (int, float, Decimal)):
        raise ValidationError(f"{field} inválido")
    else:
        raw = str(value)
    try:
        d = Decimal(raw)
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError(f"{field} inválido")
    if not d.is_finite():
        raise ValidationError(f"{field} debe ser un número finito")
    if d < Decimal("0") or d > MAX_PRECIO:
        raise ValidationError(f"{field} debe estar entre 0 y {MAX_PRECIO}")
    exp = d.as_tuple().exponent
    if not isinstance(exp, int) or exp < -2:
        raise ValidationError(f"{field} puede tener como máximo 2 decimales")
    return d


def _validate_text(value, field: str, min_len: int, max_len: int, allow_empty: bool = False) -> str:
    if not isinstance(value, str):
        raise ValidationError(f"{field} debe ser texto")
    assert_no_emojis(value, field)
    cleaned = value.strip()
    if not allow_empty and not cleaned:
        raise ValidationError(f"{field} no puede estar vacío")
    if len(cleaned) < min_len or len(cleaned) > max_len:
        if allow_empty:
            raise ValidationError(f"{field} no puede superar {max_len} caracteres")
        raise ValidationError(f"{field} debe tener entre {min_len} y {max_len} caracteres")
    return cleaned


def validate_categoria_nombre(value) -> str:
    return _validate_text(value, "nombre", 2, 100)


def validate_categoria_descripcion(value) -> str:
    if value is None:
        return ""
    return _validate_text(value, "descripcion", 0, 500, allow_empty=True)


def validate_evento_nombre(value) -> str:
    return _validate_text(value, "nombre", 2, 150)


def validate_evento_descripcion(value) -> str:
    return _validate_text(value, "descripcion", 5, 1000)


def validate_evento_lugar(value) -> str:
    return _validate_text(value, "lugar", 2, 200)


def validate_evento_fecha(value) -> datetime:
    if isinstance(value, datetime):
        return value
    if not isinstance(value, str):
        raise ValidationError("Fecha inválida (use formato ISO 8601)")
    assert_no_emojis(value, "fecha")
    cleaned = value.strip()
    if not cleaned or not ISO_DATE_PREFIX.match(cleaned):
        raise ValidationError("Fecha inválida (use formato ISO 8601)")
    try:
        return datetime.fromisoformat(cleaned.replace("Z", "+00:00"))
    except ValueError:
        raise ValidationError("Fecha inválida (use formato ISO 8601)")


def validate_evento_imagen_url(value) -> str:
    if not isinstance(value, str):
        raise ValidationError("imagen_url debe ser texto")
    assert_no_emojis(value, "imagen_url")
    cleaned = value.strip()
    if not cleaned or len(cleaned) > 2048 or any(ch.isspace() for ch in cleaned):
        raise ValidationError("imagen_url debe ser una URL http:// o https:// válida")
    parsed = urlparse(cleaned)
    if parsed.scheme not in ("http", "https") or not parsed.netloc:
        raise ValidationError("imagen_url debe ser una URL http:// o https:// válida")
    return cleaned


def validate_tipo_entrada_tipo(value) -> str:
    return _validate_text(value, "tipo", 2, 80)


def validate_search_query(value, field: str = "q") -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValidationError(f"{field} debe ser texto")
    assert_no_emojis(value, field)
    cleaned = value.strip()
    return cleaned or None
