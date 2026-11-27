"""Implementación concreta del repositorio de facturas."""
from src.domain.entities import Factura
from src.domain.repositories import FacturaRepository
from src.infrastructure.db.connection import get_connection


class PostgresFacturaRepository(FacturaRepository):
    def __init__(self, database_url: str):
        self.database_url = database_url

    @staticmethod
    def _row(row, include_content=True) -> Factura:
        return Factura(
            id=row["id"], compra_id=row["compra_id"], numero=row["numero"], fecha=row["fecha"],
            estado=row["estado"],
            xml=row.get("xml", "") if include_content else "",
            pdf_base64=row.get("pdf_base64", "") if include_content else "",
        )

    def _select(self, where, params, include_content=True):
        cols = "id, compra_id, numero, fecha, estado"
        if include_content:
            cols += ", xml, pdf_base64"
        with get_connection(self.database_url) as conn:
            row = conn.execute(f"SELECT {cols} FROM facturas {where}", params).fetchone()
        return self._row(row, include_content) if row else None

    def find_by_compra_id(self, compra_id):
        return self._select("WHERE compra_id = %s", (compra_id,), include_content=False)

    def find_by_id(self, factura_id):
        return self._select("WHERE id = %s", (factura_id,), include_content=True)

    def list_all(self, compra_id=None):
        cols = "id, compra_id, numero, fecha, estado"
        sql = f"SELECT {cols} FROM facturas"
        params = ()
        if compra_id is not None:
            sql += " WHERE compra_id = %s"
            params = (compra_id,)
        sql += " ORDER BY id"
        with get_connection(self.database_url) as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._row(r, include_content=False) for r in rows]

    def next_numero(self):
        with get_connection(self.database_url) as conn:
            row = conn.execute("SELECT nextval('factura_numero_seq') AS n").fetchone()
        return f"FAC-{row['n']:06d}"

    def create(self, compra_id, numero, fecha, xml, pdf_base64):
        with get_connection(self.database_url) as conn:
            row = conn.execute(
                "INSERT INTO facturas (compra_id, numero, fecha, xml, pdf_base64) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                (compra_id, numero, fecha, xml, pdf_base64),
            ).fetchone()
        return self.find_by_id(row["id"])

    def anular(self, factura_id):
        with get_connection(self.database_url) as conn:
            conn.execute("UPDATE facturas SET estado = 'ANULADA' WHERE id = %s", (factura_id,))
        return self.find_by_id(factura_id)
