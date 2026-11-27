"""Casos de uso de gestión de usuarios (ADMIN)."""
from typing import Optional

from src.domain.entities import Usuario
from src.domain.exceptions import ConflictError, NotFoundError, ValidationError
from src.domain.repositories import PasswordHasher, RolRepository, UsuarioRepository


def _normalize_correo(correo) -> str:
    if not isinstance(correo, str):
        raise ValidationError("Correo inválido")
    correo_norm = correo.strip().lower()
    if not correo_norm or "@" not in correo_norm:
        raise ValidationError("Correo inválido")
    return correo_norm


def _validate_positive_int(value, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValidationError(f"{field} debe ser un entero positivo")
    return value


class ListarUsuariosUseCase:
    def __init__(self, repo: UsuarioRepository):
        self.repo = repo

    def execute(self, q: Optional[str] = None) -> list[Usuario]:
        return self.repo.list_usuarios(q)


class CrearUsuarioUseCase:
    def __init__(self, repo: UsuarioRepository, rol_repo: RolRepository, password_hasher: PasswordHasher):
        self.repo = repo
        self.rol_repo = rol_repo
        self.password_hasher = password_hasher

    def execute(self, rol_id: int, nombre: str, correo: str, password: str) -> Usuario:
        rol_id_valid = _validate_positive_int(rol_id, "rol_id")
        nombre_norm = nombre.strip() if isinstance(nombre, str) else ""
        if not nombre_norm or not correo or not isinstance(password, str) or not password:
            raise ValidationError("nombre, correo y password son obligatorios")
        correo_norm = _normalize_correo(correo)
        if len(password) < 6:
            raise ValidationError("La contraseña debe tener al menos 6 caracteres")
        if self.repo.find_by_correo(correo_norm) is not None:
            raise ConflictError("El correo ya está registrado")
        if self.rol_repo.find_by_id(rol_id_valid) is None:
            raise NotFoundError("Rol no existe")
        return self.repo.create_usuario(
            rol_id_valid, nombre_norm, correo_norm, self.password_hasher.hash(password)
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
    ) -> Usuario:
        usuario = self.repo.find_by_id(usuario_id)
        if usuario is None:
            raise NotFoundError("Usuario no existe")
        fields = {}
        if nombre is not None:
            if not isinstance(nombre, str) or not nombre.strip():
                raise ValidationError("El nombre no puede estar vacío")
            fields["nombre"] = nombre.strip()
        if correo is not None:
            correo_norm = _normalize_correo(correo)
            existing = self.repo.find_by_correo(correo_norm)
            if existing is not None and existing.id != usuario_id:
                raise ConflictError("El correo ya está en uso")
            fields["correo"] = correo_norm
        if rol_id is not None:
            rol_id_valid = _validate_positive_int(rol_id, "rol_id")
            if self.rol_repo.find_by_id(rol_id_valid) is None:
                raise NotFoundError("Rol no existe")
            fields["rol_id"] = rol_id_valid
        if password is not None and password != "":
            if not isinstance(password, str) or len(password) < 6:
                raise ValidationError("La contraseña debe tener al menos 6 caracteres")
            fields["password_hash"] = self.password_hasher.hash(password)
        if estado is not None:
            if not isinstance(estado, bool):
                raise ValidationError("estado debe ser booleano")
            fields["estado"] = estado
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
