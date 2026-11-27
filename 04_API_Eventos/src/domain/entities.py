"""Entidades puras del dominio de Eventos."""
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Optional


@dataclass(frozen=True)
class Categoria:
    id: int
    nombre: str
    descripcion: str
    estado: bool

    def to_dict(self) -> dict:
        return {"id": self.id, "nombre": self.nombre, "descripcion": self.descripcion, "estado": self.estado}


@dataclass(frozen=True)
class Evento:
    id: int
    categoria_id: int
    nombre: str
    descripcion: str
    lugar: str
    fecha: datetime
    imagen_url: str
    estado: bool
    categoria_nombre: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "categoria_id": self.categoria_id,
            "categoria": self.categoria_nombre,
            "nombre": self.nombre,
            "descripcion": self.descripcion,
            "lugar": self.lugar,
            "fecha": self.fecha.isoformat() if self.fecha else None,
            "imagen_url": self.imagen_url,
            "estado": self.estado,
        }


@dataclass(frozen=True)
class TipoEntrada:
    id: int
    evento_id: int
    tipo: str
    precio: Decimal
    stock: int
    estado: bool
    evento_nombre: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "evento_id": self.evento_id,
            "evento": self.evento_nombre,
            "tipo": self.tipo,
            "precio": float(self.precio),
            "stock": self.stock,
            "estado": self.estado,
        }
