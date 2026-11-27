"""Casos de uso de cotización y descuento/restauración atómica de stock."""
from src.domain.exceptions import ValidationError
from src.domain.repositories import StockRepository
from src.domain.validators import validate_positive_int


def _normalize_items(items) -> list[dict]:
    if not isinstance(items, list) or not items:
        raise ValidationError("Se requiere una lista no vacía de items")
    aggregated: dict[int, int] = {}
    for it in items:
        if not isinstance(it, dict):
            raise ValidationError("Cada item debe ser un objeto con tipo_entrada_id y cantidad")
        tid = validate_positive_int(it.get("tipo_entrada_id"), "tipo_entrada_id")
        cantidad = validate_positive_int(it.get("cantidad"), "cantidad")
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
