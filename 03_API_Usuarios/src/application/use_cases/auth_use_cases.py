"""Casos de uso de autenticación y perfil (SRP)."""
import datetime
import jwt
import bcrypt

from src.config.settings import Settings
from src.domain.entities import Usuario
from src.domain.exceptions import ConflictError, UnauthorizedError, ValidationError
from src.domain.repositories import RolRepository, UsuarioRepository


def _hash_password(password: str) -> str:
    return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt(rounds=12)).decode("utf-8")


def _check_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    except ValueError:
        return False


class LoginUseCase:
    def __init__(self, repo: UsuarioRepository, settings: Settings):
        self.repo = repo
        self.settings = settings

    def execute(self, correo: str, password: str) -> dict:
        result = self.repo.find_auth_by_correo(correo)
        if result is None:
            raise UnauthorizedError("Credenciales inválidas")
        usuario, password_hash = result
        if not usuario.estado:
            raise UnauthorizedError("Usuario desactivado")
        if not _check_password(password, password_hash):
            raise UnauthorizedError("Credenciales inválidas")
        exp = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(minutes=self.settings.jwt_expires_minutes)
        payload = {
            "sub": str(usuario.id),
            "rol": usuario.rol_nombre,
            "nombre": usuario.nombre,
            "correo": usuario.correo,
            "exp": exp,
        }
        token = jwt.encode(payload, self.settings.jwt_secret_key, algorithm="HS256")
        return {"token": token, "usuario": usuario.to_dict()}


class RegistroUseCase:
    def __init__(self, repo: UsuarioRepository, rol_repo: RolRepository):
        self.repo = repo
        self.rol_repo = rol_repo

    def execute(self, nombre: str, correo: str, password: str) -> Usuario:
        if not nombre or not correo or not password:
            raise ValidationError("nombre, correo y password son obligatorios")
        if "@" not in correo:
            raise ValidationError("Correo inválido")
        if len(password) < 6:
            raise ValidationError("La contraseña debe tener al menos 6 caracteres")
        if self.repo.find_by_correo(correo) is not None:
            raise ConflictError("El correo ya está registrado")
        # Registro público SIEMPRE como CLIENTE (impide escalación a ADMIN)
        rol_cliente = self.rol_repo.find_by_nombre("CLIENTE")
        if rol_cliente is None:
            raise ConflictError("Rol CLIENTE no configurado")
        return self.repo.create_usuario(rol_cliente.id, nombre, correo, _hash_password(password))


class GetPerfilUseCase:
    def __init__(self, repo: UsuarioRepository):
        self.repo = repo

    def execute(self, usuario_id: int) -> Usuario:
        usuario = self.repo.find_by_id(usuario_id)
        if usuario is None:
            raise UnauthorizedError("Usuario no encontrado")
        return usuario


class UpdatePerfilUseCase:
    def __init__(self, repo: UsuarioRepository):
        self.repo = repo

    def execute(self, usuario_id: int, nombre: str | None = None, correo: str | None = None, password: str | None = None) -> Usuario:
        fields = {}
        if nombre:
            fields["nombre"] = nombre
        if correo:
            if "@" not in correo:
                raise ValidationError("Correo inválido")
            existing = self.repo.find_by_correo(correo)
            if existing is not None and existing.id != usuario_id:
                raise ConflictError("El correo ya está en uso")
            fields["correo"] = correo
        if password:
            if len(password) < 6:
                raise ValidationError("La contraseña debe tener al menos 6 caracteres")
            fields["password_hash"] = _hash_password(password)
        if not fields:
            raise ValidationError("Nada que actualizar")
        return self.repo.update_usuario(usuario_id, **fields)
