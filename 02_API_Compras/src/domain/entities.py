"""Entidades puras del dominio de Compras."""
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal


@dataclass(frozen=True)
class DetalleCompra:
    id: int
    compra_id: int
    tipo_entrada_id: int
    cantidad: int
    precio_unitario: Decimal
    subtotal: Decimal
    tipo: str = ""
    evento_nombre: str = ""

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "tipo_entrada_id": self.tipo_entrada_id,
            "tipo": self.tipo,
            "evento": self.evento_nombre,
            "cantidad": self.cantidad,
            "precio_unitario": float(self.precio_unitario),
            "subtotal": float(self.subtotal),
        }


@dataclass(frozen=True)
class Compra:
    id: int
    usuario_id: int
    solicitud_id: str
    fecha: datetime
    subtotal: Decimal
    descuento: Decimal
    base_imponible: Decimal
    iva: Decimal
    total: Decimal
    estado: str
    usuario_nombre: str = ""
    usuario_correo: str = ""
    detalles: list = field(default_factory=list)
    row_version: int = 1

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "usuario_id": self.usuario_id,
            "usuario_nombre": self.usuario_nombre,
            "usuario_correo": self.usuario_correo,
            "solicitud_id": self.solicitud_id,
            "fecha": self.fecha.isoformat() if self.fecha else None,
            "subtotal": float(self.subtotal),
            "descuento": float(self.descuento),
            "base_imponible": float(self.base_imponible),
            "iva": float(self.iva),
            "total": float(self.total),
            "estado": self.estado,
            "row_version": self.row_version,
            "detalles": [d.to_dict() for d in self.detalles],
        }
