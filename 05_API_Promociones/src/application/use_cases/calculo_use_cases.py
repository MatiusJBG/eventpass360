"""Cálculo dinámico de descuento e IVA 15% (Decimal ROUND_HALF_UP)."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import math
import re

from src.domain.exceptions import ValidationError
from src.domain.repositories import PromocionRepository

MONEY = Decimal("0.01")
IVA_RATE = Decimal("0.15")
_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U00002300-\U000023FF"
    "\U00002B00-\U00002BFF\uFE00-\uFE0F\u200D\u20E3\U0001F1E6-\U0001F1FF]"
)
_DIGITS_RE = re.compile(r"^[0-9]+$")
_DECIMAL_RE = re.compile(r"^[+-]?\d+(?:\.\d+)?$")


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


def _check_no_emojis(value: str, field_name: str) -> None:
    if _EMOJI_RE.search(value):
        raise ValidationError(f"No se permiten emojis en el campo '{field_name}'")


def _parse_decimal(value, field_name: str) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise ValidationError(f"{field_name} inválido")
    if isinstance(value, str):
        _check_no_emojis(value, field_name)
        s = value.strip()
        if not _DECIMAL_RE.fullmatch(s):
            raise ValidationError(f"{field_name} inválido")
        try:
            d = Decimal(s)
        except InvalidOperation:
            raise ValidationError(f"{field_name} inválido")
    elif isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise ValidationError(f"{field_name} inválido")
        d = Decimal(str(value))
    elif isinstance(value, (int, Decimal)):
        d = Decimal(str(value))
    else:
        raise ValidationError(f"{field_name} inválido")
    if not d.is_finite():
        raise ValidationError(f"{field_name} inválido")
    return d


def _parse_positive_int(value, field_name: str) -> int:
    if isinstance(value, (bool, float)) or value is None:
        raise ValidationError(f"{field_name} inválido")
    if isinstance(value, str):
        _check_no_emojis(value, field_name)
        s = value.strip()
        if not _DIGITS_RE.fullmatch(s):
            raise ValidationError(f"{field_name} inválido")
        parsed = int(s)
    elif isinstance(value, int):
        parsed = value
    else:
        raise ValidationError(f"{field_name} inválido")
    if parsed < 1:
        raise ValidationError(f"{field_name} debe ser >= 1")
    return parsed


class CalcularPromocionUseCase:
    def __init__(self, repo: PromocionRepository):
        self.repo = repo

    def execute(self, subtotal=None, cantidad_total=None, items=None):
        if items is not None:
            if not isinstance(items, list) or not items:
                raise ValidationError("items debe ser una lista no vacía")
            total_sub = Decimal("0.00")
            total_qty = 0
            for item in items:
                if not isinstance(item, dict):
                    raise ValidationError("Cada item debe ser un objeto")
                qty = _parse_positive_int(item.get("cantidad"), "cantidad")
                precio = _parse_decimal(item.get("precio_unitario"), "precio_unitario")
                if precio < 0:
                    raise ValidationError("precio_unitario no puede ser negativo")
                total_sub += _money(precio * Decimal(qty))
                total_qty += qty
            sub = _money(total_sub)
            cantidad = total_qty
        else:
            sub = _money(_parse_decimal(subtotal, "subtotal"))
            if sub < 0:
                raise ValidationError("subtotal no puede ser negativo")
            cantidad = _parse_positive_int(cantidad_total, "cantidad_total")

        promo = self.repo.find_aplicable(cantidad)
        pct = promo.porcentaje if promo else Decimal("0")

        descuento = _money(sub * pct / Decimal("100"))
        base = _money(sub - descuento)
        iva = _money(base * IVA_RATE)
        total = _money(base + iva)

        return {
            "subtotal": float(sub),
            "cantidad_total": cantidad,
            "porcentaje_descuento": float(pct),
            "descuento": float(descuento),
            "base_imponible": float(base),
            "iva": float(iva),
            "total": float(total),
        }
