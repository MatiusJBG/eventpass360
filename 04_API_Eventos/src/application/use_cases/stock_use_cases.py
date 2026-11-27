"""Casos de uso de cotización y descuento/restauración atómica de stock."""
from src.domain.exceptions import ValidationError
from src.domain.repositories import StockRepository


def _normalize_items(items):
    if not isinstance(items, list) or not items:
        raise ValidationError("Se requiere una lista no vacía de items")
    normalized = []
    for it in items:
        tid = it.get("tipo_entrada_id")
        cantidad = it.get("cantidad")
        try:
            tid = int(tid)
            cantidad = int(cantidad)
        except (TypeError, ValueError):
            raise ValidationError("tipo_entrada_id y cantidad deben ser enteros")
        if cantidad <= 0:
            raise ValidationError("La cantidad debe ser mayor a 0")
        normalized.append({"tipo_entrada_id": tid, "cantidad": cantidad})
    return normalized


class CotizarStockUseCase:
    def __init__(self, repo: StockRepository):
        self.repo = repo

    def execute(self, items):
        return self.repo.cotizar(_normalize_items(items))


class DescontarStockUseCase:
    def __init__(self, repo: StockRepository):
        self.repo = repo

    def execute(self, items):
        self.repo.descontar(_normalize_items(items))
        return {"message": "Stock descontado"}


class RestaurarStockUseCase:
    def __init__(self, repo: StockRepository):
        self.repo = repo

    def execute(self, items):
        self.repo.restaurar(_normalize_items(items))
        return {"message": "Stock restaurado"}
