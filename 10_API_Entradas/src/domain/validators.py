"""Validadores de dominio."""
import re

from src.domain.exceptions import ValidationError

_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U00002300-\U000023FF"
    "\U00002B00-\U00002BFF\uFE00-\uFE0F\u200D\u20E3\U0001F1E6-\U0001F1FF]"
)
_CODIGO_RE = re.compile(r"^[A-Za-z0-9_-]{1,50}$")


def validate_codigo(value, field_name: str = "codigo") -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field_name} es obligatorio")
    codigo = value.strip()
    if _EMOJI_RE.search(codigo):
        raise ValidationError(f"No se permiten emojis en el campo '{field_name}'")
    if not _CODIGO_RE.fullmatch(codigo):
        raise ValidationError(f"{field_name} inválido")
    return codigo


def validate_positive_int(value, field_name: str) -> int:
    if isinstance(value, bool) or value is None:
        raise ValidationError(f"{field_name} debe ser un entero positivo")
    if isinstance(value, str):
        s = value.strip()
        if not s.isdigit():
            raise ValidationError(f"{field_name} debe ser un entero positivo")
        parsed = int(s)
    elif isinstance(value, int):
        parsed = value
    else:
        raise ValidationError(f"{field_name} debe ser un entero positivo")
    if parsed < 1:
        raise ValidationError(f"{field_name} debe ser un entero positivo")
    return parsed
