"""Implementaciones concretas de los puertos sobre PostgreSQL."""
from decimal import Decimal

from src.domain.entities import Categoria, Evento, TipoEntrada
from src.domain.exceptions import ConflictError
from src.domain.repositories import (
    CategoriaRepository, EventoRepository, StockRepository, TipoEntradaRepository,
)
from src.infrastructure.db.connection import get_connection

OCC_CONFLICT_MSG = (
    "Conflicto de concurrencia: el registro fue modificado por otro usuario. Recarga e intenta nuevamente."
)


class PostgresCategoriaRepository(CategoriaRepository):
    def __init__(self, database_url: str):
        self.database_url = database_url

    def _conn(self):
        return get_connection(self.database_url)

    @staticmethod
    def _row(row) -> Categoria:
        return Categoria(
            id=row["id"],
            nombre=row["nombre"],
            descripcion=row["descripcion"],
            estado=row["estado"],
            row_version=row["row_version"],
        )

    def list(self):
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT id, nombre, descripcion, estado, row_version FROM categorias ORDER BY id"
            ).fetchall()
        return [self._row(r) for r in rows]

    def find_by_id(self, categoria_id):
        with self._conn() as conn:
            row = conn.execute(
                "SELECT id, nombre, descripcion, estado, row_version FROM categorias WHERE id = %s",
                (categoria_id,),
            ).fetchone()
        return self._row(row) if row else None

    def find_by_nombre(self, nombre):
        with self._conn() as conn:
            row = conn.execute(
                "SELECT id, nombre, descripcion, estado, row_version FROM categorias WHERE nombre = %s",
                (nombre,),
            ).fetchone()
        return self._row(row) if row else None

    def create(self, nombre, descripcion):
        with self._conn() as conn:
            row = conn.execute(
                "INSERT INTO categorias (nombre, descripcion) VALUES (%s, %s) RETURNING id",
                (nombre, descripcion),
            ).fetchone()
        return self.find_by_id(row["id"])

    def update(self, categoria_id, nombre=None, descripcion=None, estado=None, expected_version=None):
        sets, params = [], []
        if nombre is not None:
            sets.append("nombre = %s")
            params.append(nombre)
        if descripcion is not None:
            sets.append("descripcion = %s")
            params.append(descripcion)
        if estado is not None:
            sets.append("estado = %s")
            params.append(estado)
        if sets:
            sets.append("row_version = row_version + 1")
            if expected_version is not None:
                params.extend([categoria_id, expected_version])
                sql = f"UPDATE categorias SET {', '.join(sets)} WHERE id = %s AND row_version = %s RETURNING id"
            else:
                params.append(categoria_id)
                sql = f"UPDATE categorias SET {', '.join(sets)} WHERE id = %s RETURNING id"
            with self._conn() as conn:
                updated = conn.execute(sql, tuple(params)).fetchone()
                if updated is None and expected_version is not None:
                    exists = conn.execute("SELECT 1 FROM categorias WHERE id = %s", (categoria_id,)).fetchone()
                    if exists is not None:
                        raise ConflictError(OCC_CONFLICT_MSG)
        return self.find_by_id(categoria_id)

    def count_eventos(self, categoria_id):
        with self._conn() as conn:
            row = conn.execute("SELECT count(*) AS n FROM eventos WHERE categoria_id = %s", (categoria_id,)).fetchone()
        return row["n"]

    def delete(self, categoria_id):
        with self._conn() as conn:
            conn.execute("DELETE FROM categorias WHERE id = %s", (categoria_id,))

    def deactivate(self, categoria_id):
        with self._conn() as conn:
            conn.execute(
                "UPDATE categorias SET estado = FALSE, row_version = row_version + 1 WHERE id = %s",
                (categoria_id,),
            )


