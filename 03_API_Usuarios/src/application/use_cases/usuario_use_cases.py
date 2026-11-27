"""Casos de uso de gestión de usuarios (ADMIN)."""
from typing import Optional

from src.domain.entities import Usuario
from src.domain.exceptions import ConflictError, NotFoundError, ValidationError
from src.domain.repositories import PasswordHasher, RolRepository, UsuarioRepository
from src.domain.validators import (
    validate_correo,
    validate_nombre_usuario,
    validate_password_strict,
    validate_positive_int,
    validate_search_query,
)


class ListarUsuariosUseCase:
    def __init__(self, repo: UsuarioRepository):
        self.repo = repo

    def execute(self, q: Optional[str] = None) -> list[Usuario]:
        q_valid = validate_search_query(q, "q")
        return self.repo.list_usuarios(q_valid)


class CrearUsuarioUseCase:
    def __init__(self, repo: UsuarioRepository, rol_repo: RolRepository, password_hasher: PasswordHasher):
        self.repo = repo
        self.rol_repo = rol_repo
        self.password_hasher = password_hasher

    def execute(self, rol_id: int, nombre: str, correo: str, password: str) -> Usuario:
        rol_id_valid = validate_positive_int(rol_id, "rol_id")
        nombre_norm = validate_nombre_usuario(nombre, "nombre")
        correo_norm = validate_correo(correo)
        password_valid = validate_password_strict(password)
        if self.repo.find_by_correo(correo_norm) is not None:
            raise ConflictError("El correo ya está registrado")
        if self.rol_repo.find_by_id(rol_id_valid) is None:
            raise NotFoundError("Rol no existe")
        return self.repo.create_usuario(
            rol_id_valid, nombre_norm, correo_norm, self.password_hasher.hash(password_valid)
        )


class ActualizarUsuarioUseCase:
    def __init__(self, repo: UsuarioRepository, rol_repo: RolRepository, password_hasher: PasswordHasher):
        self.repo = repo
        self.rol_repo = rol_repo
        self.password_hasher = password_hasher

    def execute(
        self,
        usuario_id: int,
        nombre=None,
        correo=None,
        rol_id=None,
        password=None,
        estado=None,
        row_version: Optional[int] = None,
    ) -> Usuario:
        usuario = self.repo.find_by_id(usuario_id)
        if usuario is None:
            raise NotFoundError("Usuario no existe")
        expected_version = validate_positive_int(row_version, "row_version") if row_version is not None else None
        fields = {}
        if nombre is not None:
            fields["nombre"] = validate_nombre_usuario(nombre, "nombre")
        if correo is not None:
            correo_norm = validate_correo(correo)
            existing = self.repo.find_by_correo(correo_norm)
            if existing is not None and existing.id != usuario_id:
                raise ConflictError("El correo ya está en uso")
            fields["correo"] = correo_norm
        if rol_id is not None:
            rol_id_valid = validate_positive_int(rol_id, "rol_id")
            if self.rol_repo.find_by_id(rol_id_valid) is None:
                raise NotFoundError("Rol no existe")
            fields["rol_id"] = rol_id_valid
        if password is not None and password != "":
            password_valid = validate_password_strict(password)
            fields["password_hash"] = self.password_hasher.hash(password_valid)
        if estado is not None:
            if not isinstance(estado, bool):
                raise ValidationError("estado debe ser booleano")
            fields["estado"] = estado
        if not fields:
            raise ValidationError("Nada que actualizar")
        return self.repo.update_usuario(usuario_id, expected_version=expected_version, **fields)


class DesactivarUsuarioUseCase:
    def __init__(self, repo: UsuarioRepository):
        self.repo = repo

    def execute(self, usuario_id: int) -> None:
        if self.repo.find_by_id(usuario_id) is None:
            raise NotFoundError("Usuario no existe")
        # Baja lógica si posee historial de compras; física en caso contrario.
        if self.repo.count_compras_usuario(usuario_id) > 0:
            self.repo.deactivate_usuario(usuario_id)
        else:
            self.repo.delete_usuario(usuario_id)
