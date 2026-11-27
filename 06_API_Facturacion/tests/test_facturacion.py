"""Pruebas unitarias para API Facturación (:5004)."""
from datetime import datetime, timezone
import unittest
from unittest.mock import MagicMock, patch
import xml.etree.ElementTree as ET

import jwt

from app import create_app
from src.application.use_cases.factura_use_cases import (
    AnularFacturaUseCase,
    EmitirFacturaUseCase,
    ListarFacturasUseCase,
    ObtenerFacturaUseCase,
)
from src.domain.entities import Factura
from src.domain.exceptions import ConflictError
from src.domain.repositories import FacturaRepository
from src.infrastructure.gateways.pdf_service import GenerarFacturaPdfService
from src.infrastructure.gateways.xml_service import GenerarFacturaXmlService


class InMemoryFacturaRepo(FacturaRepository):
    def __init__(self, compra_owners=None):
        self._items = {}
        self._by_compra = {}
        self._seq = 1
        self._num_seq = 1
        self._compra_owners = compra_owners or {}
        self.simulate_race_on_create = False

    def find_by_compra_id(self, compra_id):
        fid = self._by_compra.get(compra_id)
        return self._items.get(fid) if fid is not None else None

    def find_by_id(self, factura_id):
        return self._items.get(factura_id)

    def list_all(self, compra_id=None, usuario_id=None):
        res = list(self._items.values())
        if compra_id is not None:
            res = [f for f in res if f.compra_id == compra_id]
        if usuario_id is not None:
            res = [f for f in res if f.usuario_id == usuario_id]
        return sorted(res, key=lambda f: f.id)

    def next_numero(self):
        n = self._num_seq
        self._num_seq += 1
        return f"FAC-{n:06d}"

    def create(self, compra_id, numero, fecha, xml, pdf_base64):
        if self.simulate_race_on_create:
            self.simulate_race_on_create = False
            # Another concurrent request won the insert first
            self._insert(compra_id, "FAC-999999", fecha, xml, pdf_base64)
            raise ConflictError("UniqueViolation simulado")
        if compra_id in self._by_compra:
            raise ConflictError("Duplicado")
        return self._insert(compra_id, numero, fecha, xml, pdf_base64)

    def _insert(self, compra_id, numero, fecha, xml, pdf_base64):
        fid = self._seq
        self._seq += 1
        f = Factura(
            id=fid,
            compra_id=compra_id,
            numero=numero,
            fecha=fecha,
            estado="EMITIDA",
            xml=xml,
            pdf_base64=pdf_base64,
            usuario_id=self._compra_owners.get(compra_id),
        )
        self._items[fid] = f
        self._by_compra[compra_id] = fid
        return f

    def anular(self, factura_id, expected_version=None):
        f = self._items.get(factura_id)
        if f is None:
            return None
        if f.estado == "ANULADA":
            raise ConflictError("La factura ya se encuentra anulada")
        if expected_version is not None and f.row_version != expected_version:
            raise ConflictError(
                "Conflicto de concurrencia: la factura fue modificada por otro usuario. Recarga e intenta nuevamente."
            )
        updated = Factura(
            id=f.id, compra_id=f.compra_id, numero=f.numero, fecha=f.fecha,
            estado="ANULADA", xml=f.xml, pdf_base64=f.pdf_base64, usuario_id=f.usuario_id,
            row_version=f.row_version + 1,
        )
        self._items[factura_id] = updated
        return updated


