"""Pruebas unitarias para API Entradas (:5005)."""
import unittest
from datetime import datetime, timezone

from src.application.use_cases.entrada_use_cases import (
    AnularEntradasUseCase,
    GenerarEntradasUseCase,
    ListarEntradasUseCase,
    ValidarEntradaUseCase,
)
from src.domain.entities import Entrada
from src.domain.exceptions import ConflictError, NotFoundError, ValidationError
from src.domain.repositories import EntradaRepository


class InMemoryEntradaRepo(EntradaRepository):
    def __init__(self):
        self._entradas = {}
        self._seq = 1
        self._compra_detalle = {}

    def set_compra(self, compra_id, estado, detalles):
        self._compra_detalle[compra_id] = (estado, detalles)

    def find_by_id(self, entrada_id):
        return self._entradas.get(entrada_id)

    def find_by_codigo(self, codigo):
        for e in self._entradas.values():
            if e.codigo == codigo:
                return e
        return None

    def find_by_compra_id(self, compra_id):
        return [e for e in self._entradas.values() if e.compra_id == compra_id]

    def list_all(self, compra_id=None, usuario_id=None):
        res = list(self._entradas.values())
        if compra_id is not None:
            res = [e for e in res if e.compra_id == compra_id]
        return res

    def generar(self, compra_id):
        if compra_id not in self._compra_detalle:
            raise NotFoundError("Compra no existe")
        estado, detalles = self._compra_detalle[compra_id]
        if estado not in ("PENDIENTE", "CONFIRMADA"):
            raise ConflictError("La compra no está en un estado válido")
        existing = self.find_by_compra_id(compra_id)
        if existing:
            return existing
        for d in detalles:
            for _ in range(d["cantidad"]):
                eid = self._seq
                self._seq += 1
                self._entradas[eid] = Entrada(
                    id=eid, compra_id=compra_id, detalle_compra_id=d["id"],
                    evento_id=d["evento_id"], codigo="EVT-%06d" % eid, estado="DISPONIBLE",
                    fecha_validacion=None, evento_nombre="Rock Fest", tipo="General",
                )
        return self.find_by_compra_id(compra_id)

    def validar(self, codigo, evento_id):
        entrada = self.find_by_codigo(codigo)
        if entrada is None or entrada.evento_id != evento_id or entrada.estado != "DISPONIBLE":
            return None
        self._entradas[entrada.id] = Entrada(
            id=entrada.id, compra_id=entrada.compra_id, detalle_compra_id=entrada.detalle_compra_id,
            evento_id=entrada.evento_id, codigo=entrada.codigo, estado="UTILIZADA",
            fecha_validacion=datetime.now(timezone.utc), evento_nombre=entrada.evento_nombre,
            tipo=entrada.tipo, row_version=entrada.row_version + 1,
        )
        return self._entradas[entrada.id]

    def anular_por_compra(self, compra_id):
        for eid, e in list(self._entradas.items()):
            if e.compra_id == compra_id and e.estado == "DISPONIBLE":
                self._entradas[eid] = Entrada(
                    id=e.id, compra_id=e.compra_id, detalle_compra_id=e.detalle_compra_id,
                    evento_id=e.evento_id, codigo=e.codigo, estado="ANULADA",
                    fecha_validacion=e.fecha_validacion, evento_nombre=e.evento_nombre,
                    tipo=e.tipo, row_version=e.row_version + 1,
                )


class EntradasTestCase(unittest.TestCase):
    def setUp(self):
        self.repo = InMemoryEntradaRepo()
        self.repo.set_compra(1, "CONFIRMADA", [{"id": 1, "cantidad": 3, "evento_id": 1}])
        self.generar_uc = GenerarEntradasUseCase(self.repo)
        self.validar_uc = ValidarEntradaUseCase(self.repo)
        self.listar_uc = ListarEntradasUseCase(self.repo)
        self.anular_uc = AnularEntradasUseCase(self.repo)

    def test_generar_crea_tres_codigos_unicos(self):
        entradas = self.generar_uc.execute(1)
        self.assertEqual(len(entradas), 3)
        codigos = [e.codigo for e in entradas]
        self.assertEqual(len(set(codigos)), 3)
        for e in entradas:
            self.assertEqual(e.estado, "DISPONIBLE")
            self.assertEqual(e.evento_id, 1)

    def test_generar_es_idempotente(self):
        e1 = self.generar_uc.execute(1)
        e2 = self.generar_uc.execute(1)
        self.assertEqual(len(e1), len(e2))
        self.assertEqual([x.codigo for x in e1], [x.codigo for x in e2])

    def test_validar_disponible_marca_utilizada(self):
        entradas = self.generar_uc.execute(1)
        actualizada = self.validar_uc.execute(entradas[0].codigo, 1)
        self.assertEqual(actualizada.estado, "UTILIZADA")
        self.assertIsNotNone(actualizada.fecha_validacion)

    def test_validar_codigo_inexistente_404(self):
        with self.assertRaises(NotFoundError):
            self.validar_uc.execute("EVT-999999", 1)

    def test_validar_evento_incorrecto_409(self):
        entradas = self.generar_uc.execute(1)
        with self.assertRaises(ConflictError):
            self.validar_uc.execute(entradas[0].codigo, 999)

    def test_validar_reutilizacion_409(self):
        entradas = self.generar_uc.execute(1)
        self.validar_uc.execute(entradas[0].codigo, 1)
        with self.assertRaises(ConflictError):
            self.validar_uc.execute(entradas[0].codigo, 1)

    def test_validar_codigo_vacio_400(self):
        with self.assertRaises(ValidationError):
            self.validar_uc.execute("", 1)

    def test_anular_por_compra(self):
        self.generar_uc.execute(1)
        self.anular_uc.execute(1)
        for e in self.repo.find_by_compra_id(1):
            self.assertEqual(e.estado, "ANULADA")

    def test_listar_por_compra(self):
        self.generar_uc.execute(1)
        entradas = self.listar_uc.execute(compra_id=1)
        self.assertEqual(len(entradas), 3)


if __name__ == "__main__":
    unittest.main()
