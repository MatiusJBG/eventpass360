"""Casos de uso de gestión de usuarios (ADMIN)."""
from typing import Optional

from src.domain.entities import Usuario
from src.domain.exceptions import ConflictError, NotFoundError, ValidationError
from src.domain.repositories import RolRepository, UsuarioRepository


def _validate_correo(correo: str) -> None:
    if not correo or "@" not in correo:
        raise ValidationError("Correo inválido")


class ListarUsuariosUseCase:
    def __init__(self, repo: UsuarioRepository):
        self.repo = repo

    def execute(self, q: Optional[str] = None) -> list[Usuario]:
        return self.repo.list_usuarios(q)


class CrearUsuarioUseCase:
    def __init__(self, repo: UsuarioRepository, rol_repo: RolRepository):
        self.repo = repo
        self.rol_repo = rol_repo

    def execute(self, rol_id: int, nombre: str, correo: str, password: str) -> Usuario:
        if not nombre or not correo or not password:
            raise ValidationError("nombre, correo y password son obligatorios")
        _validate_correo(correo)
        if len(password) < 6:
            raise ValidationError("La contraseña debe tener al menos 6 caracteres")
        if self.repo.find_by_correo(correo) is not None:
            raise ConflictError("El correo ya está registrado")
        if self.rol_repo.find_by_id(rol_id) is None:
            raise NotFoundError("Rol no existe")
        from src.application.use_cases.auth_use_cases import _hash_password
        return self.repo.create_usuario(rol_id, nombre, correo, _hash_password(password))


class ActualizarUsuarioUseCase:
    def __init__(self, repo: UsuarioRepository, rol_repo: RolRepository):
        self.repo = repo
        self.rol_repo = rol_repo

    def execute(self, usuario_id: int, nombre=None, correo=None, rol_id=None, password=None) -> Usuario:
        usuario = self.repo.find_by_id(usuario_id)
        if usuario is None:
            raise NotFoundError("Usuario no existe")
        fields = {}
        if nombre:
            fields["nombre"] = nombre
        if correo:
            _validate_correo(correo)
            existing = self.repo.find_by_correo(correo)
            if existing is not None and existing.id != usuario_id:
                raise ConflictError("El correo ya está en uso")
            fields["correo"] = correo
        if rol_id is not None:
            if self.rol_repo.find_by_id(rol_id) is None:
                raise NotFoundError("Rol no existe")
            fields["rol_id"] = rol_id
        if password:
            if len(password) < 6:
                raise ValidationError("La contraseña debe tener al menos 6 caracteres")
            from src.application.use_cases.auth_use_cases import _hash_password
            fields["password_hash"] = _hash_password(password)
        if not fields:
            raise ValidationError("Nada que actualizar")
        return self.repo.update_usuario(usuario_id, **fields)


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
