"""Caso de uso de previsualización (cotización en vivo)."""
import re

from src.domain.exceptions import ConflictError, ValidationError
from src.domain.repositories import EventosGateway, PromocionesGateway

MAX_CANTIDAD = 10_000
_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U00002300-\U000023FF"
    "\U00002B00-\U00002BFF\uFE00-\uFE0F\u200D\u20E3\U0001F1E6-\U0001F1FF]"
)
_DIGITS_RE = re.compile(r"^[0-9]+$")


def _parse_positive_int(value, field_name: str, max_value: int | None = None) -> int:
    if isinstance(value, (bool, float)) or value is None:
        raise ValidationError(f"{field_name} debe ser un entero positivo")
    if isinstance(value, str):
        if _EMOJI_RE.search(value):
            raise ValidationError(f"No se permiten emojis en el campo '{field_name}'")
        s = value.strip()
        if not _DIGITS_RE.fullmatch(s):
            raise ValidationError(f"{field_name} debe ser un entero positivo")
        parsed = int(s)
    elif isinstance(value, int):
        parsed = value
    else:
        raise ValidationError(f"{field_name} debe ser un entero positivo")
    if parsed <= 0:
        raise ValidationError(f"{field_name} debe ser mayor a 0")
    if max_value is not None and parsed > max_value:
        raise ValidationError(f"{field_name} no puede superar {max_value}")
    return parsed


def normalize_items(items) -> list[dict]:
    if not isinstance(items, list) or not items:
        raise ValidationError("Se requiere una lista no vacía de items")
    aggregated: dict[int, int] = {}
    for it in items:
        if not isinstance(it, dict):
            raise ValidationError("Cada item debe ser un objeto")
        tid = _parse_positive_int(it.get("tipo_entrada_id"), "tipo_entrada_id")
        cantidad = _parse_positive_int(it.get("cantidad"), "cantidad", max_value=MAX_CANTIDAD)
        new_qty = aggregated.get(tid, 0) + cantidad
        if new_qty > MAX_CANTIDAD:
            raise ValidationError(f"cantidad acumulada no puede superar {MAX_CANTIDAD}")
        aggregated[tid] = new_qty
    return [{"tipo_entrada_id": tid, "cantidad": qty} for tid, qty in aggregated.items()]


class PrevisualizarCompraUseCase:
    def __init__(self, eventos_gw: EventosGateway, promociones_gw: PromocionesGateway):
        self.eventos_gw = eventos_gw
        self.promociones_gw = promociones_gw

    def execute(self, items):
        normalized = normalize_items(items)
        cotizacion = self.eventos_gw.cotizar(normalized)
        cot_items = cotizacion.get("items", [])
        if not all(it.get("disponible") for it in cot_items):
            raise ConflictError("Stock insuficiente para uno o más items")
        subtotal = cotizacion.get("subtotal_total", 0)
        cantidad_total = sum(it["cantidad"] for it in normalized)
        calculo = self.promociones_gw.calcular(subtotal, cantidad_total)
        return {
            "items": cot_items,
            "subtotal": calculo["subtotal"],
            "cantidad_total": cantidad_total,
            "porcentaje_descuento": calculo["porcentaje_descuento"],
            "descuento": calculo["descuento"],
            "base_imponible": calculo["base_imponible"],
            "iva": calculo["iva"],
            "total": calculo["total"],
        }
