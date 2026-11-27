"""Pruebas unitarias para API Compras (:5000 — Orquestador SAGA)."""
from datetime import datetime, timezone
from decimal import Decimal
import unittest

import jwt

from app import create_app
from src.application.use_cases.compra_use_cases import (
    AnularCompraUseCase,
    CrearCompraUseCase,
    EstadisticasComprasUseCase,
    ListarComprasUseCase,
    ObtenerCompraUseCase,
)
from src.application.use_cases.previsualizar_use_cases import (
    PrevisualizarCompraUseCase,
    normalize_items,
)
from src.domain.entities import Compra, DetalleCompra
from src.domain.exceptions import (
    ConflictError,
    ForbiddenError,
    ServiceUnavailableError,
    ValidationError,
)
from src.domain.repositories import (
    CompraRepository,
    EventosGateway,
    FacturacionGateway,
    PromocionesGateway,
)


class InMemoryCompraRepo(CompraRepository):
    def __init__(self):
        self._compras = {}
        self._by_solicitud = {}
        self._seq = 1
        self.fail_create_with = None
        self.insert_concurrent_on_fail = None
        self.fail_transition = False

    def find_by_solicitud_id(self, solicitud_id):
        cid = self._by_solicitud.get(solicitud_id)
        return self._compras.get(cid) if cid is not None else None

    def find_by_id(self, compra_id):
        return self._compras.get(compra_id)

    def list_all(self, usuario_id=None):
        res = list(self._compras.values())
        if usuario_id is not None:
            res = [c for c in res if c.usuario_id == usuario_id]
        return sorted(res, key=lambda c: c.id, reverse=True)

    def create(self, usuario_id, solicitud_id, subtotal, descuento, base_imponible, iva, total, estado, detalles):
        if self.fail_create_with is not None:
            err = self.fail_create_with
            self.fail_create_with = None
            if self.insert_concurrent_on_fail is not None:
                c = self.insert_concurrent_on_fail
                self.insert_concurrent_on_fail = None
                self._compras[c.id] = c
                self._by_solicitud[c.solicitud_id] = c.id
            raise err
        cid = self._seq
        self._seq += 1
        det_objs = [
            DetalleCompra(
                id=i + 1,
                compra_id=cid,
                tipo_entrada_id=d["tipo_entrada_id"],
                cantidad=d["cantidad"],
                precio_unitario=Decimal(str(d["precio_unitario"])),
                subtotal=Decimal(str(d["subtotal"])),
            )
            for i, d in enumerate(detalles)
        ]
        compra = Compra(
            id=cid,
            usuario_id=usuario_id,
            solicitud_id=solicitud_id,
            fecha=datetime.now(timezone.utc),
            subtotal=Decimal(str(subtotal)),
            descuento=Decimal(str(descuento)),
            base_imponible=Decimal(str(base_imponible)),
            iva=Decimal(str(iva)),
            total=Decimal(str(total)),
            estado=estado,
            detalles=det_objs,
        )
        self._compras[cid] = compra
        self._by_solicitud[solicitud_id] = cid
        return compra

    def update_estado(self, compra_id, estado):
        c = self._compras[compra_id]
        self._compras[compra_id] = Compra(
            id=c.id, usuario_id=c.usuario_id, solicitud_id=c.solicitud_id, fecha=c.fecha,
            subtotal=c.subtotal, descuento=c.descuento, base_imponible=c.base_imponible,
            iva=c.iva, total=c.total, estado=estado, detalles=c.detalles,
        )

    def transition_estado(self, compra_id, from_estado, to_estado):
        if self.fail_transition:
            return False
        c = self._compras.get(compra_id)
        if c is None or c.estado != from_estado:
            return False
        self.update_estado(compra_id, to_estado)
        return True

    def estadisticas(self):
        return {"total_compras": len(self._compras)}

    def anular(self, compra_id):
        self.update_estado(compra_id, "ANULADA")
        return self._compras[compra_id]


