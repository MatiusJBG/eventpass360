"""Pruebas unitarias de 04_API_Eventos (casos de uso + rutas HTTP con fakes en memoria)."""
from datetime import datetime, timezone
from decimal import Decimal
import unittest

import jwt

from app import create_app
from src.config.container import Container
from src.config.settings import Settings
from src.domain.entities import Categoria, Evento, TipoEntrada
from src.domain.exceptions import ConflictError
from src.domain.repositories import (
    CategoriaRepository,
    EventoRepository,
    StockRepository,
    TipoEntradaRepository,
)

OCC_CONFLICT_MSG = (
    "Conflicto de concurrencia: el registro fue modificado por otro usuario. Recarga e intenta nuevamente."
)


class FakeCategoriaRepository(CategoriaRepository):
    def __init__(self):
        self._items: dict[int, Categoria] = {
            1: Categoria(id=1, nombre="Conciertos", descripcion="Música en vivo", estado=True),
        }
        self._next_id = 2
        self.evento_counts: dict[int, int] = {}

    def list(self):
        return [self._items[k] for k in sorted(self._items)]

    def find_by_id(self, categoria_id: int):
        return self._items.get(categoria_id)

    def find_by_nombre(self, nombre: str):
        for c in self._items.values():
            if c.nombre == nombre:
                return c
        return None

    def create(self, nombre: str, descripcion: str) -> Categoria:
        cat = Categoria(id=self._next_id, nombre=nombre, descripcion=descripcion, estado=True)
        self._items[cat.id] = cat
        self._next_id += 1
        return cat

    def update(self, categoria_id: int, nombre=None, descripcion=None, estado=None, expected_version=None) -> Categoria:
        c = self._items[categoria_id]
        if expected_version is not None and c.row_version != expected_version:
            raise ConflictError(OCC_CONFLICT_MSG)
        updated = Categoria(
            id=c.id,
            nombre=nombre if nombre is not None else c.nombre,
            descripcion=descripcion if descripcion is not None else c.descripcion,
            estado=estado if estado is not None else c.estado,
            row_version=c.row_version + 1,
        )
        self._items[categoria_id] = updated
        return updated

    def count_eventos(self, categoria_id: int) -> int:
        return self.evento_counts.get(categoria_id, 0)

    def delete(self, categoria_id: int) -> None:
        self._items.pop(categoria_id, None)

    def deactivate(self, categoria_id: int) -> None:
        c = self._items[categoria_id]
        self._items[categoria_id] = Categoria(
            id=c.id, nombre=c.nombre, descripcion=c.descripcion, estado=False, row_version=c.row_version + 1
        )


class FakeEventoRepository(EventoRepository):
    def __init__(self, cat_repo: FakeCategoriaRepository, tipo_repo=None):
        self._cat_repo = cat_repo
        self._tipo_repo = tipo_repo
        self._items: dict[int, Evento] = {}
        self._next_id = 1

    def list(self, q=None, categoria_id=None, incluir_inactivos=False):
        res = []
        for k in sorted(self._items):
            e = self._items[k]
            if not incluir_inactivos and not e.estado:
                continue
            if categoria_id is not None and e.categoria_id != categoria_id:
                continue
            if q and q.lower() not in e.nombre.lower() and q.lower() not in e.descripcion.lower():
                continue
            res.append(e)
        return res

    def find_by_id(self, evento_id: int):
        return self._items.get(evento_id)

    def create(self, categoria_id: int, nombre: str, descripcion: str, lugar: str, fecha, imagen_url: str) -> Evento:
        cat = self._cat_repo.find_by_id(categoria_id)
        ev = Evento(
            id=self._next_id,
            categoria_id=categoria_id,
            nombre=nombre,
            descripcion=descripcion,
            lugar=lugar,
            fecha=fecha,
            imagen_url=imagen_url,
            estado=True,
            categoria_nombre=cat.nombre if cat else None,
        )
        self._items[ev.id] = ev
        self._next_id += 1
        return ev

    def update(self, evento_id: int, expected_version=None, **fields) -> Evento:
        e = self._items[evento_id]
        if expected_version is not None and e.row_version != expected_version:
            raise ConflictError(OCC_CONFLICT_MSG)
        cat_id = fields.get("categoria_id", e.categoria_id)
        cat = self._cat_repo.find_by_id(cat_id)
        updated = Evento(
            id=e.id,
            categoria_id=cat_id,
            nombre=fields.get("nombre", e.nombre),
            descripcion=fields.get("descripcion", e.descripcion),
            lugar=fields.get("lugar", e.lugar),
            fecha=fields.get("fecha", e.fecha),
            imagen_url=fields.get("imagen_url", e.imagen_url),
            estado=fields.get("estado", e.estado),
            categoria_nombre=cat.nombre if cat else None,
            row_version=e.row_version + 1,
        )
        self._items[evento_id] = updated
        return updated

    def delete(self, evento_id: int) -> None:
        # Mirrors PostgresEventoRepository.delete: delete child tipos_entrada first, then evento
        if self._tipo_repo is not None:
            for tid in [t.id for t in self._tipo_repo.list(evento_id=evento_id)]:
                self._tipo_repo.delete(tid)
        self._items.pop(evento_id, None)

    def deactivate(self, evento_id: int) -> None:
        self.update(evento_id, estado=False)


