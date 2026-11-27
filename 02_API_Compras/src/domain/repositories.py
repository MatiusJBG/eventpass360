"""Puertos abstractos."""
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Optional

from src.domain.entities import Compra


class CompraRepository(ABC):
    @abstractmethod
    def find_by_solicitud_id(self, solicitud_id: str) -> Optional[Compra]: ...
    @abstractmethod
    def find_by_id(self, compra_id: int) -> Optional[Compra]: ...
    @abstractmethod
    def list_all(self, usuario_id: Optional[int] = None) -> list[Compra]: ...
    @abstractmethod
    def create(self, usuario_id: int, solicitud_id: str, subtotal: Decimal, descuento: Decimal,
               base_imponible: Decimal, iva: Decimal, total: Decimal, estado: str,
               detalles: list[dict]) -> Compra: ...
    @abstractmethod
    def update_estado(self, compra_id: int, estado: str) -> None: ...
    @abstractmethod
    def estadisticas(self) -> dict: ...
    @abstractmethod
    def anular(self, compra_id: int) -> Compra: ...