class FakeEventosGateway(EventosGateway):
    def __init__(self):
        self.descontados = []
        self.restaurados = []
        self.fail_restaurar = False

    def cotizar(self, items):
        out = []
        total = 0.0
        for it in items:
            sub = round(it["cantidad"] * 25.0, 2)
            total += sub
            out.append({
                "tipo_entrada_id": it["tipo_entrada_id"],
                "evento_nombre": "Rock Fest",
                "tipo": "General",
                "cantidad_solicitada": it["cantidad"],
                "precio_unitario": 25.0,
                "subtotal": sub,
                "disponible": True,
            })
        return {"items": out, "subtotal_total": total}

    def descontar(self, items, auth_header=""):
        self.descontados.append((items, auth_header))
        return {"ok": True}

    def restaurar(self, items, auth_header=""):
        if self.fail_restaurar:
            raise ServiceUnavailableError("Eventos caído")
        self.restaurados.append((items, auth_header))
        return {"ok": True}


class FakePromocionesGateway(PromocionesGateway):
    def calcular(self, subtotal, cantidad_total):
        return {
            "subtotal": 75.0,
            "cantidad_total": cantidad_total,
            "porcentaje_descuento": 5.0,
            "descuento": 3.75,
            "base_imponible": 71.25,
            "iva": 10.69,
            "total": 81.94,
        }


class FakeFacturacionGateway(FacturacionGateway):
    def __init__(self):
        self.facturas = {}
        self.emit_calls = []
        self.anular_calls = []
        self.buscar_calls = []
        self.fail_emitir = False
        self.fail_anular = False

    def emitir(self, compra_id, cliente, items, totales, auth_header=""):
        self.emit_calls.append((compra_id, auth_header))
        if self.fail_emitir:
            raise ServiceUnavailableError("Facturación caída")
        f = {"id": compra_id, "compra_id": compra_id, "numero": f"FAC-{compra_id:06d}", "estado": "EMITIDA"}
        self.facturas[compra_id] = f
        return f

    def buscar_por_compra(self, compra_id, auth_header=""):
        self.buscar_calls.append((compra_id, auth_header))
        return self.facturas.get(compra_id)

    def anular_por_compra(self, compra_id, auth_header=""):
        self.anular_calls.append((compra_id, auth_header))
        if self.fail_anular:
            raise ServiceUnavailableError("Facturación caída al anular")
        if compra_id in self.facturas:
            self.facturas[compra_id]["estado"] = "ANULADA"


