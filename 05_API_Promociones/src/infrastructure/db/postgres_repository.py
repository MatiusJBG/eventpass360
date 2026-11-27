"""Implementación concreta sobre PostgreSQL."""
from typing import Optional

from src.domain.entities import Promocion
from src.domain.exceptions import ConflictError
from src.domain.repositories import PromocionRepository
from src.infrastructure.db.connection import get_connection


class PostgresPromocionRepository(PromocionRepository):
    def __init__(self, database_url: str):
        self.database_url = database_url

    @staticmethod
    def _row(row) -> Promocion:
        return Promocion(
            id=row["id"],
            cantidad_min=row["cantidad_min"],
            cantidad_max=row["cantidad_max"],
            porcentaje=row["porcentaje"],
            estado=row["estado"],
            row_version=row.get("row_version", 1),
        )

    def list_all(self, solo_activas=False):
        sql = "SELECT id, cantidad_min, cantidad_max, porcentaje, estado, row_version FROM promociones"
        params = ()
        if solo_activas:
            sql += " WHERE estado = TRUE"
        sql += " ORDER BY cantidad_min"
        with get_connection(self.database_url) as conn:
            rows = conn.execute(sql, params).fetchall()
        return [self._row(r) for r in rows]

    def find_by_id(self, promocion_id):
        with get_connection(self.database_url) as conn:
            row = conn.execute(
                "SELECT id, cantidad_min, cantidad_max, porcentaje, estado, row_version FROM promociones WHERE id = %s",
                (promocion_id,),
            ).fetchone()
        return self._row(row) if row else None

    def find_aplicable(self, cantidad_total):
        with get_connection(self.database_url) as conn:
            row = conn.execute(
                """SELECT id, cantidad_min, cantidad_max, porcentaje, estado, row_version FROM promociones
                   WHERE estado = TRUE AND cantidad_min <= %s
                     AND (cantidad_max IS NULL OR cantidad_max >= %s)
                   ORDER BY porcentaje DESC LIMIT 1""",
                (cantidad_total, cantidad_total),
            ).fetchone()
        return self._row(row) if row else None

    def find_overlaps(self, cantidad_min, cantidad_max, exclude_id=None):
        rows = self.list_all(solo_activas=True)
        n_max = cantidad_max if cantidad_max is not None else float("inf")
        result = []
        for p in rows:
            if exclude_id is not None and p.id == exclude_id:
                continue
            p_max = p.cantidad_max if p.cantidad_max is not None else float("inf")
            if cantidad_min <= p_max and n_max >= p.cantidad_min:
                result.append(p)
        return result

    def create(self, cantidad_min, cantidad_max, porcentaje):
        with get_connection(self.database_url) as conn:
            row = conn.execute(
                "INSERT INTO promociones (cantidad_min, cantidad_max, porcentaje) VALUES (%s, %s, %s) RETURNING id",
                (cantidad_min, cantidad_max, porcentaje),
            ).fetchone()
        return self.find_by_id(row["id"])

    def update(self, promocion_id, expected_version: Optional[int] = None, **fields):
        allowed = {"cantidad_min": "cantidad_min", "cantidad_max": "cantidad_max",
                   "porcentaje": "porcentaje", "estado": "estado"}
        sets, params = [], []
        for key, column in allowed.items():
            if key in fields:
                if key != "cantidad_max" and fields[key] is None:
                    continue
                sets.append(f"{column} = %s")
                params.append(fields[key])
        if not sets:
            return self.find_by_id(promocion_id)
        sets.append("row_version = row_version + 1")
        returning = "id, cantidad_min, cantidad_max, porcentaje, estado, row_version"
        if expected_version is not None:
            sql = f"UPDATE promociones SET {', '.join(sets)} WHERE id = %s AND row_version = %s RETURNING {returning}"
            params.extend([promocion_id, expected_version])
        else:
            sql = f"UPDATE promociones SET {', '.join(sets)} WHERE id = %s RETURNING {returning}"
            params.append(promocion_id)
        with get_connection(self.database_url) as conn:
            row = conn.execute(sql, tuple(params)).fetchone()
        if row is None:
            if expected_version is not None and self.find_by_id(promocion_id) is not None:
                raise ConflictError(
                    "Conflicto de concurrencia: la promoción fue modificada por otro usuario. Recarga e intenta nuevamente."
                )
            return None
        return self._row(row)

    def delete(self, promocion_id):
        with get_connection(self.database_url) as conn:
            conn.execute("DELETE FROM promociones WHERE id = %s", (promocion_id,))