class FakeTipoEntradaRepository(TipoEntradaRepository):
    def __init__(self, evento_repo: FakeEventoRepository):
        self._evento_repo = evento_repo
        self._items: dict[int, TipoEntrada] = {}
        self._next_id = 1
        self.detalles_counts: dict[int, int] = {}

    def list(self, evento_id=None):
        res = []
        for k in sorted(self._items):
            t = self._items[k]
            if evento_id is not None and t.evento_id != evento_id:
                continue
            res.append(t)
        return res

    def find_by_id(self, tipo_id: int):
        return self._items.get(tipo_id)

    def find_by_evento_tipo(self, evento_id: int, tipo: str):
        for t in self._items.values():
            if t.evento_id == evento_id and t.tipo == tipo:
                return t
        return None

    def create(self, evento_id: int, tipo: str, precio: Decimal, stock: int) -> TipoEntrada:
        ev = self._evento_repo.find_by_id(evento_id)
        te = TipoEntrada(
            id=self._next_id,
            evento_id=evento_id,
            tipo=tipo,
            precio=precio,
            stock=stock,
            estado=True,
            evento_nombre=ev.nombre if ev else None,
        )
        self._items[te.id] = te
        self._next_id += 1
        return te

    def update(self, tipo_id: int, expected_version=None, **fields) -> TipoEntrada:
        t = self._items[tipo_id]
        if expected_version is not None and t.row_version != expected_version:
            raise ConflictError(OCC_CONFLICT_MSG)
        updated = TipoEntrada(
            id=t.id,
            evento_id=t.evento_id,
            tipo=fields.get("tipo", t.tipo),
            precio=fields.get("precio", t.precio),
            stock=fields.get("stock", t.stock),
            estado=fields.get("estado", t.estado),
            evento_nombre=t.evento_nombre,
            row_version=t.row_version + 1,
        )
        self._items[tipo_id] = updated
        return updated

    def delete(self, tipo_id: int) -> None:
        self._items.pop(tipo_id, None)

    def deactivate(self, tipo_id: int) -> None:
        self.update(tipo_id, estado=False)

    def count_detalles(self, tipo_id: int) -> int:
        return self.detalles_counts.get(tipo_id, 0)


