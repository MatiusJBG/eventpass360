"""Implementaciones concretas de los puertos de dominio sobre PostgreSQL."""
from src.domain.entities import Rol, Usuario
from src.domain.exceptions import ConflictError
from src.domain.repositories import RolRepository, UsuarioRepository
from src.infrastructure.db.connection import get_connection

OCC_CONFLICT_MSG = (
    "Conflicto de concurrencia: el registro fue modificado por otro usuario. Recarga e intenta nuevamente."
)


class PostgresUsuarioRepository(UsuarioRepository):
    def __init__(self, database_url: str):
        self.database_url = database_url

    def _conn(self):
        return get_connection(self.database_url)

    @staticmethod
    def _row_to_usuario(row) -> Usuario:
        return Usuario(
            id=row["id"],
            rol_id=row["rol_id"],
            nombre=row["nombre"],
            correo=row["correo"],
            estado=row["estado"],
            creado_en=row["creado_en"],
            rol_nombre=row.get("rol_nombre"),
            row_version=row["row_version"],
        )

    def find_by_id(self, usuario_id: int):
        with self._conn() as conn:
            row = conn.execute(
                """SELECT u.id, u.rol_id, u.nombre, u.correo, u.estado, u.creado_en, u.row_version,
                          r.nombre AS rol_nombre
                   FROM usuarios u JOIN roles r ON r.id = u.rol_id WHERE u.id = %s""",
                (usuario_id,),
            ).fetchone()
        return self._row_to_usuario(row) if row else None

    def find_by_correo(self, correo: str):
        with self._conn() as conn:
            row = conn.execute(
                """SELECT u.id, u.rol_id, u.nombre, u.correo, u.estado, u.creado_en, u.row_version,
                          r.nombre AS rol_nombre
                   FROM usuarios u JOIN roles r ON r.id = u.rol_id WHERE u.correo = %s""",
                (correo,),
            ).fetchone()
        return self._row_to_usuario(row) if row else None

    def find_auth_by_correo(self, correo: str):
        with self._conn() as conn:
            row = conn.execute(
                """SELECT u.id, u.rol_id, u.nombre, u.correo, u.estado, u.creado_en, u.row_version,
                          u.password_hash, r.nombre AS rol_nombre
                   FROM usuarios u JOIN roles r ON r.id = u.rol_id WHERE u.correo = %s""",
                (correo,),
            ).fetchone()
        if not row:
            return None
        return self._row_to_usuario(row), row["password_hash"]

    def list_usuarios(self, q=None):
        sql = """SELECT u.id, u.rol_id, u.nombre, u.correo, u.estado, u.creado_en, u.row_version,
                        r.nombre AS rol_nombre
                 FROM usuarios u JOIN roles r ON r.id = u.rol_id"""
        params: tuple = ()
        if q:
            sql += " WHERE u.nombre ILIKE %s OR u.correo ILIKE %s"
            params = (f"%{q}%", f"%{q}%")
        sql += " ORDER BY u.id"
        with self._conn() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._row_to_usuario(r) for r in rows]

    def create_usuario(self, rol_id, nombre, correo, password_hash):
        with self._conn() as conn:
            row = conn.execute(
                "INSERT INTO usuarios (rol_id, nombre, correo, password_hash) VALUES (%s, %s, %s, %s) RETURNING id",
                (rol_id, nombre, correo, password_hash),
            ).fetchone()
        return self.find_by_id(row["id"])

    def update_usuario(self, usuario_id, expected_version=None, **fields):
        allowed = {
            "nombre": "nombre",
            "correo": "correo",
            "rol_id": "rol_id",
            "password_hash": "password_hash",
            "estado": "estado",
        }
        sets, params = [], []
        for key, column in allowed.items():
            if key in fields and fields[key] is not None:
                sets.append(f"{column} = %s")
                params.append(fields[key])
        if not sets:
            return self.find_by_id(usuario_id)
        sets.append("row_version = row_version + 1")
        if expected_version is not None:
            params.extend([usuario_id, expected_version])
            sql = f"UPDATE usuarios SET {', '.join(sets)} WHERE id = %s AND row_version = %s RETURNING id"
        else:
            params.append(usuario_id)
            sql = f"UPDATE usuarios SET {', '.join(sets)} WHERE id = %s RETURNING id"
        with self._conn() as conn:
            updated = conn.execute(sql, tuple(params)).fetchone()
            if updated is None and expected_version is not None:
                exists = conn.execute("SELECT 1 FROM usuarios WHERE id = %s", (usuario_id,)).fetchone()
                if exists is not None:
                    raise ConflictError(OCC_CONFLICT_MSG)
        return self.find_by_id(usuario_id)

    def deactivate_usuario(self, usuario_id):
        with self._conn() as conn:
            conn.execute(
                "UPDATE usuarios SET estado = FALSE, row_version = row_version + 1 WHERE id = %s",
                (usuario_id,),
            )

    def delete_usuario(self, usuario_id):
        with self._conn() as conn:
            conn.execute("DELETE FROM usuarios WHERE id = %s", (usuario_id,))

    def count_compras_usuario(self, usuario_id):
        with self._conn() as conn:
            row = conn.execute("SELECT count(*) AS n FROM compras WHERE usuario_id = %s", (usuario_id,)).fetchone()
        return row["n"]


