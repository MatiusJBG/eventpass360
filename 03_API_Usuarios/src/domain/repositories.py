"""Puertos abstractos (ABC) — ISP & LSP."""
from abc import ABC, abstractmethod
from typing import Optional

from src.domain.entities import Rol, Usuario


class UsuarioRepository(ABC):
    @abstractmethod
    def find_by_id(self, usuario_id: int) -> Optional[Usuario]: ...

    @abstractmethod
    def find_by_correo(self, correo: str) -> Optional[Usuario]: ...

    @abstractmethod
    def find_auth_by_correo(self, correo: str) -> Optional[tuple[Usuario, str]]: ...

    @abstractmethod
    def list_usuarios(self, q: Optional[str] = None) -> list[Usuario]: ...

    @abstractmethod
    def create_usuario(self, rol_id: int, nombre: str, correo: str, password_hash: str) -> Usuario: ...

    @abstractmethod
    def update_usuario(self, usuario_id: int, **fields) -> Usuario: ...

    @abstractmethod
    def deactivate_usuario(self, usuario_id: int) -> None: ...

    @abstractmethod
    def delete_usuario(self, usuario_id: int) -> None: ...

    @abstractmethod
    def count_compras_usuario(self, usuario_id: int) -> int: ...


class RolRepository(ABC):
    @abstractmethod
    def list_roles(self) -> list[Rol]: ...

    @abstractmethod
    def find_by_id(self, rol_id: int) -> Optional[Rol]: ...

    @abstractmethod
    def find_by_nombre(self, nombre: str) -> Optional[Rol]: ...

    @abstractmethod
    def create_rol(self, nombre: str) -> Rol: ...

    @abstractmethod
    def update_rol(self, rol_id: int, nombre: Optional[str] = None, estado: Optional[bool] = None) -> Rol: ...

    @abstractmethod
    def delete_rol(self, rol_id: int) -> None: ...

    @abstractmethod
    def count_usuarios_rol(self, rol_id: int) -> int: ...
