"""Entidad pura de Promoción."""
from dataclasses import dataclass
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class Promocion:
    id: int
    cantidad_min: int
    cantidad_max: Optional[int]
    porcentaje: Decimal
    estado: bool

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "cantidad_min": self.cantidad_min,
            "cantidad_max": self.cantidad_max,
            "porcentaje": float(self.porcentaje),
            "estado": self.estado,
        }
