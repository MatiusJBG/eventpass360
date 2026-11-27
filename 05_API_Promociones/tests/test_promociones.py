"""Pruebas unitarias para API Promociones (:5003)."""
from decimal import Decimal
import unittest
from unittest.mock import MagicMock, patch

import jwt

from app import create_app
from src.application.use_cases.calculo_use_cases import CalcularPromocionUseCase
from src.application.use_cases.promocion_use_cases import (
    ActualizarPromocionUseCase,
    CrearPromocionUseCase,
    EliminarPromocionUseCase,
    ListarPromocionesUseCase,
)
from src.domain.entities import Promocion
from src.domain.exceptions import ConflictError, ValidationError
from src.domain.repositories import PromocionRepository
from src.infrastructure.db.postgres_repository import PostgresPromocionRepository


class InMemoryPromocionRepo(PromocionRepository):
    def __init__(self, initial=None):
        self._items = {}
        self._seq = 1
        for p in initial or []:
            self._items[p.id] = p
            self._seq = max(self._seq, p.id + 1)

    def list_all(self, solo_activas=False):
        items = list(self._items.values())
        if solo_activas:
            items = [p for p in items if p.estado]
        return sorted(items, key=lambda p: p.cantidad_min)

    def find_by_id(self, promocion_id):
        return self._items.get(promocion_id)

    def find_aplicable(self, cantidad_total):
        matches = [
            p for p in self._items.values()
            if p.estado and p.cantidad_min <= cantidad_total
            and (p.cantidad_max is None or p.cantidad_max >= cantidad_total)
        ]
        if not matches:
            return None
        return max(matches, key=lambda p: p.porcentaje)

    def find_overlaps(self, cantidad_min, cantidad_max, exclude_id=None):
        n_max = cantidad_max if cantidad_max is not None else float("inf")
        result = []
        for p in self.list_all(solo_activas=True):
            if exclude_id is not None and p.id == exclude_id:
                continue
            p_max = p.cantidad_max if p.cantidad_max is not None else float("inf")
            if cantidad_min <= p_max and n_max >= p.cantidad_min:
                result.append(p)
        return result

    def create(self, cantidad_min, cantidad_max, porcentaje):
        pid = self._seq
        self._seq += 1
        p = Promocion(id=pid, cantidad_min=cantidad_min, cantidad_max=cantidad_max, porcentaje=porcentaje, estado=True)
        self._items[pid] = p
        return p

    def update(self, promocion_id, expected_version=None, **fields):
        actual = self._items.get(promocion_id)
        if actual is None:
            return None
        if expected_version is not None and actual.row_version != expected_version:
            raise ConflictError(
                "Conflicto de concurrencia: la promoción fue modificada por otro usuario. Recarga e intenta nuevamente."
            )
        updated = Promocion(
            id=actual.id,
            cantidad_min=fields.get("cantidad_min", actual.cantidad_min),
            cantidad_max=fields["cantidad_max"] if "cantidad_max" in fields else actual.cantidad_max,
            porcentaje=fields.get("porcentaje", actual.porcentaje),
            estado=fields.get("estado", actual.estado),
            row_version=actual.row_version + 1,
        )
        self._items[promocion_id] = updated
        return updated

    def delete(self, promocion_id):
        self._items.pop(promocion_id, None)


