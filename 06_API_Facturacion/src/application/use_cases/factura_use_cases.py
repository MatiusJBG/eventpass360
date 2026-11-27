"""Casos de uso de facturación."""
import base64
from datetime import datetime, timezone
from decimal import Decimal, InvalidOperation
import math
import re

from src.domain.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from src.domain.repositories import FacturaRepository, PdfGenerator, XmlGenerator

_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U00002300-\U000023FF"
    "\U00002B00-\U00002BFF\uFE00-\uFE0F\u200D\u20E3\U0001F1E6-\U0001F1FF]"
)
_DIGITS_RE = re.compile(r"^[0-9]+$")
_DECIMAL_RE = re.compile(r"^[+-]?\d+(?:\.\d+)?$")


def _check_no_emojis(value: str, field_name: str) -> None:
    if _EMOJI_RE.search(value):
        raise ValidationError(f"No se permiten emojis en el campo '{field_name}'")


def _parse_positive_int(value, field_name: str) -> int:
    if isinstance(value, (bool, float)) or value is None:
        raise ValidationError(f"{field_name} debe ser un entero positivo")
    if isinstance(value, str):
        _check_no_emojis(value, field_name)
        s = value.strip()
        if not _DIGITS_RE.fullmatch(s):
            raise ValidationError(f"{field_name} debe ser un entero positivo")
        parsed = int(s)
    elif isinstance(value, int):
        parsed = value
    else:
        raise ValidationError(f"{field_name} debe ser un entero positivo")
    if parsed < 1:
        raise ValidationError(f"{field_name} debe ser un entero positivo")
    return parsed


def _parse_non_negative_decimal(value, field_name: str) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise ValidationError(f"{field_name} debe ser un monto válido >= 0")
    if isinstance(value, str):
        _check_no_emojis(value, field_name)
        s = value.strip()
        if not _DECIMAL_RE.fullmatch(s):
            raise ValidationError(f"{field_name} debe ser un monto válido >= 0")
        try:
            d = Decimal(s)
        except InvalidOperation:
            raise ValidationError(f"{field_name} debe ser un monto válido >= 0")
    elif isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise ValidationError(f"{field_name} debe ser un monto válido >= 0")
        d = Decimal(str(value))
    elif isinstance(value, (int, Decimal)):
        d = Decimal(str(value))
    else:
        raise ValidationError(f"{field_name} debe ser un monto válido >= 0")
    if not d.is_finite() or d < 0:
        raise ValidationError(f"{field_name} debe ser un monto válido >= 0")
    return d


def _validate_factura_inputs(cliente: dict, items: list, totales: dict) -> None:
    if not isinstance(cliente, dict):
        raise ValidationError("cliente debe ser un objeto")
    for field in ("nombre", "correo"):
        val = cliente.get(field)
        if val is not None:
            if not isinstance(val, str):
                raise ValidationError(f"cliente.{field} debe ser una cadena")
            _check_no_emojis(val, f"cliente.{field}")
    if "id" in cliente and cliente["id"] is not None:
        _parse_positive_int(cliente["id"], "cliente.id")

    if not isinstance(items, list) or not items:
        raise ValidationError("items no puede estar vacío")
    for idx, item in enumerate(items):
        if not isinstance(item, dict):
            raise ValidationError("Cada item debe ser un objeto")
        desc = item.get("descripcion")
        if desc is not None:
            if not isinstance(desc, str):
                raise ValidationError(f"items[{idx}].descripcion debe ser una cadena")
            _check_no_emojis(desc, f"items[{idx}].descripcion")
        _parse_positive_int(item.get("cantidad"), f"items[{idx}].cantidad")
        if "precio_unitario" in item:
            _parse_non_negative_decimal(item["precio_unitario"], f"items[{idx}].precio_unitario")
        if "subtotal" in item:
            _parse_non_negative_decimal(item["subtotal"], f"items[{idx}].subtotal")

    if not isinstance(totales, dict):
        raise ValidationError("totales debe ser un objeto")
    for key in ("subtotal", "descuento", "base_imponible", "iva", "total"):
        if key in totales:
            _parse_non_negative_decimal(totales[key], f"totales.{key}")


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
        _validate_factura_inputs(cliente, items, totales)
        # Idempotencia: si ya existe una factura para esta compra, se devuelve sin regenerar número.
        existing = self.repo.find_by_compra_id(cid)
        if existing is not None:
            return existing
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

    def execute(self, factura_id: int, usuario: dict | None = None, expected_version: int | None = None):
        if expected_version is not None:
            expected_version = _parse_positive_int(expected_version, "row_version")
        factura = self.repo.find_by_id(factura_id)
        if factura is None:
            raise NotFoundError("Factura no existe")
        _check_ownership(factura, usuario, "Sin permiso para anular esta factura")
        if factura.estado == "ANULADA":
            raise ConflictError("La factura ya se encuentra anulada")
        if expected_version is not None and factura.row_version != expected_version:
            raise ConflictError(
                "Conflicto de concurrencia: la factura fue modificada por otro usuario. Recarga e intenta nuevamente."
            )
        updated = self.repo.anular(factura_id, expected_version=expected_version)
        if updated is None:
            raise NotFoundError("Factura no existe")
        return updated
