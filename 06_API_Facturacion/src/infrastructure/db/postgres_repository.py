"""Implementación concreta del repositorio de facturas."""
import psycopg

from src.domain.entities import Factura
from src.domain.exceptions import ConflictError
from src.domain.repositories import FacturaRepository
from src.infrastructure.db.connection import get_connection


class PostgresFacturaRepository(FacturaRepository):
    def __init__(self, database_url: str):
        self.database_url = database_url

    @staticmethod
    def _row(row, include_content=True) -> Factura:
        return Factura(
            id=row["id"],
            compra_id=row["compra_id"],
            numero=row["numero"],
            fecha=row["fecha"],
            estado=row["estado"],
            xml=row.get("xml", "") if include_content else "",
            pdf_base64=row.get("pdf_base64", "") if include_content else "",
            usuario_id=row.get("usuario_id"),
            row_version=row.get("row_version", 1),
        )

    def _select(self, where, params, include_content=True):
        cols = "f.id, f.compra_id, f.numero, f.fecha, f.estado, f.row_version, c.usuario_id"
        if include_content:
            cols += ", f.xml, f.pdf_base64"
        with get_connection(self.database_url) as conn:
            row = conn.execute(
                f"SELECT {cols} FROM facturas f JOIN compras c ON c.id = f.compra_id {where}",
                params,
            ).fetchone()
        return self._row(row, include_content) if row else None

    def find_by_compra_id(self, compra_id):
        return self._select("WHERE f.compra_id = %s", (compra_id,), include_content=False)

    def find_by_id(self, factura_id):
        return self._select("WHERE f.id = %s", (factura_id,), include_content=True)

    def list_all(self, compra_id=None, usuario_id=None):
        cols = "f.id, f.compra_id, f.numero, f.fecha, f.estado, f.row_version, c.usuario_id"
        sql = f"SELECT {cols} FROM facturas f JOIN compras c ON c.id = f.compra_id"
        clauses = []
        params = []
        if compra_id is not None:
            clauses.append("f.compra_id = %s")
            params.append(compra_id)
        if usuario_id is not None:
            clauses.append("c.usuario_id = %s")
            params.append(usuario_id)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY f.id"
        with get_connection(self.database_url) as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()
        return [self._row(r, include_content=False) for r in rows]

    def next_numero(self):
        with get_connection(self.database_url) as conn:
            row = conn.execute("SELECT nextval('factura_numero_seq') AS n").fetchone()
        return f"FAC-{row['n']:06d}"

    def create(self, compra_id, numero, fecha, xml, pdf_base64):
        try:
            with get_connection(self.database_url) as conn:
                row = conn.execute(
                    "INSERT INTO facturas (compra_id, numero, fecha, xml, pdf_base64) VALUES (%s, %s, %s, %s, %s) RETURNING id",
                    (compra_id, numero, fecha, xml, pdf_base64),
                ).fetchone()
        except psycopg.errors.UniqueViolation as exc:
            existing = self.find_by_compra_id(compra_id)
            if existing is not None:
                return existing
            raise ConflictError("Ya existe una factura para esta compra") from exc
        return self.find_by_id(row["id"])

    def anular(self, factura_id, expected_version=None):
        if expected_version is not None:
            sql = (
                "UPDATE facturas SET estado = 'ANULADA', row_version = row_version + 1 "
                "WHERE id = %s AND estado = 'EMITIDA' AND row_version = %s "
                "RETURNING id, compra_id, numero, fecha, estado, row_version"
            )
            params = (factura_id, expected_version)
        else:
            sql = (
                "UPDATE facturas SET estado = 'ANULADA', row_version = row_version + 1 "
                "WHERE id = %s AND estado = 'EMITIDA' "
                "RETURNING id, compra_id, numero, fecha, estado, row_version"
            )
            params = (factura_id,)
        with get_connection(self.database_url) as conn:
            row = conn.execute(sql, params).fetchone()
        if row is None:
            existing = self.find_by_id(factura_id)
            if existing is not None:
                if existing.estado == "ANULADA":
                    raise ConflictError("La factura ya se encuentra anulada")
                raise ConflictError(
                    "Conflicto de concurrencia: la factura fue modificada por otro usuario. Recarga e intenta nuevamente."
                )
            return None
        return self._row(row, include_content=False)