class PromocionesTestCase(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryPromocionRepo([
            Promocion(id=1, cantidad_min=3, cantidad_max=4, porcentaje=Decimal("5.00"), estado=True),
            Promocion(id=2, cantidad_min=5, cantidad_max=9, porcentaje=Decimal("10.00"), estado=True),
            Promocion(id=3, cantidad_min=10, cantidad_max=None, porcentaje=Decimal("15.00"), estado=True),
        ])
        self.calcular_uc = CalcularPromocionUseCase(self.repo)
        self.crear_uc = CrearPromocionUseCase(self.repo)
        self.actualizar_uc = ActualizarPromocionUseCase(self.repo)

        self.app = create_app()
        container = self.app.extensions["container"]
        container.repo = self.repo
        container.listar_promociones = ListarPromocionesUseCase(self.repo)
        container.crear_promocion = self.crear_uc
        container.actualizar_promocion = self.actualizar_uc
        container.eliminar_promocion = EliminarPromocionUseCase(self.repo)
        container.calcular_promocion = self.calcular_uc
        self.client = self.app.test_client()
        self.secret = self.app.config["SETTINGS"].jwt_secret_key
        self.admin_headers = {
            "Authorization": "Bearer " + jwt.encode(
                {"sub": "1", "rol": "ADMIN", "nombre": "Admin", "correo": "admin@test.com"},
                self.secret,
                algorithm="HS256",
            )
        }

    def test_official_reference_case_both_payload_formats(self):
        # 3 * 25.00 -> subtotal 75.00, pct 5, descuento 3.75, base 71.25, iva 10.69, total 81.94
        expected = {
            "subtotal": 75.0,
            "cantidad_total": 3,
            "porcentaje_descuento": 5.0,
            "descuento": 3.75,
            "base_imponible": 71.25,
            "iva": 10.69,
            "total": 81.94,
        }
        r1 = self.client.post("/api/promociones/calcular", json={"subtotal": 75.0, "cantidad_total": 3})
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r1.get_json(), expected)

        r2 = self.client.post(
            "/api/promociones/calcular",
            json={"items": [{"cantidad": 2, "precio_unitario": 25.0}, {"cantidad": 1, "precio_unitario": 25.0}]},
        )
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.get_json(), expected)

    def test_calcular_rejects_invalid_inputs(self):
        for bad in (
            {"subtotal": -10, "cantidad_total": 3},
            {"subtotal": 50, "cantidad_total": 0},
            {"subtotal": 50, "cantidad_total": True},
            {"subtotal": True, "cantidad_total": 3},
            {"items": []},
            {"items": [{"cantidad": False, "precio_unitario": 10}]},
            {"items": [{"cantidad": 2, "precio_unitario": -1}]},
        ):
            resp = self.client.post("/api/promociones/calcular", json=bad)
            self.assertEqual(resp.status_code, 400, f"Expected 400 for {bad}")

    def test_overlap_rejected_on_create(self):
        with self.assertRaises(ConflictError):
            self.crear_uc.execute(4, 6, 8)
        resp = self.client.post(
            "/api/promociones",
            headers=self.admin_headers,
            json={"cantidad_min": 4, "cantidad_max": 6, "porcentaje": 8},
        )
        self.assertEqual(resp.status_code, 409)

    def test_overlap_rejected_on_edit_and_reactivation(self):
        # Edit promo 1 to overlap with promo 2 (5..9)
        with self.assertRaises(ConflictError):
            self.actualizar_uc.execute(1, cantidad_max=5)

        # Deactivate promo 1, create a new active promo in 3..4, then try reactivating promo 1
        self.actualizar_uc.execute(1, estado=False)
        self.crear_uc.execute(3, 4, 7)

        # Reactivating promo 1 (False -> True) WITHOUT changing cantidad_min/cantidad_max MUST raise 409
        resp = self.client.put(
            "/api/promociones/1",
            headers=self.admin_headers,
            json={"estado": True},
        )
        self.assertEqual(resp.status_code, 409)

    def test_update_cantidad_max_back_to_null_and_preserve_when_omitted(self):
        # Remove promo 3 (10..None) so promo 2 (5..9) can become open-ended (5..None)
        self.repo.delete(3)

        # Omitting cantidad_max keeps existing 9
        r_keep = self.client.put(
            "/api/promociones/2",
            headers=self.admin_headers,
            json={"porcentaje": 12},
        )
        self.assertEqual(r_keep.status_code, 200)
        self.assertEqual(r_keep.get_json()["cantidad_max"], 9)

        # Explicitly passing cantidad_max: null clears it to None ("Sin límite")
        r_null = self.client.put(
            "/api/promociones/2",
            headers=self.admin_headers,
            json={"cantidad_max": None},
        )
        self.assertEqual(r_null.status_code, 200)
        self.assertIsNone(r_null.get_json()["cantidad_max"])

        # Set back to 9, then clear using empty string ""
        self.client.put("/api/promociones/2", headers=self.admin_headers, json={"cantidad_max": 9})
        r_empty = self.client.put(
            "/api/promociones/2",
            headers=self.admin_headers,
            json={"cantidad_max": ""},
        )
        self.assertEqual(r_empty.status_code, 200)
        self.assertIsNone(r_empty.get_json()["cantidad_max"])

    def test_postgres_repo_update_sets_cantidad_max_to_none(self):
        pg_repo = PostgresPromocionRepository("postgresql://fake")
        mock_conn = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.__enter__.return_value = mock_conn
        mock_ctx.__exit__.return_value = False
        mock_conn.execute.return_value.fetchone.return_value = {
            "id": 2, "cantidad_min": 5, "cantidad_max": None, "porcentaje": Decimal("10.00"), "estado": True,
        }
        with patch("src.infrastructure.db.postgres_repository.get_connection", return_value=mock_ctx):
            pg_repo.update(2, cantidad_min=5, cantidad_max=None)
        update_call = mock_conn.execute.call_args_list[0]
        sql, params = update_call[0]
        self.assertIn("cantidad_max = %s", sql)
        self.assertIn(None, params)

    def test_reject_bool_and_non_int_inputs_with_400(self):
        for payload in (
            {"cantidad_min": True, "cantidad_max": 2, "porcentaje": 5},
            {"cantidad_min": 1, "cantidad_max": False, "porcentaje": 5},
            {"cantidad_min": "abc", "cantidad_max": 2, "porcentaje": 5},
            {"cantidad_min": 1, "cantidad_max": 2, "porcentaje": True},
        ):
            resp = self.client.post("/api/promociones", headers=self.admin_headers, json=payload)
            self.assertEqual(resp.status_code, 400, f"Expected 400 for {payload}")

        resp_put = self.client.put(
            "/api/promociones/1",
            headers=self.admin_headers,
            json={"cantidad_min": True},
        )
        self.assertEqual(resp_put.status_code, 400)

    def test_row_version_increment_and_occ_conflict_409(self):
        # Initial row_version is 1
        r_list = self.client.get("/api/promociones")
        self.assertEqual(r_list.status_code, 200)
        promo1 = next(p for p in r_list.get_json() if p["id"] == 1)
        self.assertEqual(promo1["row_version"], 1)

        # Matching row_version succeeds and increments to 2
        r_ok = self.client.put(
            "/api/promociones/1",
            headers=self.admin_headers,
            json={"porcentaje": 6.5, "row_version": 1},
        )
        self.assertEqual(r_ok.status_code, 200)
        self.assertEqual(r_ok.get_json()["row_version"], 2)

        # Stale row_version=1 returns 409 Conflict
        r_stale = self.client.put(
            "/api/promociones/1",
            headers=self.admin_headers,
            json={"porcentaje": 7.0, "row_version": 1},
        )
        self.assertEqual(r_stale.status_code, 409)

        # Invalid row_version (bool/float/zero/emoji) returns 400
        for bad_rv in (True, False, 0, -1, 1.5, "1🔥", "abc"):
            r_bad = self.client.put(
                "/api/promociones/1",
                headers=self.admin_headers,
                json={"porcentaje": 7.0, "row_version": bad_rv},
            )
            self.assertEqual(r_bad.status_code, 400, f"Expected 400 for row_version={bad_rv}")

    def test_postgres_repo_update_occ_sql_and_conflict(self):
        pg_repo = PostgresPromocionRepository("postgresql://fake")
        mock_conn = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.__enter__.return_value = mock_conn
        mock_ctx.__exit__.return_value = False
        # First execute (UPDATE ... RETURNING) returns None; second (find_by_id) returns existing row -> ConflictError
        mock_conn.execute.return_value.fetchone.side_effect = [
            None,
            {"id": 1, "cantidad_min": 3, "cantidad_max": 4, "porcentaje": Decimal("5.00"), "estado": True, "row_version": 2},
        ]
        with patch("src.infrastructure.db.postgres_repository.get_connection", return_value=mock_ctx):
            with self.assertRaises(ConflictError):
                pg_repo.update(1, expected_version=1, porcentaje=Decimal("6.00"))
        sql, params = mock_conn.execute.call_args_list[0][0]
        self.assertIn("row_version = row_version + 1", sql)
        self.assertIn("WHERE id = %s AND row_version = %s RETURNING", sql)
        self.assertEqual(params[-2:], (1, 1))

    def test_reject_emojis_and_strict_numeric_validation_400(self):
        # Emojis in create, update, and calcular
        for endpoint, method, payload in (
            ("/api/promociones", "post", {"cantidad_min": "3😀", "porcentaje": 5}),
            ("/api/promociones", "post", {"cantidad_min": 11, "cantidad_max": "20🔥", "porcentaje": 5}),
            ("/api/promociones", "post", {"cantidad_min": 11, "porcentaje": "10🎉"}),
            ("/api/promociones/1", "put", {"porcentaje": "5.5🚀"}),
            ("/api/promociones/calcular", "post", {"subtotal": "75😀", "cantidad_total": 3}),
            ("/api/promociones/calcular", "post", {"subtotal": 75, "cantidad_total": "3🎫"}),
            ("/api/promociones/calcular", "post", {"items": [{"cantidad": "2😎", "precio_unitario": 25}]}),
            ("/api/promociones/calcular", "post", {"items": [{"cantidad": 2, "precio_unitario": "25💰"}]}),
        ):
            fn = getattr(self.client, method)
            resp = fn(endpoint, headers=self.admin_headers, json=payload)
            self.assertEqual(resp.status_code, 400, f"Expected 400 for {endpoint} {payload}")

        # Strict numeric / decimal bounds
        for bad_payload in (
            {"cantidad_min": 1.5, "porcentaje": 5},
            {"cantidad_min": 1_000_001, "porcentaje": 5},
            {"cantidad_min": 1, "cantidad_max": 1_000_001, "porcentaje": 5},
            {"cantidad_min": 1, "cantidad_max": 2, "porcentaje": 10.123},
            {"cantidad_min": 1, "cantidad_max": 2, "porcentaje": "10.123"},
            {"cantidad_min": 1, "cantidad_max": 2, "porcentaje": "abc"},
            {"cantidad_min": 1, "cantidad_max": 2, "porcentaje": -1},
            {"cantidad_min": 1, "cantidad_max": 2, "porcentaje": 101},
            {"cantidad_min": "1.0", "porcentaje": 5},
        ):
            resp = self.client.post("/api/promociones", headers=self.admin_headers, json=bad_payload)
            self.assertEqual(resp.status_code, 400, f"Expected 400 for {bad_payload}")


if __name__ == "__main__":
    unittest.main()
