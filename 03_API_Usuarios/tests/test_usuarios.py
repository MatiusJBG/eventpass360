"""Pruebas unitarias de 03_API_Usuarios (casos de uso + rutas HTTP con fakes en memoria)."""
from datetime import datetime, timezone
import unittest

import jwt

from app import create_app
from src.config.container import Container
from src.config.settings import Settings
from src.domain.entities import Rol, Usuario
from src.domain.repositories import PasswordHasher, RolRepository, UsuarioRepository
from src.infrastructure.security.bcrypt_hasher import BcryptPasswordHasher


class FakePasswordHasher(PasswordHasher):
    def hash(self, password: str) -> str:
        return f"hashed::{password}"

    def verify(self, password: str, password_hash: str) -> bool:
        return password_hash == f"hashed::{password}"


class FakeRolRepository(RolRepository):
    def __init__(self):
        self._roles: dict[int, Rol] = {
            1: Rol(id=1, nombre="ADMIN", estado=True),
            2: Rol(id=2, nombre="CLIENTE", estado=True),
        }
        self._next_id = 3
        self.usuario_counts: dict[int, int] = {}

    def list_roles(self) -> list[Rol]:
        return [self._roles[k] for k in sorted(self._roles)]

    def find_by_id(self, rol_id: int):
        return self._roles.get(rol_id)

    def find_by_nombre(self, nombre: str):
        for r in self._roles.values():
            if r.nombre == nombre:
                return r
        return None

    def create_rol(self, nombre: str) -> Rol:
        rol = Rol(id=self._next_id, nombre=nombre, estado=True)
        self._roles[rol.id] = rol
        self._next_id += 1
        return rol

    def update_rol(self, rol_id: int, nombre=None, estado=None) -> Rol:
        cur = self._roles[rol_id]
        updated = Rol(
            id=cur.id,
            nombre=nombre if nombre is not None else cur.nombre,
            estado=estado if estado is not None else cur.estado,
        )
        self._roles[rol_id] = updated
        return updated

    def delete_rol(self, rol_id: int) -> None:
        self._roles.pop(rol_id, None)

    def count_usuarios_rol(self, rol_id: int) -> int:
        return self.usuario_counts.get(rol_id, 0)


class FakeUsuarioRepository(UsuarioRepository):
    def __init__(self, rol_repo: FakeRolRepository):
        self._rol_repo = rol_repo
        self._users: dict[int, dict] = {}
        self._next_id = 1
        self.compras_counts: dict[int, int] = {}

    def _to_entity(self, row: dict) -> Usuario:
        rol = self._rol_repo.find_by_id(row["rol_id"])
        return Usuario(
            id=row["id"],
            rol_id=row["rol_id"],
            nombre=row["nombre"],
            correo=row["correo"],
            estado=row["estado"],
            creado_en=row["creado_en"],
            rol_nombre=rol.nombre if rol else None,
        )

    def find_by_id(self, usuario_id: int):
        row = self._users.get(usuario_id)
        return self._to_entity(row) if row else None

    def find_by_correo(self, correo: str):
        for row in self._users.values():
            if row["correo"] == correo:
                return self._to_entity(row)
        return None

    def find_auth_by_correo(self, correo: str):
        for row in self._users.values():
            if row["correo"] == correo:
                return self._to_entity(row), row["password_hash"]
        return None

    def list_usuarios(self, q=None):
        res = []
        for uid in sorted(self._users):
            u = self._to_entity(self._users[uid])
            if q:
                ql = q.lower()
                if ql not in u.nombre.lower() and ql not in u.correo.lower():
                    continue
            res.append(u)
        return res

    def create_usuario(self, rol_id: int, nombre: str, correo: str, password_hash: str) -> Usuario:
        uid = self._next_id
        self._next_id += 1
        self._users[uid] = {
            "id": uid,
            "rol_id": rol_id,
            "nombre": nombre,
            "correo": correo,
            "password_hash": password_hash,
            "estado": True,
            "creado_en": datetime.now(timezone.utc),
        }
        return self._to_entity(self._users[uid])

    def update_usuario(self, usuario_id: int, **fields) -> Usuario:
        row = self._users[usuario_id]
        for k in ("nombre", "correo", "rol_id", "password_hash", "estado"):
            if k in fields and fields[k] is not None:
                row[k] = fields[k]
        return self._to_entity(row)

    def deactivate_usuario(self, usuario_id: int) -> None:
        self._users[usuario_id]["estado"] = False

    def delete_usuario(self, usuario_id: int) -> None:
        self._users.pop(usuario_id, None)

    def count_compras_usuario(self, usuario_id: int) -> int:
        return self.compras_counts.get(usuario_id, 0)


