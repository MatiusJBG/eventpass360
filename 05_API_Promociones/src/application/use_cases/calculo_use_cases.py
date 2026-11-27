"""Cálculo dinámico de descuento e IVA 15% (Decimal ROUND_HALF_UP)."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP

from src.domain.exceptions import ValidationError
from src.domain.repositories import PromocionRepository

MONEY = Decimal("0.01")
IVA_RATE = Decimal("0.15")


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY, rounding=ROUND_HALF_UP)


class CalcularPromocionUseCase:
    def __init__(self, repo: PromocionRepository):
        self.repo = repo

    def execute(self, subtotal, cantidad_total):
        try:
            sub = _money(Decimal(str(subtotal)))
        except (InvalidOperation, ValueError, TypeError):
            raise ValidationError("subtotal inválido")
        if sub < 0:
            raise ValidationError("subtotal no puede ser negativo")
        try:
            cantidad = int(cantidad_total)
        except (TypeError, ValueError):
            raise ValidationError("cantidad_total inválida")
        if cantidad < 1:
            raise ValidationError("cantidad_total debe ser >= 1")

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
