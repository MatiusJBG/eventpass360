"""Entidad pura de Entrada (ticket electrónico)."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Entrada:
    id: int
    compra_id: int
    detalle_compra_id: int
    evento_id: int
    codigo: str
    estado: str
    fecha_validacion: Optional[datetime]
    row_version: int = 1
    evento_nombre: str = ""
    tipo: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "compra_id": self.compra_id,
            "detalle_compra_id": self.detalle_compra_id,
            "evento_id": self.evento_id,
            "evento": self.evento_nombre,
            "tipo": self.tipo,
            "codigo": self.codigo,
            "estado": self.estado,
            "fecha_validacion": self.fecha_validacion.isoformat() if self.fecha_validacion else None,
            "row_version": self.row_version,
        }
