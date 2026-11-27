"""Casos de uso de facturación."""
import base64
from datetime import datetime, timezone

from src.domain.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from src.domain.repositories import FacturaRepository, PdfGenerator, XmlGenerator


def _parse_positive_int(value, field_name: str) -> int:
    if isinstance(value, (bool, float)) or value is None:
        raise ValidationError(f"{field_name} debe ser un entero positivo")
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field_name} debe ser un entero positivo")
    if parsed < 1:
        raise ValidationError(f"{field_name} debe ser un entero positivo")
    return parsed


def _check_ownership(factura, usuario: dict | None, message: str) -> None:
    if usuario is None:
        return
    if usuario.get("rol") == "ADMIN":
        return
    try:
        user_id = int(usuario["sub"])
    except (KeyError, TypeError, ValueError):
        raise ForbiddenError(message)
    if factura.usuario_id is None or factura.usuario_id != user_id:
        raise ForbiddenError(message)


class EmitirFacturaUseCase:
    def __init__(self, repo: FacturaRepository, xml_service: XmlGenerator, pdf_service: PdfGenerator):
        self.repo = repo
        self.xml_service = xml_service
        self.pdf_service = pdf_service

    def execute(self, compra_id, cliente, items, totales):
        cid = _parse_positive_int(compra_id, "compra_id")
        # Idempotencia: si ya existe una factura para esta compra, se devuelve sin regenerar número.
        existing = self.repo.find_by_compra_id(cid)
        if existing is not None:
            return existing
        if not isinstance(items, list) or not items:
            raise ValidationError("items no puede estar vacío")
        if not isinstance(cliente, dict):
            raise ValidationError("cliente debe ser un objeto")
        if not isinstance(totales, dict):
            raise ValidationError("totales debe ser un objeto")
        numero = self.repo.next_numero()
        fecha = datetime.now(timezone.utc)
        xml_str = self.xml_service.generar(numero, fecha, cliente, items, totales)
        pdf_bytes = self.pdf_service.generar(numero, fecha, cliente, items, totales)
        pdf_b64 = base64.b64encode(pdf_bytes).decode("utf-8")
        try:
            return self.repo.create(cid, numero, fecha, xml_str, pdf_b64)
        except ConflictError:
            existing = self.repo.find_by_compra_id(cid)
            if existing is not None:
                return existing
            raise


class ListarFacturasUseCase:
    def __init__(self, repo: FacturaRepository):
        self.repo = repo

    def execute(self, compra_id=None, usuario_id=None):
        cid = _parse_positive_int(compra_id, "compra_id") if compra_id is not None else None
        return self.repo.list_all(compra_id=cid, usuario_id=usuario_id)


class ObtenerFacturaUseCase:
    def __init__(self, repo: FacturaRepository):
        self.repo = repo

    def execute(self, factura_id: int, usuario: dict | None = None):
        factura = self.repo.find_by_id(factura_id)
        if factura is None:
            raise NotFoundError("Factura no existe")
        _check_ownership(factura, usuario, "Sin permiso para acceder a esta factura")
        return factura


class AnularFacturaUseCase:
    def __init__(self, repo: FacturaRepository):
        self.repo = repo

    def execute(self, factura_id: int, usuario: dict | None = None):
        factura = self.repo.find_by_id(factura_id)
        if factura is None:
            raise NotFoundError("Factura no existe")
        _check_ownership(factura, usuario, "Sin permiso para anular esta factura")
        if factura.estado == "ANULADA":
            raise ConflictError("La factura ya se encuentra anulada")
        return self.repo.anular(factura_id)