class PostgresEventoRepository(EventoRepository):
    def __init__(self, database_url: str):
        self.database_url = database_url

    def _conn(self):
        return get_connection(self.database_url)

    @staticmethod
    def _row(row) -> Evento:
        return Evento(
            id=row["id"],
            categoria_id=row["categoria_id"],
            nombre=row["nombre"],
            descripcion=row["descripcion"],
            lugar=row["lugar"],
            fecha=row["fecha"],
            imagen_url=row["imagen_url"],
            estado=row["estado"],
            categoria_nombre=row.get("categoria_nombre"),
            row_version=row["row_version"],
        )

    def list(self, q=None, categoria_id=None, incluir_inactivos=False):
        sql = """SELECT e.id, e.categoria_id, e.nombre, e.descripcion, e.lugar, e.fecha, e.imagen_url,
                        e.estado, e.row_version, c.nombre AS categoria_nombre
                 FROM eventos e JOIN categorias c ON c.id = e.categoria_id"""
        where, params = [], []
        if q:
            where.append("(e.nombre ILIKE %s OR e.descripcion ILIKE %s)")
            params.extend([f"%{q}%", f"%{q}%"])
        if categoria_id is not None:
            where.append("e.categoria_id = %s")
            params.append(categoria_id)
        if not incluir_inactivos:
            where.append("e.estado = TRUE")
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY e.fecha"
        with self._conn() as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()
        return [self._row(r) for r in rows]

    def find_by_id(self, evento_id):
        with self._conn() as conn:
            row = conn.execute(
                """SELECT e.id, e.categoria_id, e.nombre, e.descripcion, e.lugar, e.fecha, e.imagen_url,
                          e.estado, e.row_version, c.nombre AS categoria_nombre
                   FROM eventos e JOIN categorias c ON c.id = e.categoria_id WHERE e.id = %s""",
                (evento_id,),
            ).fetchone()
        return self._row(row) if row else None

    def create(self, categoria_id, nombre, descripcion, lugar, fecha, imagen_url):
        with self._conn() as conn:
            row = conn.execute(
                "INSERT INTO eventos (categoria_id, nombre, descripcion, lugar, fecha, imagen_url) VALUES (%s,%s,%s,%s,%s,%s) RETURNING id",
                (categoria_id, nombre, descripcion, lugar, fecha, imagen_url),
            ).fetchone()
        return self.find_by_id(row["id"])

    def update(self, evento_id, expected_version=None, **fields):
        allowed = {
            "categoria_id": "categoria_id",
            "nombre": "nombre",
            "descripcion": "descripcion",
            "lugar": "lugar",
            "fecha": "fecha",
            "imagen_url": "imagen_url",
            "estado": "estado",
        }
        sets, params = [], []
        for key, column in allowed.items():
            if key in fields and fields[key] is not None:
                sets.append(f"{column} = %s")
                params.append(fields[key])
        if sets:
            sets.append("row_version = row_version + 1")
            if expected_version is not None:
                params.extend([evento_id, expected_version])
                sql = f"UPDATE eventos SET {', '.join(sets)} WHERE id = %s AND row_version = %s RETURNING id"
            else:
                params.append(evento_id)
                sql = f"UPDATE eventos SET {', '.join(sets)} WHERE id = %s RETURNING id"
            with self._conn() as conn:
                updated = conn.execute(sql, tuple(params)).fetchone()
                if updated is None and expected_version is not None:
                    exists = conn.execute("SELECT 1 FROM eventos WHERE id = %s", (evento_id,)).fetchone()
                    if exists is not None:
                        raise ConflictError(OCC_CONFLICT_MSG)
        return self.find_by_id(evento_id)

    def delete(self, evento_id):
        # Elimina primero los tipos_entrada hijos sin compras en la misma transacción
        # para evitar ForeignKeyViolation al eliminar el evento padre.
        with self._conn() as conn:
            with conn.transaction():
                conn.execute("DELETE FROM tipos_entrada WHERE evento_id = %s", (evento_id,))
                conn.execute("DELETE FROM eventos WHERE id = %s", (evento_id,))

    def deactivate(self, evento_id):
        with self._conn() as conn:
            conn.execute(
                "UPDATE eventos SET estado = FALSE, row_version = row_version + 1 WHERE id = %s",
                (evento_id,),
            )


