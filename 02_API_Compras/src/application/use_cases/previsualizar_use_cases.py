"""Caso de uso de previsualización (cotización en vivo)."""
from src.domain.exceptions import ConflictError, ValidationError


def normalize_items(items) -> list[dict]:
    if not isinstance(items, list) or not items:
        raise ValidationError("Se requiere una lista no vacía de items")
    normalized = []
    for it in items:
        try:
            tid = int(it.get("tipo_entrada_id"))
            cantidad = int(it.get("cantidad"))
        except (TypeError, ValueError):
            raise ValidationError("tipo_entrada_id y cantidad deben ser enteros")
        if cantidad <= 0:
            raise ValidationError("La cantidad debe ser mayor a 0")
        normalized.append({"tipo_entrada_id": tid, "cantidad": cantidad})
    return normalized


class PrevisualizarCompraUseCase:
    def __init__(self, eventos_gw, promociones_gw):
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
