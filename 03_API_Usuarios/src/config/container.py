"""Contenedor de Inyección de Dependencias (DIP)."""
from src.config.settings import Settings
from src.domain.repositories import PasswordHasher, RolRepository, UsuarioRepository
from src.infrastructure.db.postgres_repository import (
    PostgresRolRepository,
    PostgresUsuarioRepository,
)
from src.infrastructure.security.bcrypt_hasher import BcryptPasswordHasher
from src.application.use_cases.auth_use_cases import (
    GetPerfilUseCase,
    LoginUseCase,
    RegistroUseCase,
    UpdatePerfilUseCase,
)
from src.application.use_cases.usuario_use_cases import (
    ActualizarUsuarioUseCase,
    CrearUsuarioUseCase,
    DesactivarUsuarioUseCase,
    ListarUsuariosUseCase,
)
from src.application.use_cases.rol_use_cases import (
    ActualizarRolUseCase,
    CrearRolUseCase,
    EliminarRolUseCase,
    ListarRolesUseCase,
)


class Container:
    def __init__(
        self,
        settings: Settings,
        usuario_repo: UsuarioRepository,
        rol_repo: RolRepository,
        password_hasher: PasswordHasher,
    ):
        self.settings = settings
        self.usuario_repo = usuario_repo
        self.rol_repo = rol_repo
        self.password_hasher = password_hasher

        # Auth
        self.login_use_case = LoginUseCase(usuario_repo, settings, password_hasher)
        self.registro_use_case = RegistroUseCase(usuario_repo, rol_repo, password_hasher)
        self.get_perfil_use_case = GetPerfilUseCase(usuario_repo)
        self.update_perfil_use_case = UpdatePerfilUseCase(usuario_repo, password_hasher)

        # Usuarios (ADMIN)
        self.listar_usuarios_use_case = ListarUsuariosUseCase(usuario_repo)
        self.crear_usuario_use_case = CrearUsuarioUseCase(usuario_repo, rol_repo, password_hasher)
        self.actualizar_usuario_use_case = ActualizarUsuarioUseCase(usuario_repo, rol_repo, password_hasher)
        self.desactivar_usuario_use_case = DesactivarUsuarioUseCase(usuario_repo)

        # Roles (ADMIN)
        self.listar_roles_use_case = ListarRolesUseCase(rol_repo)
        self.crear_rol_use_case = CrearRolUseCase(rol_repo)
        self.actualizar_rol_use_case = ActualizarRolUseCase(rol_repo)
        self.eliminar_rol_use_case = EliminarRolUseCase(rol_repo)


def build_container(settings: Settings) -> Container:
    usuario_repo = PostgresUsuarioRepository(settings.database_url)
    rol_repo = PostgresRolRepository(settings.database_url)
    password_hasher = BcryptPasswordHasher()
    return Container(settings, usuario_repo, rol_repo, password_hasher)