class FakeStockRepository(StockRepository):
    def __init__(self, evento_repo: FakeEventoRepository, tipo_repo: FakeTipoEntradaRepository):
        self._evento_repo = evento_repo
        self._tipo_repo = tipo_repo
        self.last_cotizar_items = None
        self.last_descontar_items = None
        self.last_restaurar_items = None

    def cotizar(self, items: list[dict]) -> dict:
        self.last_cotizar_items = items
        result_items = []
        subtotal_total = Decimal("0")
        for it in items:
            t = self._tipo_repo.find_by_id(it["tipo_entrada_id"])
            if t is None:
                result_items.append({
                    "tipo_entrada_id": it["tipo_entrada_id"], "evento_id": None, "evento_nombre": None,
                    "tipo": None, "precio_unitario": 0.0, "stock_disponible": 0,
                    "cantidad_solicitada": it["cantidad"], "disponible": False, "subtotal": 0.0,
                })
                continue
            ev = self._evento_repo.find_by_id(t.evento_id)
            disponible = bool(t.estado) and bool(ev and ev.estado) and t.stock >= it["cantidad"]
            subtotal = t.precio * it["cantidad"]
            result_items.append({
                "tipo_entrada_id": t.id, "evento_id": t.evento_id, "evento_nombre": ev.nombre if ev else None,
                "tipo": t.tipo, "precio_unitario": float(t.precio), "stock_disponible": t.stock,
                "cantidad_solicitada": it["cantidad"], "disponible": disponible, "subtotal": float(subtotal),
            })
            if disponible:
                subtotal_total += subtotal
        return {"items": result_items, "subtotal_total": float(subtotal_total)}

    def descontar(self, items: list[dict]) -> None:
        self.last_descontar_items = items
        # Atomic check first
        for it in items:
            t = self._tipo_repo.find_by_id(it["tipo_entrada_id"])
            ev = self._evento_repo.find_by_id(t.evento_id) if t else None
            if t is None or not t.estado or ev is None or not ev.estado or t.stock < it["cantidad"]:
                raise ConflictError("Stock insuficiente o tipo de entrada no disponible")
        for it in items:
            t = self._tipo_repo.find_by_id(it["tipo_entrada_id"])
            self._tipo_repo.update(t.id, stock=t.stock - it["cantidad"])

    def restaurar(self, items: list[dict]) -> None:
        self.last_restaurar_items = items
        for it in items:
            t = self._tipo_repo.find_by_id(it["tipo_entrada_id"])
            if t is not None:
                self._tipo_repo.update(t.id, stock=t.stock + it["cantidad"])


