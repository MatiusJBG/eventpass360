"""Entidad pura de Factura."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Factura:
    id: int
    compra_id: int
    numero: str
    fecha: datetime
    estado: str
    xml: str = ""
    pdf_base64: str = ""
    usuario_id: Optional[int] = None
    row_version: int = 1

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "compra_id": self.compra_id,
            "numero": self.numero,
            "fecha": self.fecha.isoformat() if self.fecha else None,
            "estado": self.estado,
            "row_version": self.row_version,
        }
