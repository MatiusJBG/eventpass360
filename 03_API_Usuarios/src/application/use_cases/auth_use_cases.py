"""Casos de uso de autenticación y perfil (SRP)."""
import datetime
import jwt

from src.config.settings import Settings
from src.domain.entities import Usuario
from src.domain.exceptions import ConflictError, NotFoundError, UnauthorizedError, ValidationError
from src.domain.repositories import PasswordHasher, RolRepository, UsuarioRepository


def _normalize_correo(correo) -> str:
    if not isinstance(correo, str):
        return ""
    return correo.strip().lower()


class LoginUseCase:
    def __init__(self, repo: UsuarioRepository, settings: Settings, password_hasher: PasswordHasher):
        self.repo = repo
        self.settings = settings
        self.password_hasher = password_hasher

    def execute(self, correo: str, password: str) -> dict:
        correo_norm = _normalize_correo(correo)
        if not correo_norm or not isinstance(password, str) or not password:
            raise UnauthorizedError("Credenciales inválidas")
        result = self.repo.find_auth_by_correo(correo_norm)
        if result is None:
            raise UnauthorizedError("Credenciales inválidas")
        usuario, password_hash = result
        if not usuario.estado:
            raise UnauthorizedError("Usuario desactivado")
        if not self.password_hasher.verify(password, password_hash):
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
    def __init__(self, repo: UsuarioRepository, rol_repo: RolRepository, password_hasher: PasswordHasher):
        self.repo = repo
        self.rol_repo = rol_repo
        self.password_hasher = password_hasher

    def execute(self, nombre: str, correo: str, password: str) -> Usuario:
        nombre_norm = nombre.strip() if isinstance(nombre, str) else ""
        correo_norm = _normalize_correo(correo)
        if not nombre_norm or not correo_norm or not isinstance(password, str) or not password:
            raise ValidationError("nombre, correo y password son obligatorios")
        if "@" not in correo_norm:
            raise ValidationError("Correo inválido")
        if len(password) < 6:
            raise ValidationError("La contraseña debe tener al menos 6 caracteres")
        if self.repo.find_by_correo(correo_norm) is not None:
            raise ConflictError("El correo ya está registrado")
        # Registro público SIEMPRE como CLIENTE (impide escalación a ADMIN)
        rol_cliente = self.rol_repo.find_by_nombre("CLIENTE")
        if rol_cliente is None:
            raise ConflictError("Rol CLIENTE no configurado")
        return self.repo.create_usuario(
            rol_cliente.id, nombre_norm, correo_norm, self.password_hasher.hash(password)
        )


class GetPerfilUseCase:
    def __init__(self, repo: UsuarioRepository):
        self.repo = repo

    def execute(self, usuario_id: int) -> Usuario:
        usuario = self.repo.find_by_id(usuario_id)
        if usuario is None:
            raise NotFoundError("Usuario no encontrado")
        if not usuario.estado:
            raise UnauthorizedError("Usuario inactivo")
        return usuario


class UpdatePerfilUseCase:
    def __init__(self, repo: UsuarioRepository, password_hasher: PasswordHasher):
        self.repo = repo
        self.password_hasher = password_hasher

    def execute(
        self,
        usuario_id: int,
        nombre: str | None = None,
        correo: str | None = None,
        password: str | None = None,
    ) -> Usuario:
        usuario = self.repo.find_by_id(usuario_id)
        if usuario is None:
            raise NotFoundError("Usuario no encontrado")
        if not usuario.estado:
            raise UnauthorizedError("Usuario inactivo")
        fields = {}
        if nombre is not None:
            if not isinstance(nombre, str) or not nombre.strip():
                raise ValidationError("El nombre no puede estar vacío")
            fields["nombre"] = nombre.strip()
        if correo is not None:
            correo_norm = _normalize_correo(correo)
            if not correo_norm or "@" not in correo_norm:
                raise ValidationError("Correo inválido")
            existing = self.repo.find_by_correo(correo_norm)
            if existing is not None and existing.id != usuario_id:
                raise ConflictError("El correo ya está en uso")
            fields["correo"] = correo_norm
        if password is not None and password != "":
            if not isinstance(password, str) or len(password) < 6:
                raise ValidationError("La contraseña debe tener al menos 6 caracteres")
            fields["password_hash"] = self.password_hasher.hash(password)
        if not fields:
            raise ValidationError("Nada que actualizar")
        return self.repo.update_usuario(usuario_id, **fields)
