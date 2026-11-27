"""Implementación concreta del repositorio de entradas sobre PostgreSQL."""
from src.domain.entities import Entrada
from src.domain.exceptions import ConflictError, NotFoundError
from src.domain.repositories import EntradaRepository
from src.infrastructure.db.connection import get_connection

_ESTADOS_GENERABLES = ("PENDIENTE", "CONFIRMADA")


class PostgresEntradaRepository(EntradaRepository):
    def __init__(self, database_url: str):
        self.database_url = database_url

    @staticmethod
    def _row(row) -> Entrada:
        return Entrada(
            id=row["id"], compra_id=row["compra_id"], detalle_compra_id=row["detalle_compra_id"],
            evento_id=row["evento_id"], codigo=row["codigo"], estado=row["estado"],
            fecha_validacion=row["fecha_validacion"], row_version=row["row_version"],
            evento_nombre=row.get("evento_nombre", ""), tipo=row.get("tipo", ""),
        )

    _SELECT = """
        SELECT e.id, e.compra_id, e.detalle_compra_id, e.evento_id, e.codigo, e.estado,
               e.fecha_validacion, e.row_version, ev.nombre AS evento_nombre, t.tipo AS tipo
        FROM entradas e
        JOIN eventos ev ON ev.id = e.evento_id
        JOIN detalle_compra d ON d.id = e.detalle_compra_id
        JOIN tipos_entrada t ON t.id = d.tipo_entrada_id
    """

    def find_by_id(self, entrada_id):
        with get_connection(self.database_url) as conn:
            row = conn.execute(self._SELECT + " WHERE e.id = %s", (entrada_id,)).fetchone()
        return self._row(row) if row else None

    def find_by_codigo(self, codigo):
        with get_connection(self.database_url) as conn:
            row = conn.execute(self._SELECT + " WHERE e.codigo = %s", (codigo,)).fetchone()
        return self._row(row) if row else None

    def find_by_compra_id(self, compra_id):
        with get_connection(self.database_url) as conn:
            rows = conn.execute(self._SELECT + " WHERE e.compra_id = %s ORDER BY e.id", (compra_id,)).fetchall()
        return [self._row(r) for r in rows]

    def list_all(self, compra_id=None, usuario_id=None):
        sql = self._SELECT
        where, params = [], []
        if usuario_id is not None:
            sql += " JOIN compras c ON c.id = e.compra_id"
            where.append("c.usuario_id = %s")
            params.append(usuario_id)
        if compra_id is not None:
            where.append("e.compra_id = %s")
            params.append(compra_id)
        if where:
            sql += " WHERE " + " AND ".join(where)
        sql += " ORDER BY e.id"
        with get_connection(self.database_url) as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()
        return [self._row(r) for r in rows]

    def generar(self, compra_id):
        # Transacción con advisory lock: una única generación por compra (idempotente).
        with get_connection(self.database_url) as conn:
            conn.execute("SELECT pg_advisory_xact_lock(%s)", (compra_id,))
            existing = conn.execute("SELECT id FROM entradas WHERE compra_id = %s LIMIT 1", (compra_id,)).fetchone()
            if existing is not None:
                return self.find_by_compra_id(compra_id)
            compra = conn.execute("SELECT id, estado FROM compras WHERE id = %s", (compra_id,)).fetchone()
            if compra is None:
                raise NotFoundError("Compra no existe")
            if compra["estado"] not in _ESTADOS_GENERABLES:
                raise ConflictError("La compra no está en un estado válido para generar entradas")
            detalles = conn.execute(
                """SELECT d.id, d.cantidad, t.evento_id
                   FROM detalle_compra d JOIN tipos_entrada t ON t.id = d.tipo_entrada_id
                   WHERE d.compra_id = %s ORDER BY d.id""",
                (compra_id,),
            ).fetchall()
            if not detalles:
                raise NotFoundError("La compra no tiene detalle")
            for d in detalles:
                for _ in range(d["cantidad"]):
                    codigo = conn.execute(
                        "SELECT 'EVT-' || lpad(nextval('entrada_codigo_seq')::text, 6, '0') AS c"
                    ).fetchone()["c"]
                    conn.execute(
                        "INSERT INTO entradas (compra_id, detalle_compra_id, evento_id, codigo) VALUES (%s, %s, %s, %s)",
                        (compra_id, d["id"], d["evento_id"], codigo),
                    )
        return self.find_by_compra_id(compra_id)

    def validar(self, codigo, evento_id):
        with get_connection(self.database_url) as conn:
            cur = conn.execute(
                """UPDATE entradas SET estado = 'UTILIZADA', fecha_validacion = NOW(), row_version = row_version + 1
                   WHERE codigo = %s AND estado = 'DISPONIBLE' AND evento_id = %s RETURNING id""",
                (codigo, evento_id),
            )
            row = cur.fetchone()
        if row is None:
            return None
        return self.find_by_id(row["id"])

    def anular_por_compra(self, compra_id):
        with get_connection(self.database_url) as conn:
            conn.execute(
                "UPDATE entradas SET estado = 'ANULADA', row_version = row_version + 1 WHERE compra_id = %s AND estado = 'DISPONIBLE'",
                (compra_id,),
            )
