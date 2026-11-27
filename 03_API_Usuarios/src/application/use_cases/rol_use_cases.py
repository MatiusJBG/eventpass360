"""Casos de uso de gestión de roles (ADMIN)."""
from typing import Optional

from src.domain.entities import Rol
from src.domain.exceptions import ConflictError, NotFoundError, ValidationError
from src.domain.repositories import RolRepository


class ListarRolesUseCase:
    def __init__(self, repo: RolRepository):
        self.repo = repo

    def execute(self) -> list[Rol]:
        return self.repo.list_roles()


class CrearRolUseCase:
    def __init__(self, repo: RolRepository):
        self.repo = repo

    def execute(self, nombre: str) -> Rol:
        nombre = (nombre or "").strip()
        if not nombre:
            raise ValidationError("El nombre del rol es obligatorio")
        if self.repo.find_by_nombre(nombre) is not None:
            raise ConflictError("El rol ya existe")
        return self.repo.create_rol(nombre)


class ActualizarRolUseCase:
    def __init__(self, repo: RolRepository):
        self.repo = repo

    def execute(self, rol_id: int, nombre: Optional[str] = None, estado: Optional[bool] = None) -> Rol:
        if self.repo.find_by_id(rol_id) is None:
            raise NotFoundError("Rol no existe")
        if nombre:
            nombre = nombre.strip()
            existing = self.repo.find_by_nombre(nombre)
            if existing is not None and existing.id != rol_id:
                raise ConflictError("El rol ya existe")
        return self.repo.update_rol(rol_id, nombre=nombre, estado=estado)


class EliminarRolUseCase:
    def __init__(self, repo: RolRepository):
        self.repo = repo

    def execute(self, rol_id: int) -> None:
        if self.repo.find_by_id(rol_id) is None:
            raise NotFoundError("Rol no existe")
        if self.repo.count_usuarios_rol(rol_id) > 0:
            raise ConflictError("No se puede eliminar un rol con usuarios asociados")
        self.repo.delete_rol(rol_id)
