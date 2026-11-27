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
        if not isinstance(nombre, str) or not nombre.strip():
            raise ValidationError("El nombre del rol es obligatorio")
        nombre_norm = nombre.strip()
        if self.repo.find_by_nombre(nombre_norm) is not None:
            raise ConflictError("El rol ya existe")
        return self.repo.create_rol(nombre_norm)


class ActualizarRolUseCase:
    def __init__(self, repo: RolRepository):
        self.repo = repo

    def execute(self, rol_id: int, nombre: Optional[str] = None, estado: Optional[bool] = None) -> Rol:
        if self.repo.find_by_id(rol_id) is None:
            raise NotFoundError("Rol no existe")
        if nombre is None and estado is None:
            raise ValidationError("Nada que actualizar")
        nombre_norm = None
        if nombre is not None:
            if not isinstance(nombre, str) or not nombre.strip():
                raise ValidationError("El nombre del rol no puede estar vacío")
            nombre_norm = nombre.strip()
            existing = self.repo.find_by_nombre(nombre_norm)
            if existing is not None and existing.id != rol_id:
                raise ConflictError("El rol ya existe")
        if estado is not None and not isinstance(estado, bool):
            raise ValidationError("estado debe ser booleano")
        return self.repo.update_rol(rol_id, nombre=nombre_norm, estado=estado)


class EliminarRolUseCase:
    def __init__(self, repo: RolRepository):
        self.repo = repo

    def execute(self, rol_id: int) -> None:
        if self.repo.find_by_id(rol_id) is None:
            raise NotFoundError("Rol no existe")
        if self.repo.count_usuarios_rol(rol_id) > 0:
            raise ConflictError("No se puede eliminar un rol con usuarios asociados")
        self.repo.delete_rol(rol_id)