class PostgresRolRepository(RolRepository):
    def __init__(self, database_url: str):
        self.database_url = database_url

    def _conn(self):
        return get_connection(self.database_url)

    @staticmethod
    def _row_to_rol(row) -> Rol:
        return Rol(
            id=row["id"],
            nombre=row["nombre"],
            estado=row["estado"],
            row_version=row["row_version"],
        )

    def list_roles(self):
        with self._conn() as conn:
            rows = conn.execute("SELECT id, nombre, estado, row_version FROM roles ORDER BY id").fetchall()
        return [self._row_to_rol(r) for r in rows]

    def find_by_id(self, rol_id):
        with self._conn() as conn:
            row = conn.execute(
                "SELECT id, nombre, estado, row_version FROM roles WHERE id = %s", (rol_id,)
            ).fetchone()
        return self._row_to_rol(row) if row else None

    def find_by_nombre(self, nombre):
        with self._conn() as conn:
            row = conn.execute(
                "SELECT id, nombre, estado, row_version FROM roles WHERE nombre = %s", (nombre,)
            ).fetchone()
        return self._row_to_rol(row) if row else None

    def create_rol(self, nombre):
        with self._conn() as conn:
            row = conn.execute("INSERT INTO roles (nombre) VALUES (%s) RETURNING id", (nombre,)).fetchone()
        return self.find_by_id(row["id"])

    def update_rol(self, rol_id, nombre=None, estado=None, expected_version=None):
        sets, params = [], []
        if nombre is not None:
            sets.append("nombre = %s")
            params.append(nombre)
        if estado is not None:
            sets.append("estado = %s")
            params.append(estado)
        if sets:
            sets.append("row_version = row_version + 1")
            if expected_version is not None:
                params.extend([rol_id, expected_version])
                sql = f"UPDATE roles SET {', '.join(sets)} WHERE id = %s AND row_version = %s RETURNING id"
            else:
                params.append(rol_id)
                sql = f"UPDATE roles SET {', '.join(sets)} WHERE id = %s RETURNING id"
            with self._conn() as conn:
                updated = conn.execute(sql, tuple(params)).fetchone()
                if updated is None and expected_version is not None:
                    exists = conn.execute("SELECT 1 FROM roles WHERE id = %s", (rol_id,)).fetchone()
                    if exists is not None:
                        raise ConflictError(OCC_CONFLICT_MSG)
        return self.find_by_id(rol_id)

    def delete_rol(self, rol_id):
        with self._conn() as conn:
            conn.execute("DELETE FROM roles WHERE id = %s", (rol_id,))

    def count_usuarios_rol(self, rol_id):
        with self._conn() as conn:
            row = conn.execute("SELECT count(*) AS n FROM usuarios WHERE rol_id = %s", (rol_id,)).fetchone()
        return row["n"]
