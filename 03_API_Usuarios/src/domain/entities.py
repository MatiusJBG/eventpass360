"""Entidades puras e inmutables del dominio de Usuarios/Roles."""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass(frozen=True)
class Rol:
    id: int
    nombre: str
    estado: bool

    def to_dict(self) -> dict:
        return {"id": self.id, "nombre": self.nombre, "estado": self.estado}


@dataclass(frozen=True)
class Usuario:
    id: int
    rol_id: int
    nombre: str
    correo: str
    estado: bool
    creado_en: datetime
    rol_nombre: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "rol_id": self.rol_id,
            "rol": self.rol_nombre,
            "nombre": self.nombre,
            "correo": self.correo,
            "estado": self.estado,
            "creado_en": self.creado_en.isoformat() if self.creado_en else None,
        }