class FacturacionTestCase(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryFacturaRepo(compra_owners={10: 2, 20: 3})
        self.xml_svc = GenerarFacturaXmlService()
        self.pdf_svc = GenerarFacturaPdfService()

        self.app = create_app()
        container = self.app.extensions["container"]
        container.repo = self.repo
        container.xml_service = self.xml_svc
        container.pdf_service = self.pdf_svc
        container.emitir_factura = EmitirFacturaUseCase(self.repo, self.xml_svc, self.pdf_svc)
        container.listar_facturas = ListarFacturasUseCase(self.repo)
        container.obtener_factura = ObtenerFacturaUseCase(self.repo)
        container.anular_factura = AnularFacturaUseCase(self.repo)
        self.client = self.app.test_client()
        self.secret = self.app.config["SETTINGS"].jwt_secret_key

    def _headers(self, sub: int, rol: str):
        token = jwt.encode(
            {"sub": str(sub), "rol": rol, "nombre": f"User {sub}", "correo": f"u{sub}@test.com"},
            self.secret,
            algorithm="HS256",
        )
        return {"Authorization": f"Bearer {token}"}

    def test_xml_schema_and_decimal_round_half_up(self):
        fecha = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
        xml_str = self.xml_svc.generar(
            "FAC-000001",
            fecha,
            {"id": 2, "nombre": "Ana & <Luis>", "correo": "ana@test.com"},
            [{"descripcion": "Rock & Roll <VIP>", "cantidad": 3, "precio_unitario": "25.005", "subtotal": "75.015"}],
            {"subtotal": "75.00", "descuento": "3.75", "base_imponible": "71.25", "iva": "10.685", "total": "81.935"},
        )
        root = ET.fromstring(xml_str)
        self.assertEqual(root.tag, "Factura")
        self.assertEqual(root.findtext("Cabecera/Numero"), "FAC-000001")
        self.assertEqual(root.findtext("Cabecera/Estado"), "EMITIDA")
        self.assertEqual(root.findtext("Cliente/Nombre"), "Ana & <Luis>")
        self.assertEqual(root.findtext("Detalle/Item/PrecioUnitario"), "25.01")
        self.assertEqual(root.findtext("Detalle/Item/Subtotal"), "75.02")
        self.assertEqual(root.findtext("Totales/IVA"), "10.69")
        self.assertEqual(root.findtext("Totales/Total"), "81.94")

    def test_pdf_escapes_xml_special_characters_and_formats_decimal(self):
        fecha = datetime(2026, 5, 1, 12, 0, tzinfo=timezone.utc)
        pdf_bytes = self.pdf_svc.generar(
            "FAC-000001",
            fecha,
            {"id": 2, "nombre": "Rock & Roll <VIP> > 100%", "correo": "a&b<c>@test.com"},
            [{"descripcion": "Concierto A & B <Especial> > Pro", "cantidad": 3, "precio_unitario": "25.005", "subtotal": "75.015"}],
            {"subtotal": "75.00", "descuento": "3.75", "base_imponible": "71.25", "iva": "10.685", "total": "81.935"},
        )
        self.assertTrue(pdf_bytes.startswith(b"%PDF-"))
        self.assertEqual(self.pdf_svc._money("10.685"), "10.69")
        self.assertEqual(self.pdf_svc._money("1.005"), "1.01")

    def test_idempotent_emission_normal_and_concurrent(self):
        payload = {
            "compra_id": 10,
            "cliente": {"id": 2, "nombre": "Cliente", "correo": "c@test.com"},
            "items": [{"descripcion": "General", "cantidad": 3, "precio_unitario": 25.0, "subtotal": 75.0}],
            "totales": {"subtotal": 75.0, "descuento": 3.75, "base_imponible": 71.25, "iva": 10.69, "total": 81.94},
        }
        headers = self._headers(2, "CLIENTE")
        r1 = self.client.post("/api/factura", headers=headers, json=payload)
        r2 = self.client.post("/api/factura", headers=headers, json=payload)
        self.assertEqual(r1.status_code, 201)
        self.assertEqual(r2.status_code, 201)
        self.assertEqual(r1.get_json()["numero"], r2.get_json()["numero"])

        # Concurrent UniqueViolation / ConflictError returns existing cleanly
        self.repo.simulate_race_on_create = True
        payload2 = dict(payload, compra_id=20)
        r3 = self.client.post("/api/factura", headers=self._headers(3, "CLIENTE"), json=payload2)
        self.assertEqual(r3.status_code, 201)
        self.assertEqual(r3.get_json()["numero"], "FAC-999999")

    def test_invalid_compra_id_returns_400(self):
        headers = self._headers(1, "ADMIN")
        for bad_id in (True, False, 0, -5, "abc", 1.5):
            r = self.client.post("/api/factura", headers=headers, json={"compra_id": bad_id, "items": [{"a": 1}]})
            self.assertEqual(r.status_code, 400, f"Expected 400 for compra_id={bad_id}")
        self.assertEqual(self.client.get("/api/factura?compra_id=abc", headers=headers).status_code, 400)
        self.assertEqual(self.client.get("/api/factura?compra_id=0", headers=headers).status_code, 400)

    def test_auth_ownership_and_double_cancel_409(self):
        # Emit two invoices: compra 10 -> user 2, compra 20 -> user 3
        item = [{"descripcion": "General", "cantidad": 1, "precio_unitario": 25.0, "subtotal": 25.0}]
        tot = {"subtotal": 25.0, "descuento": 0, "base_imponible": 25.0, "iva": 3.75, "total": 28.75}
        f1 = self.client.post(
            "/api/factura", headers=self._headers(2, "CLIENTE"),
            json={"compra_id": 10, "cliente": {"id": 2, "nombre": "U2", "correo": "u2@t.com"}, "items": item, "totales": tot},
        ).get_json()
        f2 = self.client.post(
            "/api/factura", headers=self._headers(3, "CLIENTE"),
            json={"compra_id": 20, "cliente": {"id": 3, "nombre": "U3", "correo": "u3@t.com"}, "items": item, "totales": tot},
        ).get_json()

        # 401 without token on all 5 endpoints
        self.assertEqual(self.client.post("/api/factura", json={}).status_code, 401)
        self.assertEqual(self.client.get("/api/factura").status_code, 401)
        self.assertEqual(self.client.get(f"/api/factura/{f1['id']}/xml").status_code, 401)
        self.assertEqual(self.client.get(f"/api/factura/{f1['id']}/pdf").status_code, 401)
        self.assertEqual(self.client.patch(f"/api/factura/{f1['id']}/anular").status_code, 401)

        # GET /api/factura filters for CLIENTE, returns all for ADMIN
        c2_list = self.client.get("/api/factura", headers=self._headers(2, "CLIENTE")).get_json()
        self.assertEqual([x["id"] for x in c2_list], [f1["id"]])
        admin_list = self.client.get("/api/factura", headers=self._headers(1, "ADMIN")).get_json()
        self.assertEqual([x["id"] for x in admin_list], [f1["id"], f2["id"]])

        # Client 2 cannot access or cancel Client 3's invoice -> 403
        self.assertEqual(self.client.get(f"/api/factura/{f2['id']}/xml", headers=self._headers(2, "CLIENTE")).status_code, 403)
        self.assertEqual(self.client.get(f"/api/factura/{f2['id']}/pdf", headers=self._headers(2, "CLIENTE")).status_code, 403)
        self.assertEqual(self.client.patch(f"/api/factura/{f2['id']}/anular", headers=self._headers(2, "CLIENTE")).status_code, 403)

        # Owner can download XML & PDF, and ADMIN can download anyone's
        self.assertEqual(self.client.get(f"/api/factura/{f1['id']}/xml", headers=self._headers(2, "CLIENTE")).status_code, 200)
        self.assertEqual(self.client.get(f"/api/factura/{f1['id']}/pdf", headers=self._headers(2, "CLIENTE")).status_code, 200)
        self.assertEqual(self.client.get(f"/api/factura/{f2['id']}/xml", headers=self._headers(1, "ADMIN")).status_code, 200)

        # Owner cancels once -> 200, second cancel -> 409 Conflict
        r_cancel1 = self.client.patch(f"/api/factura/{f1['id']}/anular", headers=self._headers(2, "CLIENTE"))
        self.assertEqual(r_cancel1.status_code, 200)
        self.assertEqual(r_cancel1.get_json()["estado"], "ANULADA")
        self.assertEqual(r_cancel1.get_json()["row_version"], 2)
        r_cancel2 = self.client.patch(f"/api/factura/{f1['id']}/anular", headers=self._headers(2, "CLIENTE"))
        self.assertEqual(r_cancel2.status_code, 409)

    def test_anular_row_version_occ_conflict_and_postgres_sql(self):
        from src.infrastructure.db.postgres_repository import PostgresFacturaRepository

        item = [{"descripcion": "General", "cantidad": 1, "precio_unitario": 25.0, "subtotal": 25.0}]
        tot = {"subtotal": 25.0, "descuento": 0, "base_imponible": 25.0, "iva": 3.75, "total": 28.75}
        f1 = self.client.post(
            "/api/factura",
            headers=self._headers(2, "CLIENTE"),
            json={"compra_id": 10, "cliente": {"id": 2, "nombre": "U2", "correo": "u2@t.com"}, "items": item, "totales": tot},
        ).get_json()
        self.assertEqual(f1["row_version"], 1)

        # Stale row_version -> 409 Conflict
        r_stale = self.client.patch(
            f"/api/factura/{f1['id']}/anular",
            headers=self._headers(2, "CLIENTE"),
            json={"row_version": 99},
        )
        self.assertEqual(r_stale.status_code, 409)

        # Invalid row_version -> 400
        for bad_rv in (True, 0, -1, 1.5, "1🔥", "abc"):
            r_bad = self.client.patch(
                f"/api/factura/{f1['id']}/anular",
                headers=self._headers(2, "CLIENTE"),
                json={"row_version": bad_rv},
            )
            self.assertEqual(r_bad.status_code, 400, f"Expected 400 for row_version={bad_rv}")

        # Exact row_version -> 200 and increments row_version
        r_ok = self.client.patch(
            f"/api/factura/{f1['id']}/anular",
            headers=self._headers(2, "CLIENTE"),
            json={"row_version": 1},
        )
        self.assertEqual(r_ok.status_code, 200)
        self.assertEqual(r_ok.get_json()["estado"], "ANULADA")
        self.assertEqual(r_ok.get_json()["row_version"], 2)

        # Postgres repo atomic UPDATE ... AND row_version = %s RETURNING -> ConflictError on 0 rows
        pg_repo = PostgresFacturaRepository("postgresql://fake")
        mock_conn = MagicMock()
        mock_ctx = MagicMock()
        mock_ctx.__enter__.return_value = mock_conn
        mock_ctx.__exit__.return_value = False
        mock_conn.execute.return_value.fetchone.side_effect = [
            None,
            {
                "id": 1, "compra_id": 10, "numero": "FAC-000001",
                "fecha": datetime.now(timezone.utc), "estado": "EMITIDA",
                "row_version": 2, "usuario_id": 2, "xml": "", "pdf_base64": "",
            },
        ]
        with patch("src.infrastructure.db.postgres_repository.get_connection", return_value=mock_ctx):
            with self.assertRaises(ConflictError):
                pg_repo.anular(1, expected_version=1)
        sql, params = mock_conn.execute.call_args_list[0][0]
        self.assertIn("row_version = row_version + 1", sql)
        self.assertIn("WHERE id = %s AND estado = 'EMITIDA' AND row_version = %s RETURNING", sql)
        self.assertEqual(params, (1, 1))

    def test_reject_emojis_and_invalid_numeric_fields_400(self):
        headers = self._headers(2, "CLIENTE")
        base_item = {"descripcion": "General", "cantidad": 1, "precio_unitario": 25.0, "subtotal": 25.0}
        base_tot = {"subtotal": 25.0, "descuento": 0, "base_imponible": 25.0, "iva": 3.75, "total": 28.75}
        base_cli = {"id": 2, "nombre": "Ana Perez", "correo": "ana@test.com"}

        bad_payloads = [
            {"compra_id": 10, "cliente": {**base_cli, "nombre": "Ana 😀"}, "items": [base_item], "totales": base_tot},
            {"compra_id": 10, "cliente": {**base_cli, "correo": "ana🔥@test.com"}, "items": [base_item], "totales": base_tot},
            {"compra_id": 10, "cliente": base_cli, "items": [{**base_item, "descripcion": "VIP 🎫"}], "totales": base_tot},
            {"compra_id": "10😀", "cliente": base_cli, "items": [base_item], "totales": base_tot},
            {"compra_id": 10, "cliente": base_cli, "items": [{**base_item, "cantidad": True}], "totales": base_tot},
            {"compra_id": 10, "cliente": base_cli, "items": [{**base_item, "cantidad": 0}], "totales": base_tot},
            {"compra_id": 10, "cliente": base_cli, "items": [{**base_item, "cantidad": 1.5}], "totales": base_tot},
            {"compra_id": 10, "cliente": base_cli, "items": [{**base_item, "precio_unitario": -1}], "totales": base_tot},
            {"compra_id": 10, "cliente": base_cli, "items": [{**base_item, "subtotal": "abc"}], "totales": base_tot},
            {"compra_id": 10, "cliente": base_cli, "items": [base_item], "totales": {**base_tot, "total": -5}},
            {"compra_id": 10, "cliente": base_cli, "items": [base_item], "totales": {**base_tot, "iva": True}},
            {"compra_id": 10, "cliente": base_cli, "items": [base_item], "totales": {**base_tot, "subtotal": "10💰"}},
        ]
        for payload in bad_payloads:
            resp = self.client.post("/api/factura", headers=headers, json=payload)
            self.assertEqual(resp.status_code, 400, f"Expected 400 for {payload}")


if __name__ == "__main__":
    unittest.main()