class PostgresTipoEntradaRepository(TipoEntradaRepository):
    def __init__(self, database_url: str):
        self.database_url = database_url

    def _conn(self):
        return get_connection(self.database_url)

    @staticmethod
    def _row(row) -> TipoEntrada:
        return TipoEntrada(
            id=row["id"],
            evento_id=row["evento_id"],
            tipo=row["tipo"],
            precio=row["precio"],
            stock=row["stock"],
            estado=row["estado"],
            evento_nombre=row.get("evento_nombre"),
            row_version=row["row_version"],
        )

    def list(self, evento_id=None):
        sql = """SELECT t.id, t.evento_id, t.tipo, t.precio, t.stock, t.estado, t.row_version,
                        e.nombre AS evento_nombre
                 FROM tipos_entrada t JOIN eventos e ON e.id = t.evento_id"""
        params = ()
        if evento_id is not None:
            sql += " WHERE t.evento_id = %s"
            params = (evento_id,)
        sql += " ORDER BY t.id"
        with self._conn() as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._row(r) for r in rows]

    def find_by_id(self, tipo_id):
        with self._conn() as conn:
            row = conn.execute(
                """SELECT t.id, t.evento_id, t.tipo, t.precio, t.stock, t.estado, t.row_version,
                          e.nombre AS evento_nombre
                   FROM tipos_entrada t JOIN eventos e ON e.id = t.evento_id WHERE t.id = %s""",
                (tipo_id,),
            ).fetchone()
        return self._row(row) if row else None

    def find_by_evento_tipo(self, evento_id, tipo):
        with self._conn() as conn:
            row = conn.execute(
                """SELECT t.id, t.evento_id, t.tipo, t.precio, t.stock, t.estado, t.row_version,
                          e.nombre AS evento_nombre
                   FROM tipos_entrada t JOIN eventos e ON e.id = t.evento_id
                   WHERE t.evento_id = %s AND t.tipo = %s""",
                (evento_id, tipo),
            ).fetchone()
        return self._row(row) if row else None

    def create(self, evento_id, tipo, precio, stock):
        with self._conn() as conn:
            row = conn.execute(
                "INSERT INTO tipos_entrada (evento_id, tipo, precio, stock) VALUES (%s,%s,%s,%s) RETURNING id",
                (evento_id, tipo, precio, stock),
            ).fetchone()
        return self.find_by_id(row["id"])

    def update(self, tipo_id, expected_version=None, **fields):
        allowed = {"tipo": "tipo", "precio": "precio", "stock": "stock", "estado": "estado"}
        sets, params = [], []
        for key, column in allowed.items():
            if key in fields and fields[key] is not None:
                sets.append(f"{column} = %s")
                params.append(fields[key])
        if sets:
            sets.append("row_version = row_version + 1")
            if expected_version is not None:
                params.extend([tipo_id, expected_version])
                sql = f"UPDATE tipos_entrada SET {', '.join(sets)} WHERE id = %s AND row_version = %s RETURNING id"
            else:
                params.append(tipo_id)
                sql = f"UPDATE tipos_entrada SET {', '.join(sets)} WHERE id = %s RETURNING id"
            with self._conn() as conn:
                updated = conn.execute(sql, tuple(params)).fetchone()
                if updated is None and expected_version is not None:
                    exists = conn.execute("SELECT 1 FROM tipos_entrada WHERE id = %s", (tipo_id,)).fetchone()
                    if exists is not None:
                        raise ConflictError(OCC_CONFLICT_MSG)
        return self.find_by_id(tipo_id)

    def delete(self, tipo_id):
        with self._conn() as conn:
            conn.execute("DELETE FROM tipos_entrada WHERE id = %s", (tipo_id,))

    def deactivate(self, tipo_id):
        with self._conn() as conn:
            conn.execute(
                "UPDATE tipos_entrada SET estado = FALSE, row_version = row_version + 1 WHERE id = %s",
                (tipo_id,),
            )

    def count_detalles(self, tipo_id):
        with self._conn() as conn:
            row = conn.execute(
                "SELECT count(*) AS n FROM detalle_compra WHERE tipo_entrada_id = %s", (tipo_id,)
            ).fetchone()
        return row["n"]


