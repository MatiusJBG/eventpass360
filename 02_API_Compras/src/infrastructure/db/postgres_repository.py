"""Implementación concreta del repositorio de compras."""
from decimal import Decimal

from src.domain.entities import Compra, DetalleCompra
from src.domain.repositories import CompraRepository
from src.infrastructure.db.connection import get_connection


def _d(value) -> Decimal:
    return Decimal(str(value))


class PostgresCompraRepository(CompraRepository):
    def __init__(self, database_url: str):
        self.database_url = database_url

    @staticmethod
    def _build_compra(row, detalles=None) -> Compra:
        return Compra(
            id=row["id"], usuario_id=row["usuario_id"], solicitud_id=row["solicitud_id"],
            fecha=row["fecha"], subtotal=row["subtotal"], descuento=row["descuento"],
            base_imponible=row["base_imponible"], iva=row["iva"], total=row["total"],
            estado=row["estado"], usuario_nombre=row.get("usuario_nombre", ""),
            usuario_correo=row.get("usuario_correo", ""), detalles=detalles or [],
        )

    @staticmethod
    def _detalle_from_row(r) -> DetalleCompra:
        return DetalleCompra(
            id=r["id"], compra_id=r["compra_id"], tipo_entrada_id=r["tipo_entrada_id"],
            cantidad=r["cantidad"], precio_unitario=r["precio_unitario"], subtotal=r["subtotal"],
            tipo=r.get("tipo", ""), evento_nombre=r.get("evento_nombre", ""),
        )

    def _detalles(self, compra_id):
        with get_connection(self.database_url) as conn:
            rows = conn.execute(
                """SELECT d.id, d.compra_id, d.tipo_entrada_id, d.cantidad, d.precio_unitario, d.subtotal,
                          t.tipo AS tipo, e.nombre AS evento_nombre
                   FROM detalle_compra d
                   JOIN tipos_entrada t ON t.id = d.tipo_entrada_id
                   JOIN eventos e ON e.id = t.evento_id
                   WHERE d.compra_id = %s ORDER BY d.id""",
                (compra_id,),
            ).fetchall()
        return [self._detalle_from_row(r) for r in rows]

    def _one(self, where, params):
        with get_connection(self.database_url) as conn:
            row = conn.execute(
                f"""SELECT c.id, c.usuario_id, c.solicitud_id, c.fecha, c.subtotal, c.descuento,
                           c.base_imponible, c.iva, c.total, c.estado,
                           u.nombre AS usuario_nombre, u.correo AS usuario_correo
                    FROM compras c JOIN usuarios u ON u.id = c.usuario_id {where}""",
                params,
            ).fetchone()
        if not row:
            return None
        return self._build_compra(row, self._detalles(row["id"]))

    def find_by_solicitud_id(self, solicitud_id):
        return self._one("WHERE c.solicitud_id = %s", (solicitud_id,))

    def find_by_id(self, compra_id):
        return self._one("WHERE c.id = %s", (compra_id,))

    def list_all(self, usuario_id=None):
        sql = """SELECT c.id, c.usuario_id, c.solicitud_id, c.fecha, c.subtotal, c.descuento,
                        c.base_imponible, c.iva, c.total, c.estado,
                        u.nombre AS usuario_nombre, u.correo AS usuario_correo
                 FROM compras c JOIN usuarios u ON u.id = c.usuario_id"""
        params = ()
        if usuario_id is not None:
            sql += " WHERE c.usuario_id = %s"
            params = (usuario_id,)
        sql += " ORDER BY c.id DESC"
        with get_connection(self.database_url) as conn:
            rows = conn.execute(sql, params).fetchall()
        ids = [r["id"] for r in rows]
        detalles_map = {}
        if ids:
            with get_connection(self.database_url) as conn:
                d_rows = conn.execute(
                    """SELECT d.id, d.compra_id, d.tipo_entrada_id, d.cantidad, d.precio_unitario, d.subtotal,
                              t.tipo AS tipo, e.nombre AS evento_nombre
                       FROM detalle_compra d
                       JOIN tipos_entrada t ON t.id = d.tipo_entrada_id
                       JOIN eventos e ON e.id = t.evento_id
                       WHERE d.compra_id = ANY(%s) ORDER BY d.id""",
                    (ids,),
                ).fetchall()
            for dr in d_rows:
                detalles_map.setdefault(dr["compra_id"], []).append(self._detalle_from_row(dr))
        return [self._build_compra(r, detalles_map.get(r["id"], [])) for r in rows]

    def create(self, usuario_id, solicitud_id, subtotal, descuento, base_imponible, iva, total, estado, detalles):
        with get_connection(self.database_url) as conn:
            row = conn.execute(
                """INSERT INTO compras (usuario_id, solicitud_id, subtotal, descuento, base_imponible, iva, total, estado)
                   VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING id""",
                (usuario_id, solicitud_id, _d(subtotal), _d(descuento), _d(base_imponible), _d(iva), _d(total), estado),
            ).fetchone()
            compra_id = row["id"]
            for d in detalles:
                conn.execute(
                    "INSERT INTO detalle_compra (compra_id, tipo_entrada_id, cantidad, precio_unitario, subtotal) VALUES (%s, %s, %s, %s, %s)",
                    (compra_id, d["tipo_entrada_id"], d["cantidad"], _d(d["precio_unitario"]), _d(d["subtotal"])),
                )
        return self.find_by_id(compra_id)

    def update_estado(self, compra_id, estado):
        with get_connection(self.database_url) as conn:
            conn.execute("UPDATE compras SET estado = %s WHERE id = %s", (estado, compra_id))

    def transition_estado(self, compra_id: int, from_estado: str, to_estado: str) -> bool:
        with get_connection(self.database_url) as conn:
            row = conn.execute(
                "UPDATE compras SET estado = %s WHERE id = %s AND estado = %s RETURNING id",
                (to_estado, compra_id, from_estado),
            ).fetchone()
        return row is not None

    def estadisticas(self):
        with get_connection(self.database_url) as conn:
            total = conn.execute("SELECT count(*) AS n FROM compras").fetchone()["n"]
            ingresos = conn.execute(
                "SELECT COALESCE(sum(total), 0) AS s FROM compras WHERE estado = 'CONFIRMADA'"
            ).fetchone()["s"]
            entradas = conn.execute(
                """SELECT COALESCE(sum(d.cantidad), 0) AS s
                   FROM detalle_compra d JOIN compras c ON c.id = d.compra_id
                   WHERE c.estado = 'CONFIRMADA'"""
            ).fetchone()["s"]
            por_estado = conn.execute(
                "SELECT estado, count(*) AS n FROM compras GROUP BY estado ORDER BY estado"
            ).fetchall()
        return {
            "total_compras": total,
            "ingresos_totales": float(ingresos),
            "entradas_vendidas": int(entradas),
            "por_estado": {r["estado"]: r["n"] for r in por_estado},
        }

    def anular(self, compra_id):
        with get_connection(self.database_url) as conn:
            conn.execute("UPDATE compras SET estado = 'ANULADA' WHERE id = %s", (compra_id,))
        return self.find_by_id(compra_id)