class ComprasSagaTestCase(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryCompraRepo()
        self.eventos_gw = FakeEventosGateway()
        self.promociones_gw = FakePromocionesGateway()
        self.facturacion_gw = FakeFacturacionGateway()

        self.crear_uc = CrearCompraUseCase(self.repo, self.eventos_gw, self.promociones_gw, self.facturacion_gw)
        self.anular_uc = AnularCompraUseCase(self.repo, self.eventos_gw, self.facturacion_gw)

        self.app = create_app()
        container = self.app.extensions["container"]
        container.repo = self.repo
        container.eventos_gw = self.eventos_gw
        container.promociones_gw = self.promociones_gw
        container.facturacion_gw = self.facturacion_gw
        container.previsualizar = PrevisualizarCompraUseCase(self.eventos_gw, self.promociones_gw)
        container.crear_compra = self.crear_uc
        container.listar_compras = ListarComprasUseCase(self.repo)
        container.obtener_compra = ObtenerCompraUseCase(self.repo)
        container.estadisticas = EstadisticasComprasUseCase(self.repo)
        container.anular_compra = self.anular_uc
        self.client = self.app.test_client()
        self.secret = self.app.config["SETTINGS"].jwt_secret_key

    def _headers(self, sub: int, rol: str = "CLIENTE"):
        token = jwt.encode(
            {"sub": str(sub), "rol": rol, "nombre": f"User {sub}", "correo": f"u{sub}@test.com"},
            self.secret,
            algorithm="HS256",
        )
        return {"Authorization": f"Bearer {token}"}

    def test_normalize_items_aggregation_and_validation(self):
        res = normalize_items([
            {"tipo_entrada_id": 1, "cantidad": 2},
            {"tipo_entrada_id": 2, "cantidad": 1},
            {"tipo_entrada_id": 1, "cantidad": 1},
        ])
        self.assertEqual(res, [{"tipo_entrada_id": 1, "cantidad": 3}, {"tipo_entrada_id": 2, "cantidad": 1}])

        for bad in (
            [],
            "not-a-list",
            [123],
            [{"tipo_entrada_id": True, "cantidad": 1}],
            [{"tipo_entrada_id": 1, "cantidad": True}],
            [{"tipo_entrada_id": 0, "cantidad": 1}],
            [{"tipo_entrada_id": 1, "cantidad": 0}],
            [{"tipo_entrada_id": 1, "cantidad": -2}],
            [{"tipo_entrada_id": 1.5, "cantidad": 2}],
        ):
            with self.assertRaises(ValidationError):
                normalize_items(bad)

    def test_saga_happy_path_and_auth_forwarding(self):
        headers = self._headers(2)
        resp = self.client.post(
            "/api/compras",
            headers=headers,
            json={"solicitud_id": "sol-1", "items": [{"tipo_entrada_id": 1, "cantidad": 3}]},
        )
        self.assertEqual(resp.status_code, 201)
        body = resp.get_json()
        self.assertEqual(body["estado"], "CONFIRMADA")
        self.assertEqual(body["factura"]["numero"], "FAC-000001")
        # Auth header forwarded to Eventos & Facturación
        self.assertEqual(self.eventos_gw.descontados[0][1], headers["Authorization"])
        self.assertEqual(self.facturacion_gw.emit_calls[0][1], headers["Authorization"])

    def test_saga_compensation_on_billing_failure(self):
        self.facturacion_gw.fail_emitir = True
        headers = self._headers(2)
        resp = self.client.post(
            "/api/compras",
            headers=headers,
            json={"solicitud_id": "sol-fail", "items": [{"tipo_entrada_id": 1, "cantidad": 3}]},
        )
        self.assertEqual(resp.status_code, 503)
        self.assertEqual(len(self.eventos_gw.restaurados), 1)
        self.assertEqual(self.eventos_gw.restaurados[0][1], headers["Authorization"])
        compra = self.repo.find_by_solicitud_id("sol-fail")
        self.assertEqual(compra.estado, "FALLIDA")

    def test_step5_failure_compensates_stock_and_handles_concurrent_duplicate(self):
        # Generic DB error -> restores stock and propagates error
        self.repo.fail_create_with = RuntimeError("DB timeout")
        with self.assertRaises(RuntimeError):
            self.crear_uc.execute({"sub": 2, "nombre": "U2", "correo": "u2@t.com"}, "sol-db-err", [{"tipo_entrada_id": 1, "cantidad": 3}], auth_header="Bearer tok")
        self.assertEqual(len(self.eventos_gw.restaurados), 1)
        self.assertEqual(self.eventos_gw.restaurados[0][1], "Bearer tok")

        # Concurrent UniqueViolation -> restores stock AND returns existing purchase with factura
        existing = Compra(
            id=99, usuario_id=2, solicitud_id="sol-race", fecha=datetime.now(timezone.utc),
            subtotal=Decimal("75.00"), descuento=Decimal("3.75"), base_imponible=Decimal("71.25"),
            iva=Decimal("10.69"), total=Decimal("81.94"), estado="CONFIRMADA", detalles=[],
        )
        self.facturacion_gw.facturas[99] = {"id": 99, "compra_id": 99, "numero": "FAC-000099", "estado": "EMITIDA"}
        self.repo.fail_create_with = RuntimeError("UniqueViolation")
        self.repo.insert_concurrent_on_fail = existing

        res, created = self.crear_uc.execute(
            {"sub": 2, "nombre": "U2", "correo": "u2@t.com"}, "sol-race", [{"tipo_entrada_id": 1, "cantidad": 3}], auth_header="Bearer tok"
        )
        self.assertFalse(created)
        self.assertEqual(res["id"], 99)
        self.assertEqual(res["factura"]["numero"], "FAC-000099")
        self.assertEqual(len(self.eventos_gw.restaurados), 2)

    def test_idempotent_replay_returns_factura_and_enforces_owner(self):
        h2 = self._headers(2)
        h3 = self._headers(3)
        r1 = self.client.post("/api/compras", headers=h2, json={"solicitud_id": "sol-idem", "items": [{"tipo_entrada_id": 1, "cantidad": 3}]})
        self.assertEqual(r1.status_code, 201)

        # Same user replay -> 200 with factura
        r2 = self.client.post("/api/compras", headers=h2, json={"solicitud_id": "sol-idem", "items": [{"tipo_entrada_id": 1, "cantidad": 3}]})
        self.assertEqual(r2.status_code, 200)
        self.assertEqual(r2.get_json()["factura"]["numero"], "FAC-000001")
        self.assertEqual(len(self.eventos_gw.descontados), 1)

        # Different user replay -> 403 Forbidden
        r3 = self.client.post("/api/compras", headers=h3, json={"solicitud_id": "sol-idem", "items": [{"tipo_entrada_id": 1, "cantidad": 3}]})
        self.assertEqual(r3.status_code, 403)

    def test_controlled_cancel_rules_and_error_handling(self):
        h2 = self._headers(2)
        c_resp = self.client.post("/api/compras", headers=h2, json={"solicitud_id": "sol-c1", "items": [{"tipo_entrada_id": 1, "cantidad": 3}]})
        cid = c_resp.get_json()["id"]

        # Cancel confirmed -> 200, stock restored, invoice cancelled with auth_header
        r1 = self.client.patch(f"/api/compras/{cid}/anular", headers=h2)
        self.assertEqual(r1.status_code, 200)
        self.assertEqual(r1.get_json()["estado"], "ANULADA")
        self.assertEqual(len(self.eventos_gw.restaurados), 1)
        self.assertEqual(self.facturacion_gw.anular_calls[0], (cid, h2["Authorization"]))

        # Double cancel -> 409 Conflict, stock NOT restored again
        r2 = self.client.patch(f"/api/compras/{cid}/anular", headers=h2)
        self.assertEqual(r2.status_code, 409)
        self.assertEqual(len(self.eventos_gw.restaurados), 1)

        # Cannot cancel FALLIDA -> 409 Conflict, stock NOT restored
        failed = self.repo.create(
            usuario_id=2, solicitud_id="sol-failed", subtotal=75, descuento=0,
            base_imponible=75, iva=11.25, total=86.25, estado="FALLIDA",
            detalles=[{"tipo_entrada_id": 1, "cantidad": 3, "precio_unitario": 25, "subtotal": 75}],
        )
        r_fail = self.client.patch(f"/api/compras/{failed.id}/anular", headers=h2)
        self.assertEqual(r_fail.status_code, 409)
        self.assertEqual(len(self.eventos_gw.restaurados), 1)

        # Failure in restaurar reverts compra back to CONFIRMADA and returns 503
        c2_id = self.client.post("/api/compras", headers=h2, json={"solicitud_id": "sol-c2", "items": [{"tipo_entrada_id": 1, "cantidad": 3}]}).get_json()["id"]
        self.eventos_gw.fail_restaurar = True
        r_err = self.client.patch(f"/api/compras/{c2_id}/anular", headers=h2)
        self.assertEqual(r_err.status_code, 503)
        self.assertEqual(self.repo.find_by_id(c2_id).estado, "CONFIRMADA")
        self.eventos_gw.fail_restaurar = False

        # Failure in facturacion anular compensates stock & reverts CONFIRMADA -> 503
        self.facturacion_gw.fail_anular = True
        descontados_before = len(self.eventos_gw.descontados)
        r_ferr = self.client.patch(f"/api/compras/{c2_id}/anular", headers=h2)
        self.assertEqual(r_ferr.status_code, 503)
        self.assertEqual(self.repo.find_by_id(c2_id).estado, "CONFIRMADA")
        self.assertEqual(len(self.eventos_gw.descontados), descontados_before + 1)
        self.facturacion_gw.fail_anular = False

        # Atomic race condition where transition_estado returns False -> 409
        self.repo.fail_transition = True
        with self.assertRaises(ConflictError):
            self.anular_uc.execute(c2_id)


if __name__ == "__main__":
    unittest.main()
