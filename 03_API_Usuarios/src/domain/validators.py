"""Validadores puros del dominio de Usuarios/Roles (sin dependencias externas)."""
import re
import unicodedata

from src.domain.exceptions import ValidationError

EMOJI_PATTERN = re.compile(
    r"[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U00002300-\U000023FF"
    r"\U00002B00-\U00002BFF\uFE00-\uFE0F\u200D\u20E3\U0001F1E6-\U0001F1FF]"
)

EMAIL_PATTERN = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")


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


def validate_nombre_usuario(value, field: str = "nombre") -> str:
    if not isinstance(value, str):
        raise ValidationError(f"{field} debe ser texto")
    assert_no_emojis(value, field)
    cleaned = value.strip()
    if not cleaned:
        raise ValidationError(f"El {field} no puede estar vacío")
    if len(cleaned) < 2 or len(cleaned) > 120:
        raise ValidationError(f"{field} debe tener entre 2 y 120 caracteres")
    normalized = unicodedata.normalize("NFC", cleaned)
    if not all(ch.isalpha() or ch in " '-." for ch in normalized) or not any(ch.isalpha() for ch in normalized):
        raise ValidationError(
            f"{field} contiene caracteres inválidos (solo letras, espacios, '-', \"'\" y '.')"
        )
    return cleaned


def validate_correo(value, field: str = "correo") -> str:
    if not isinstance(value, str):
        raise ValidationError("Correo inválido")
    assert_no_emojis(value, field)
    cleaned = value.strip().lower()
    if not cleaned or len(cleaned) > 150 or not EMAIL_PATTERN.match(cleaned):
        raise ValidationError("Correo inválido")
    return cleaned


def validate_password_login(value, field: str = "password") -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field} es obligatorio")
    assert_no_emojis(value, field)
    return value


def validate_password_strict(value, field: str = "password") -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValidationError(f"{field} es obligatorio")
    assert_no_emojis(value, field)
    if len(value) < 6 or len(value) > 72:
        raise ValidationError("La contraseña debe tener entre 6 y 72 caracteres")
    return value


def validate_nombre_rol(value, field: str = "nombre") -> str:
    if not isinstance(value, str):
        raise ValidationError(f"{field} debe ser texto")
    assert_no_emojis(value, field)
    cleaned = value.strip()
    if not cleaned:
        raise ValidationError("El nombre del rol no puede estar vacío")
    if len(cleaned) < 2 or len(cleaned) > 50:
        raise ValidationError("El nombre del rol debe tener entre 2 y 50 caracteres")
    normalized = unicodedata.normalize("NFC", cleaned)
    if not all(ch.isalnum() or ch in " _-" for ch in normalized) or not any(ch.isalnum() for ch in normalized):
        raise ValidationError(
            "El nombre del rol solo puede contener letras, dígitos, espacios, '_' y '-'"
        )
    return cleaned


def validate_search_query(value, field: str = "q") -> str | None:
    if value is None:
        return None
    if not isinstance(value, str):
        raise ValidationError(f"{field} debe ser texto")
    assert_no_emojis(value, field)
    cleaned = value.strip()
    return cleaned or None
