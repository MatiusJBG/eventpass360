"""Puertos abstractos (repositorios y gateways)."""
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
    def transition_estado(
        self, compra_id: int, from_estado: str, to_estado: str, expected_version: Optional[int] = None
    ) -> bool: ...
    @abstractmethod
    def estadisticas(self) -> dict: ...
    @abstractmethod
    def anular(self, compra_id: int) -> Compra: ...


class EventosGateway(ABC):
    @abstractmethod
    def cotizar(self, items: list[dict]) -> dict: ...
    @abstractmethod
    def descontar(self, items: list[dict], auth_header: str = "") -> dict: ...
    @abstractmethod
    def restaurar(self, items: list[dict], auth_header: str = "") -> dict: ...


class PromocionesGateway(ABC):
    @abstractmethod
    def calcular(self, subtotal, cantidad_total: int) -> dict: ...


class FacturacionGateway(ABC):
    @abstractmethod
    def emitir(self, compra_id: int, cliente: dict, items: list[dict], totales: dict, auth_header: str = "") -> dict: ...
    @abstractmethod
    def buscar_por_compra(self, compra_id: int, auth_header: str = "") -> Optional[dict]: ...
    @abstractmethod
    def anular_por_compra(self, compra_id: int, auth_header: str = "") -> None: ...