class EventosApiTestCase(unittest.TestCase):
    def setUp(self):
        self.settings = Settings(
            database_url="postgresql://fake",
            jwt_secret_key="test-secret-eventos-32-bytes-min!",
            cors_origins="*",
        )
        self.cat_repo = FakeCategoriaRepository()
        self.evento_repo = FakeEventoRepository(self.cat_repo)
        self.tipo_repo = FakeTipoEntradaRepository(self.evento_repo)
        self.evento_repo._tipo_repo = self.tipo_repo
        self.stock_repo = FakeStockRepository(self.evento_repo, self.tipo_repo)

        self.container = Container(
            settings=self.settings,
            categoria_repo=self.cat_repo,
            evento_repo=self.evento_repo,
            tipo_entrada_repo=self.tipo_repo,
            stock_repo=self.stock_repo,
        )
        self.app = create_app(container=self.container, settings=self.settings)
        self.client = self.app.test_client()

        self.evento = self.evento_repo.create(
            1, "Rock Fest", "Festival", "Estadio", datetime(2026, 12, 1, 20, 0, tzinfo=timezone.utc), "https://img/1.jpg"
        )
        self.vip = self.tipo_repo.create(self.evento.id, "VIP", Decimal("100.00"), 10)
        self.general = self.tipo_repo.create(self.evento.id, "General", Decimal("40.00"), 50)

    def _auth_header(self, rol: str = "ADMIN") -> dict:
        token = jwt.encode(
            {"sub": "1", "rol": rol, "nombre": "User", "correo": "u@test.com"},
            self.settings.jwt_secret_key,
            algorithm="HS256",
        )
        return {"Authorization": f"Bearer {token}"}

    # --- Categorías ---
    def test_categoria_update_validation_and_strip(self):
        headers = self._auth_header("ADMIN")

        self.assertEqual(self.client.put("/api/categorias/1", headers=headers, json={"nombre": ""}).status_code, 400)
        self.assertEqual(self.client.put("/api/categorias/1", headers=headers, json={"nombre": "   "}).status_code, 400)
        self.assertEqual(self.client.put("/api/categorias/1", headers=headers, json={}).status_code, 400)

        r_ok = self.client.put("/api/categorias/1", headers=headers, json={"nombre": "  Música  "})
        self.assertEqual(r_ok.status_code, 200)
        self.assertEqual(r_ok.get_json()["nombre"], "Música")

    def test_categoria_delete_soft_and_hard(self):
        headers = self._auth_header("ADMIN")
        self.cat_repo.evento_counts[1] = 2
        r_soft = self.client.delete("/api/categorias/1", headers=headers)
        self.assertEqual(r_soft.status_code, 200)
        self.assertFalse(self.cat_repo.find_by_id(1).estado)

        cat2 = self.cat_repo.create("Teatro", "Obras")
        r_hard = self.client.delete(f"/api/categorias/{cat2.id}", headers=headers)
        self.assertEqual(r_hard.status_code, 200)
        self.assertIsNone(self.cat_repo.find_by_id(cat2.id))

    # --- Eventos ---
    def test_evento_delete_without_compras_deletes_children_and_event(self):
        headers = self._auth_header("ADMIN")
        r = self.client.delete(f"/api/eventos/{self.evento.id}", headers=headers)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["accion"], "eliminado")
        self.assertIsNone(self.evento_repo.find_by_id(self.evento.id))
        self.assertEqual(self.tipo_repo.list(evento_id=self.evento.id), [])

    def test_evento_delete_with_compras_deactivates(self):
        headers = self._auth_header("ADMIN")
        self.tipo_repo.detalles_counts[self.vip.id] = 1
        r = self.client.delete(f"/api/eventos/{self.evento.id}", headers=headers)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.get_json()["accion"], "desactivado")
        ev = self.evento_repo.find_by_id(self.evento.id)
        self.assertIsNotNone(ev)
        self.assertFalse(ev.estado)

    def test_evento_invalid_categoria_id_returns_400(self):
        self.assertEqual(self.client.get("/api/eventos?categoria_id=abc").status_code, 400)
        self.assertEqual(self.client.get("/api/eventos?categoria_id=0").status_code, 400)

        headers = self._auth_header("ADMIN")
        for bad_cat in (True, "abc", 0, -1, None):
            r = self.client.post(
                "/api/eventos",
                headers=headers,
                json={
                    "categoria_id": bad_cat,
                    "nombre": "Show",
                    "lugar": "Arena",
                    "fecha": "2026-12-05T19:00:00Z",
                    "imagen_url": "https://img/x.jpg",
                },
            )
            self.assertEqual(r.status_code, 400, f"Expected 400 for categoria_id={bad_cat!r}")

    # --- Tipos de Entrada ---
    def test_tipo_entrada_update_duplicate_rejected(self):
        headers = self._auth_header("ADMIN")
        r_dup = self.client.put(f"/api/tipos-entrada/{self.general.id}", headers=headers, json={"tipo": "  VIP  "})
        self.assertEqual(r_dup.status_code, 409)

        # Updating own name to same name is allowed
        r_same = self.client.put(f"/api/tipos-entrada/{self.general.id}", headers=headers, json={"tipo": "General"})
        self.assertEqual(r_same.status_code, 200)

    def test_tipo_entrada_invalid_ints_return_400(self):
        self.assertEqual(self.client.get("/api/tipos-entrada?evento_id=abc").status_code, 400)

        headers = self._auth_header("ADMIN")
        self.assertEqual(
            self.client.post(
                "/api/tipos-entrada",
                headers=headers,
                json={"evento_id": True, "tipo": "Palco", "precio": 50, "stock": 5},
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                "/api/tipos-entrada",
                headers=headers,
                json={"evento_id": self.evento.id, "tipo": "Palco", "precio": 50, "stock": "muchos"},
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.put(
                f"/api/tipos-entrada/{self.vip.id}",
                headers=headers,
                json={"stock": True},
            ).status_code,
            400,
        )

    # --- Stock ---
    def test_stock_auth_guard_on_descontar_and_restaurar(self):
        payload = {"items": [{"tipo_entrada_id": self.vip.id, "cantidad": 2}]}

        # cotizar stays public
        self.assertEqual(self.client.post("/api/stock/cotizar", json=payload).status_code, 200)
        # descontar and restaurar require auth
        self.assertEqual(self.client.post("/api/stock/descontar", json=payload).status_code, 401)
        self.assertEqual(self.client.post("/api/stock/restaurar", json=payload).status_code, 401)

        headers = self._auth_header("CLIENTE")
        self.assertEqual(self.client.post("/api/stock/descontar", headers=headers, json=payload).status_code, 200)
        self.assertEqual(self.tipo_repo.find_by_id(self.vip.id).stock, 8)
        self.assertEqual(self.client.post("/api/stock/restaurar", headers=headers, json=payload).status_code, 200)
        self.assertEqual(self.tipo_repo.find_by_id(self.vip.id).stock, 10)

    def test_stock_duplicate_aggregation_across_operations(self):
        dup_payload = {
            "items": [
                {"tipo_entrada_id": self.vip.id, "cantidad": 3},
                {"tipo_entrada_id": self.general.id, "cantidad": 2},
                {"tipo_entrada_id": self.vip.id, "cantidad": 4},
            ]
        }
        r_cot = self.client.post("/api/stock/cotizar", json=dup_payload)
        self.assertEqual(r_cot.status_code, 200)
        self.assertEqual(
            self.stock_repo.last_cotizar_items,
            [{"tipo_entrada_id": self.vip.id, "cantidad": 7}, {"tipo_entrada_id": self.general.id, "cantidad": 2}],
        )
        self.assertEqual(r_cot.get_json()["subtotal_total"], 780.0)

        headers = self._auth_header("CLIENTE")
        r_desc = self.client.post("/api/stock/descontar", headers=headers, json=dup_payload)
        self.assertEqual(r_desc.status_code, 200)
        self.assertEqual(self.tipo_repo.find_by_id(self.vip.id).stock, 3)
        self.assertEqual(self.tipo_repo.find_by_id(self.general.id).stock, 48)

        r_rest = self.client.post("/api/stock/restaurar", headers=headers, json=dup_payload)
        self.assertEqual(r_rest.status_code, 200)
        self.assertEqual(self.tipo_repo.find_by_id(self.vip.id).stock, 10)
        self.assertEqual(self.tipo_repo.find_by_id(self.general.id).stock, 50)

    def test_stock_invalid_items_rejected(self):
        headers = self._auth_header("CLIENTE")
        bad_payloads = [
            {"items": []},
            {"items": ["not-a-dict"]},
            {"items": [{"tipo_entrada_id": True, "cantidad": 1}]},
            {"items": [{"tipo_entrada_id": self.vip.id, "cantidad": True}]},
            {"items": [{"tipo_entrada_id": "1", "cantidad": 1}]},
            {"items": [{"tipo_entrada_id": self.vip.id, "cantidad": 0}]},
            {"items": [{"tipo_entrada_id": -1, "cantidad": 1}]},
        ]
        for payload in bad_payloads:
            self.assertEqual(self.client.post("/api/stock/cotizar", json=payload).status_code, 400, f"cotizar {payload}")
            self.assertEqual(
                self.client.post("/api/stock/descontar", headers=headers, json=payload).status_code,
                400,
                f"descontar {payload}",
            )

    def test_stock_descontar_rejects_inactive_event(self):
        self.evento_repo.deactivate(self.evento.id)
        headers = self._auth_header("CLIENTE")
        r = self.client.post(
            "/api/stock/descontar",
            headers=headers,
            json={"items": [{"tipo_entrada_id": self.vip.id, "cantidad": 1}]},
        )
        self.assertEqual(r.status_code, 409)

    # --- Optimistic Concurrency Control (row_version) ---
    def test_occ_categoria_evento_tipo_entrada_and_stale_409(self):
        headers = self._auth_header("ADMIN")

        # Categoria
        r_c1 = self.client.put("/api/categorias/1", headers=headers, json={"nombre": "Música Vivo", "row_version": 1})
        self.assertEqual(r_c1.status_code, 200)
        self.assertEqual(r_c1.get_json()["row_version"], 2)
        r_c_stale = self.client.put("/api/categorias/1", headers=headers, json={"nombre": "Otra Cat", "row_version": 1})
        self.assertEqual(r_c_stale.status_code, 409)
        self.assertEqual(
            self.client.put("/api/categorias/1", headers=headers, json={"nombre": "Otra Cat", "row_version": True}).status_code,
            400,
        )

        # Evento
        r_e1 = self.client.put(
            f"/api/eventos/{self.evento.id}",
            headers=headers,
            json={"nombre": "Rock Fest 2026", "row_version": 1},
        )
        self.assertEqual(r_e1.status_code, 200)
        self.assertEqual(r_e1.get_json()["row_version"], 2)
        r_e_stale = self.client.put(
            f"/api/eventos/{self.evento.id}",
            headers=headers,
            json={"nombre": "Rock Stale", "row_version": 1},
        )
        self.assertEqual(r_e_stale.status_code, 409)
        self.assertEqual(
            self.client.put(
                f"/api/eventos/{self.evento.id}", headers=headers, json={"nombre": "Rock", "row_version": 0}
            ).status_code,
            400,
        )

        # TipoEntrada
        r_t1 = self.client.put(
            f"/api/tipos-entrada/{self.vip.id}",
            headers=headers,
            json={"precio": 120.50, "row_version": 1},
        )
        self.assertEqual(r_t1.status_code, 200)
        self.assertEqual(r_t1.get_json()["row_version"], 2)
        r_t_stale = self.client.put(
            f"/api/tipos-entrada/{self.vip.id}",
            headers=headers,
            json={"precio": 130.00, "row_version": 1},
        )
        self.assertEqual(r_t_stale.status_code, 409)

        # Stock operations also increment row_version
        cli_h = self._auth_header("CLIENTE")
        self.assertEqual(
            self.client.post(
                "/api/stock/descontar",
                headers=cli_h,
                json={"items": [{"tipo_entrada_id": self.vip.id, "cantidad": 1}]},
            ).status_code,
            200,
        )
        self.assertEqual(self.tipo_repo.find_by_id(self.vip.id).row_version, 3)

    # --- Strict No-Emoji Validation ---
    def test_emoji_rejected_400_on_all_eventos_fields(self):
        headers = self._auth_header("ADMIN")

        self.assertEqual(
            self.client.post("/api/categorias", headers=headers, json={"nombre": "Música 🎵"}).status_code, 400
        )
        self.assertEqual(
            self.client.post(
                "/api/categorias", headers=headers, json={"nombre": "Teatro", "descripcion": "Obras 🎭"}
            ).status_code,
            400,
        )
        self.assertEqual(self.client.get("/api/eventos?q=Rock🎸").status_code, 400)

        base_ev = {
            "categoria_id": 1,
            "nombre": "Festival Quito",
            "descripcion": "Descripcion valida del evento",
            "lugar": "Estadio Olimpico",
            "fecha": "2026-12-20T19:00:00Z",
            "imagen_url": "https://cdn.example.com/rock.jpg",
        }
        for field, bad_val in (
            ("nombre", "Festival 🔥"),
            ("descripcion", "Evento increible 🎉"),
            ("lugar", "Quito 🇪🇨"),
            ("fecha", "2026-12-20T19:00:00Z ⏰"),
            ("imagen_url", "https://cdn.example.com/rock🎸.jpg"),
        ):
            payload = dict(base_ev, **{field: bad_val})
            r = self.client.post("/api/eventos", headers=headers, json=payload)
            self.assertEqual(r.status_code, 400, f"Expected 400 for emoji in {field}")
            self.assertIn("No se permiten emojis", r.get_json()["message"])

        self.assertEqual(
            self.client.post(
                "/api/tipos-entrada",
                headers=headers,
                json={"evento_id": self.evento.id, "tipo": "Palco ⭐", "precio": 50, "stock": 10},
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                "/api/tipos-entrada",
                headers=headers,
                json={"evento_id": self.evento.id, "tipo": "Palco", "precio": "50💵", "stock": 10},
            ).status_code,
            400,
        )
        self.assertEqual(
            self.client.post(
                "/api/tipos-entrada",
                headers=headers,
                json={"evento_id": self.evento.id, "tipo": "Palco", "precio": 50, "stock": "10🎟️"},
            ).status_code,
            400,
        )

    # --- Strict URL / Fecha / Descripcion / Precio / Stock Validation ---
    def test_strict_url_fecha_precio_stock_validation(self):
        headers = self._auth_header("ADMIN")
        base_ev = {
            "categoria_id": 1,
            "nombre": "Concierto Sinfónico",
            "descripcion": "Presentación especial de la orquesta sinfónica",
            "lugar": "Teatro Nacional Sucre",
            "fecha": "2026-12-20T19:00:00-05:00",
            "imagen_url": "https://cdn.example.com/sinfonico.png",
        }
        r_ok = self.client.post("/api/eventos", headers=headers, json=base_ev)
        self.assertEqual(r_ok.status_code, 201)
        self.assertEqual(r_ok.get_json()["row_version"], 1)

        # Invalid URLs
        for bad_url in ("ftp://cdn.example.com/a.jpg", "not-a-url", "https://", "javascript:alert(1)", "https://a.com/x y.jpg"):
            r = self.client.post("/api/eventos", headers=headers, json=dict(base_ev, imagen_url=bad_url))
            self.assertEqual(r.status_code, 400, f"Expected 400 for imagen_url={bad_url!r}")

        # Invalid fechas
        for bad_fecha in ("not-a-date", "2026-13-45T99:00:00Z", "20261220", 123456):
            r = self.client.post("/api/eventos", headers=headers, json=dict(base_ev, fecha=bad_fecha))
            self.assertEqual(r.status_code, 400, f"Expected 400 for fecha={bad_fecha!r}")

        # Invalid descripcion (<5 chars or >1000 chars)
        for bad_desc in ("Hola", "x" * 1001):
            r = self.client.post("/api/eventos", headers=headers, json=dict(base_ev, descripcion=bad_desc))
            self.assertEqual(r.status_code, 400, f"Expected 400 for descripcion len={len(bad_desc)}")

        # Invalid precios
        for bad_precio in (-1, 1000000, 25.123, "10.999", True, "abc", "NaN", "Infinity"):
            r = self.client.post(
                "/api/tipos-entrada",
                headers=headers,
                json={"evento_id": self.evento.id, "tipo": "Tribuna", "precio": bad_precio, "stock": 10},
            )
            self.assertEqual(r.status_code, 400, f"Expected 400 for precio={bad_precio!r}")

        # Invalid stocks
        for bad_stock in (-1, 1000001, 5.5, True, "10"):
            r = self.client.post(
                "/api/tipos-entrada",
                headers=headers,
                json={"evento_id": self.evento.id, "tipo": "Tribuna", "precio": 25.50, "stock": bad_stock},
            )
            self.assertEqual(r.status_code, 400, f"Expected 400 for stock={bad_stock!r}")

        # Valid boundary values
        r_te_ok = self.client.post(
            "/api/tipos-entrada",
            headers=headers,
            json={"evento_id": self.evento.id, "tipo": "Tribuna", "precio": 999999.99, "stock": 1000000},
        )
        self.assertEqual(r_te_ok.status_code, 201)
        self.assertEqual(r_te_ok.get_json()["row_version"], 1)


if __name__ == "__main__":
    unittest.main()
