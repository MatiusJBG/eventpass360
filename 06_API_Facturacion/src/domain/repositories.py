"""Puertos abstractos."""
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Optional

from src.domain.entities import Factura


class FacturaRepository(ABC):
    @abstractmethod
    def find_by_compra_id(self, compra_id: int) -> Optional[Factura]: ...
    @abstractmethod
    def find_by_id(self, factura_id: int) -> Optional[Factura]: ...
    @abstractmethod
    def list_all(self, compra_id: Optional[int] = None) -> list[Factura]: ...
    @abstractmethod
    def next_numero(self) -> str: ...
    @abstractmethod
    def create(self, compra_id: int, numero: str, fecha: datetime, xml: str, pdf_base64: str) -> Factura: ...
    @abstractmethod
    def anular(self, factura_id: int) -> Factura: ...
