"""Casos de uso de facturación."""
import base64
from datetime import datetime, timezone

from src.domain.exceptions import NotFoundError, ValidationError
from src.domain.repositories import FacturaRepository


class EmitirFacturaUseCase:
    def __init__(self, repo: FacturaRepository, xml_service, pdf_service):
        self.repo = repo
        self.xml_service = xml_service
        self.pdf_service = pdf_service

    def execute(self, compra_id, cliente, items, totales):
        if compra_id is None:
            raise ValidationError("compra_id obligatorio")
        # Idempotencia: si ya existe una factura para esta compra, se devuelve sin regenerar número.
        existing = self.repo.find_by_compra_id(compra_id)
        if existing is not None:
            return existing
        if not isinstance(items, list) or not items:
            raise ValidationError("items no puede estar vacío")
        numero = self.repo.next_numero()
        fecha = datetime.now(timezone.utc)
        xml_str = self.xml_service.generar(numero, fecha, cliente, items, totales)
        pdf_bytes = self.pdf_service.generar(numero, fecha, cliente, items, totales)
        pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")
        return self.repo.create(compra_id, numero, fecha, xml_str, pdf_b64)


class ListarFacturasUseCase:
    def __init__(self, repo: FacturaRepository):
        self.repo = repo

    def execute(self, compra_id=None):
        return self.repo.list_all(compra_id=compra_id)


class ObtenerFacturaUseCase:
    def __init__(self, repo: FacturaRepository):
        self.repo = repo

    def execute(self, factura_id: int):
        factura = self.repo.find_by_id(factura_id)
        if factura is None:
            raise NotFoundError("Factura no existe")
        return factura


class AnularFacturaUseCase:
    def __init__(self, repo: FacturaRepository):
        self.repo = repo

    def execute(self, factura_id: int):
        if self.repo.find_by_id(factura_id) is None:
            raise NotFoundError("Factura no existe")
        return self.repo.anular(factura_id)