class UsuariosApiTestCase(unittest.TestCase):
    def setUp(self):
        self.settings = Settings(
            database_url="postgresql://fake",
            jwt_secret_key="test-secret-key-unit-32-bytes-min!",
            jwt_expires_minutes=60,
            cors_origins="*",
        )
        self.rol_repo = FakeRolRepository()
        self.user_repo = FakeUsuarioRepository(self.rol_repo)
        self.hasher = FakePasswordHasher()
        self.container = Container(self.settings, self.user_repo, self.rol_repo, self.hasher)
        self.app = create_app(container=self.container, settings=self.settings)
        self.client = self.app.test_client()

        self.admin = self.user_repo.create_usuario(1, "Admin", "admin@test.com", self.hasher.hash("admin123"))
        self.cliente = self.user_repo.create_usuario(2, "Cliente", "cliente@test.com", self.hasher.hash("client123"))

    def _auth_header(self, user_id: int, rol: str) -> dict:
        token = jwt.encode(
            {"sub": str(user_id), "rol": rol, "nombre": "Test", "correo": "t@test.com"},
            self.settings.jwt_secret_key,
            algorithm="HS256",
        )
        return {"Authorization": f"Bearer {token}"}

    # --- Login ---
    def test_login_active_normalizes_email(self):
        resp = self.client.post("/api/login", json={"correo": "  ADMIN@Test.COM ", "password": "admin123"})
        self.assertEqual(resp.status_code, 200)
        body = resp.get_json()
        self.assertIn("token", body)
        self.assertEqual(body["usuario"]["correo"], "admin@test.com")

    def test_login_inactive_rejected(self):
        self.user_repo.deactivate_usuario(self.cliente.id)
        resp = self.client.post("/api/login", json={"correo": "cliente@test.com", "password": "client123"})
        self.assertEqual(resp.status_code, 401)

    def test_login_wrong_password_rejected(self):
        resp = self.client.post("/api/login", json={"correo": "cliente@test.com", "password": "wrong"})
        self.assertEqual(resp.status_code, 401)

    # --- Registro ---
    def test_registro_forces_cliente_even_with_rol_id_1(self):
        resp = self.client.post(
            "/api/registro",
            json={"nombre": "  Ana  ", "correo": "  ANA@Test.COM ", "password": "secret123", "rol_id": 1},
        )
        self.assertEqual(resp.status_code, 201)
        body = resp.get_json()
        self.assertEqual(body["rol"], "CLIENTE")
        self.assertEqual(body["rol_id"], 2)
        self.assertEqual(body["correo"], "ana@test.com")
        self.assertEqual(body["nombre"], "Ana")

    # --- Perfil ---
    def test_perfil_active_get_and_put(self):
        headers = self._auth_header(self.cliente.id, "CLIENTE")
        r_get = self.client.get("/api/perfil", headers=headers)
        self.assertEqual(r_get.status_code, 200)
        self.assertEqual(r_get.get_json()["id"], self.cliente.id)

        r_put = self.client.put(
            "/api/perfil",
            headers=headers,
            json={"nombre": "Cliente Nuevo", "correo": "  NUEVO@Test.COM "},
        )
        self.assertEqual(r_put.status_code, 200)
        self.assertEqual(r_put.get_json()["correo"], "nuevo@test.com")

    def test_perfil_inactive_user_returns_401(self):
        self.user_repo.deactivate_usuario(self.cliente.id)
        headers = self._auth_header(self.cliente.id, "CLIENTE")
        r_get = self.client.get("/api/perfil", headers=headers)
        self.assertEqual(r_get.status_code, 401)
        self.assertEqual(r_get.get_json()["message"], "Usuario inactivo")

        r_put = self.client.put("/api/perfil", headers=headers, json={"nombre": "X"})
        self.assertEqual(r_put.status_code, 401)

    def test_perfil_missing_user_returns_404_not_500(self):
        headers = self._auth_header(999, "CLIENTE")
        r_get = self.client.get("/api/perfil", headers=headers)
        self.assertEqual(r_get.status_code, 404)

        r_put = self.client.put("/api/perfil", headers=headers, json={"nombre": "X"})
        self.assertEqual(r_put.status_code, 404)

    # --- Usuarios (ADMIN) ---
    def test_usuario_create_and_invalid_rol_id(self):
        headers = self._auth_header(self.admin.id, "ADMIN")

        for bad_rol in (None, True, False, "abc", 0, -2, 1.5):
            r = self.client.post(
                "/api/usuarios",
                headers=headers,
                json={"rol_id": bad_rol, "nombre": "Juan", "correo": "j@test.com", "password": "password123"},
            )
            self.assertEqual(r.status_code, 400, f"Expected 400 for rol_id={bad_rol!r}")

        r_ok = self.client.post(
            "/api/usuarios",
            headers=headers,
            json={"rol_id": 2, "nombre": " Juan ", "correo": "  JUAN@Test.COM ", "password": "password123"},
        )
        self.assertEqual(r_ok.status_code, 201)
        self.assertEqual(r_ok.get_json()["correo"], "juan@test.com")

    def test_usuario_update_reactivate_estado_and_invalid_rol_id(self):
        headers = self._auth_header(self.admin.id, "ADMIN")
        self.user_repo.deactivate_usuario(self.cliente.id)

        r_bad_rol = self.client.put(
            f"/api/usuarios/{self.cliente.id}",
            headers=headers,
            json={"rol_id": True},
        )
        self.assertEqual(r_bad_rol.status_code, 400)

        r_bad_estado = self.client.put(
            f"/api/usuarios/{self.cliente.id}",
            headers=headers,
            json={"estado": "true"},
        )
        self.assertEqual(r_bad_estado.status_code, 400)

        r_reactivate = self.client.put(
            f"/api/usuarios/{self.cliente.id}",
            headers=headers,
            json={"estado": True},
        )
        self.assertEqual(r_reactivate.status_code, 200)
        self.assertTrue(r_reactivate.get_json()["estado"])

    # --- Roles (ADMIN) ---
    def test_role_update_rejects_empty_nombre_and_empty_payload_and_strips(self):
        headers = self._auth_header(self.admin.id, "ADMIN")

        r_empty = self.client.put("/api/roles/2", headers=headers, json={"nombre": ""})
        self.assertEqual(r_empty.status_code, 400)

        r_spaces = self.client.put("/api/roles/2", headers=headers, json={"nombre": "   "})
        self.assertEqual(r_spaces.status_code, 400)

        r_noop = self.client.put("/api/roles/2", headers=headers, json={})
        self.assertEqual(r_noop.status_code, 400)

        r_ok = self.client.put("/api/roles/2", headers=headers, json={"nombre": "  VIP  "})
        self.assertEqual(r_ok.status_code, 200)
        self.assertEqual(r_ok.get_json()["nombre"], "VIP")

    def test_role_delete_with_users_blocked(self):
        headers = self._auth_header(self.admin.id, "ADMIN")
        self.rol_repo.usuario_counts[2] = 3
        r_blocked = self.client.delete("/api/roles/2", headers=headers)
        self.assertEqual(r_blocked.status_code, 409)

        nuevo = self.rol_repo.create_rol("TEMP")
        r_ok = self.client.delete(f"/api/roles/{nuevo.id}", headers=headers)
        self.assertEqual(r_ok.status_code, 200)

    def test_bcrypt_password_hasher_roundtrip(self):
        hasher = BcryptPasswordHasher(rounds=4)
        hashed = hasher.hash("claveSegura123")
        self.assertNotEqual(hashed, "claveSegura123")
        self.assertTrue(hasher.verify("claveSegura123", hashed))
        self.assertFalse(hasher.verify("otraClave", hashed))
        self.assertFalse(hasher.verify("claveSegura123", "not-a-valid-hash"))


if __name__ == "__main__":
    unittest.main()
