"""Casos de uso de cotización y descuento/restauración atómica de stock."""
from src.domain.exceptions import ValidationError
from src.domain.repositories import StockRepository


def _normalize_items(items) -> list[dict]:
    if not isinstance(items, list) or not items:
        raise ValidationError("Se requiere una lista no vacía de items")
    aggregated: dict[int, int] = {}
    for it in items:
        if not isinstance(it, dict):
            raise ValidationError("Cada item debe ser un objeto con tipo_entrada_id y cantidad")
        tid = it.get("tipo_entrada_id")
        cantidad = it.get("cantidad")
        if isinstance(tid, bool) or not isinstance(tid, int) or tid <= 0:
            raise ValidationError("tipo_entrada_id debe ser un entero positivo")
        if isinstance(cantidad, bool) or not isinstance(cantidad, int) or cantidad <= 0:
            raise ValidationError("cantidad debe ser un entero positivo")
        aggregated[tid] = aggregated.get(tid, 0) + cantidad
    return [{"tipo_entrada_id": tid, "cantidad": cant} for tid, cant in aggregated.items()]


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
