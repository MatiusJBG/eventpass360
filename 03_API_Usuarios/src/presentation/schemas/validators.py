"""Validadores de payload de entrada (-> HTTP 400 si inválido)."""
from src.domain.exceptions import ValidationError


def require_fields(data: dict, required: list[str]) -> None:
    for field in required:
        value = data.get(field)
        if value is None or (isinstance(value, str) and value.strip() == ""):
            raise ValidationError(f"Campo obligatorio: {field}")


def require_email(value: str) -> None:
    if not value or "@" not in value:
        raise ValidationError("Correo inválido")