class PostgresStockRepository(StockRepository):
    def __init__(self, database_url: str):
        self.database_url = database_url

    @staticmethod
    def _aggregate(items: list[dict]) -> list[dict]:
        grouped: dict[int, int] = {}
        for it in items:
            tid = it["tipo_entrada_id"]
            grouped[tid] = grouped.get(tid, 0) + it["cantidad"]
        return [{"tipo_entrada_id": tid, "cantidad": cant} for tid, cant in grouped.items()]

    def cotizar(self, items):
        items = self._aggregate(items)
        ids = [it["tipo_entrada_id"] for it in items]
        with get_connection(self.database_url) as conn:
            rows = conn.execute(
                """SELECT t.id, t.evento_id, t.tipo, t.precio, t.stock, t.estado AS tipo_estado,
                          e.nombre AS evento_nombre, e.estado AS evento_estado
                   FROM tipos_entrada t JOIN eventos e ON e.id = t.evento_id
                   WHERE t.id = ANY(%s)""",
                (ids,),
            ).fetchall()
        by_id = {r["id"]: r for r in rows}
        result_items = []
        subtotal_total = Decimal("0")
        for it in items:
            r = by_id.get(it["tipo_entrada_id"])
            if r is None:
                result_items.append({
                    "tipo_entrada_id": it["tipo_entrada_id"], "evento_id": None, "evento_nombre": None,
                    "tipo": None, "precio_unitario": 0.0, "stock_disponible": 0,
                    "cantidad_solicitada": it["cantidad"], "disponible": False, "subtotal": 0.0,
                })
                continue
            disponible = bool(r["tipo_estado"]) and bool(r["evento_estado"]) and r["stock"] >= it["cantidad"]
            precio = r["precio"]
            subtotal = precio * it["cantidad"]
            result_items.append({
                "tipo_entrada_id": r["id"], "evento_id": r["evento_id"], "evento_nombre": r["evento_nombre"],
                "tipo": r["tipo"], "precio_unitario": float(precio), "stock_disponible": r["stock"],
                "cantidad_solicitada": it["cantidad"], "disponible": disponible, "subtotal": float(subtotal),
            })
            if disponible:
                subtotal_total += subtotal
        return {"items": result_items, "subtotal_total": float(subtotal_total)}

    def descontar(self, items):
        items = sorted(self._aggregate(items), key=lambda x: x["tipo_entrada_id"])
        # Bloqueo pesimista ordenado (anti-deadlock) + verificación OCC por row_version.
        with get_connection(self.database_url) as conn:
            with conn.transaction():
                for it in items:
                    row = conn.execute(
                        """SELECT te.id, te.stock, te.row_version, te.estado, e.estado AS evento_estado
                           FROM tipos_entrada te
                           JOIN eventos e ON e.id = te.evento_id
                           WHERE te.id = %s
                           FOR UPDATE""",
                        (it["tipo_entrada_id"],),
                    ).fetchone()
                    if (
                        row is None
                        or not row["estado"]
                        or not row["evento_estado"]
                        or row["stock"] < it["cantidad"]
                    ):
                        raise ConflictError("Stock insuficiente o tipo de entrada no disponible")
                    cur = conn.execute(
                        """UPDATE tipos_entrada
                           SET stock = stock - %s, row_version = row_version + 1
                           WHERE id = %s AND row_version = %s AND stock >= %s""",
                        (it["cantidad"], it["tipo_entrada_id"], row["row_version"], it["cantidad"]),
                    )
                    if cur.rowcount == 0:
                        raise ConflictError(OCC_CONFLICT_MSG)

    def restaurar(self, items):
        items = sorted(self._aggregate(items), key=lambda x: x["tipo_entrada_id"])
        with get_connection(self.database_url) as conn:
            with conn.transaction():
                for it in items:
                    row = conn.execute(
                        """SELECT te.id, te.stock, te.row_version, te.estado, e.estado AS evento_estado
                           FROM tipos_entrada te
                           JOIN eventos e ON e.id = te.evento_id
                           WHERE te.id = %s
                           FOR UPDATE""",
                        (it["tipo_entrada_id"],),
                    ).fetchone()
                    if row is None:
                        raise ConflictError("Tipo de entrada no encontrado para restaurar stock")
                    cur = conn.execute(
                        """UPDATE tipos_entrada
                           SET stock = stock + %s, row_version = row_version + 1
                           WHERE id = %s AND row_version = %s""",
                        (it["cantidad"], it["tipo_entrada_id"], row["row_version"]),
                    )
                    if cur.rowcount == 0:
                        raise ConflictError(OCC_CONFLICT_MSG)
