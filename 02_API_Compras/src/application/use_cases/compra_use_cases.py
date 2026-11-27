"""Casos de uso de compras (orquestación SAGA)."""
import logging
import re

from src.application.use_cases.previsualizar_use_cases import normalize_items
from src.domain.exceptions import (
    ConflictError,
    ForbiddenError,
    NotFoundError,
    ServiceUnavailableError,
    ValidationError,
)
from src.domain.repositories import (
    CompraRepository,
    EventosGateway,
    FacturacionGateway,
    PromocionesGateway,
)

logger = logging.getLogger(__name__)
_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U00002300-\U000023FF"
    "\U00002B00-\U00002BFF\uFE00-\uFE0F\u200D\u20E3\U0001F1E6-\U0001F1FF]"
)
_SOLICITUD_ID_RE = re.compile(r"^[A-Za-z0-9_-]{1,100}$")


class CrearCompraUseCase:
    def __init__(
        self,
        repo: CompraRepository,
        eventos_gw: EventosGateway,
        promociones_gw: PromocionesGateway,
        facturacion_gw: FacturacionGateway,
    ):
        self.repo = repo
        self.eventos_gw = eventos_gw
        self.promociones_gw = promociones_gw
        self.facturacion_gw = facturacion_gw

    def _build_replay_response(self, existing, usuario: dict, auth_header: str) -> dict:
        if existing.usuario_id != usuario["sub"]:
            raise ForbiddenError("La solicitud pertenece a otro usuario")
        factura = None
        try:
            factura = self.facturacion_gw.buscar_por_compra(existing.id, auth_header=auth_header)
        except Exception as exc:  # noqa: BLE001
            logger.warning("No se pudo recuperar factura para compra idempotente %s: %s", existing.id, exc)
        resultado = existing.to_dict()
        resultado["factura"] = factura
        return resultado

    def execute(self, usuario: dict, solicitud_id: str, items, auth_header: str = ""):
        normalized = normalize_items(items)
        if not isinstance(solicitud_id, str) or not solicitud_id.strip():
            raise ValidationError("solicitud_id es obligatorio")
        if _EMOJI_RE.search(solicitud_id):
            raise ValidationError("No se permiten emojis en el campo 'solicitud_id'")
        solicitud_id = solicitud_id.strip()
        if not _SOLICITUD_ID_RE.fullmatch(solicitud_id):
            raise ValidationError("solicitud_id debe tener entre 1 y 100 caracteres alfanuméricos, '-' o '_'")

        # 1. Idempotencia: mismo solicitud_id -> misma compra, sin repetir efectos.
        existing = self.repo.find_by_solicitud_id(solicitud_id)
        if existing is not None:
            return self._build_replay_response(existing, usuario, auth_header), False

        # 2. Cotizar precios reales en API Eventos (jamás confiar en precios del cliente).
        cotizacion = self.eventos_gw.cotizar(normalized)
        cot_items = cotizacion.get("items", [])
        if not all(it.get("disponible") for it in cot_items):
            raise ConflictError("Stock insuficiente para uno o más items")
        subtotal = cotizacion.get("subtotal_total", 0)
        cantidad_total = sum(it["cantidad"] for it in normalized)

        # 3. Calcular descuento e IVA en API Promociones.
        calculo = self.promociones_gw.calcular(subtotal, cantidad_total)

        # 4. Descuento atómico de stock en API Eventos (409 si no alcanza).
        self.eventos_gw.descontar(normalized, auth_header=auth_header)

        # 5. Persistir compra (PENDIENTE) + detalle. Si falla, compensar stock inmediatamente.
        detalles_db = [
            {"tipo_entrada_id": it["tipo_entrada_id"], "cantidad": it["cantidad_solicitada"],
             "precio_unitario": it["precio_unitario"], "subtotal": it["subtotal"]}
            for it in cot_items
        ]
        try:
            compra = self.repo.create(
                usuario_id=usuario["sub"], solicitud_id=solicitud_id,
                subtotal=calculo["subtotal"], descuento=calculo["descuento"],
                base_imponible=calculo["base_imponible"], iva=calculo["iva"],
                total=calculo["total"], estado="PENDIENTE", detalles=detalles_db,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Fallo al persistir compra (%s); restaurando stock: %s", solicitud_id, exc)
            try:
                self.eventos_gw.restaurar(normalized, auth_header=auth_header)
            except Exception as restore_exc:  # noqa: BLE001
                logger.error("No se pudo restaurar stock tras fallo en paso 5 (%s): %s", solicitud_id, restore_exc)
            existing = self.repo.find_by_solicitud_id(solicitud_id)
            if existing is not None:
                return self._build_replay_response(existing, usuario, auth_header), False
            raise

        # 6. Emitir factura en API Facturación.
        factura_items = [
            {"descripcion": f"{it['evento_nombre']} - {it['tipo']}", "cantidad": it["cantidad_solicitada"],
             "precio_unitario": it["precio_unitario"], "subtotal": it["subtotal"]}
            for it in cot_items
        ]
        cliente = {"id": usuario["sub"], "nombre": usuario.get("nombre", ""), "correo": usuario.get("correo", "")}
        totales = {k: calculo[k] for k in ("subtotal", "descuento", "base_imponible", "iva", "total")}

        try:
            factura = self.facturacion_gw.emitir(
                compra.id, cliente, factura_items, totales, auth_header=auth_header
            )
        except Exception as exc:  # noqa: BLE001
            # 7. COMPENSACIÓN SAGA: restaurar stock y marcar FALLIDA (nunca confirmada incompleta).
            logger.warning("Facturación falló; compensando compra %s: %s", compra.id, exc)
            try:
                self.eventos_gw.restaurar(normalized, auth_header=auth_header)
            except Exception as restore_exc:  # noqa: BLE001
                logger.error("No se pudo restaurar stock de compra %s: %s", compra.id, restore_exc)
            self.repo.update_estado(compra.id, "FALLIDA")
            raise ServiceUnavailableError("No se pudo emitir la factura; compra compensada")

        # 8. Confirmar compra.
        self.repo.update_estado(compra.id, "CONFIRMADA")
        resultado = self.repo.find_by_id(compra.id).to_dict()
        resultado["factura"] = factura
        return resultado, True


class ListarComprasUseCase:
    def __init__(self, repo: CompraRepository):
        self.repo = repo

    def execute(self, usuario_id=None):
        return self.repo.list_all(usuario_id=usuario_id)


class ObtenerCompraUseCase:
    def __init__(self, repo: CompraRepository):
        self.repo = repo

    def execute(self, compra_id: int):
        compra = self.repo.find_by_id(compra_id)
        if compra is None:
            raise NotFoundError("Compra no existe")
        return compra


class EstadisticasComprasUseCase:
    def __init__(self, repo: CompraRepository):
        self.repo = repo

    def execute(self):
        return self.repo.estadisticas()


class AnularCompraUseCase:
    def __init__(
        self,
        repo: CompraRepository,
        eventos_gw: EventosGateway,
        facturacion_gw: FacturacionGateway,
    ):
        self.repo = repo
        self.eventos_gw = eventos_gw
        self.facturacion_gw = facturacion_gw

    def execute(self, compra_id: int, auth_header: str = "", expected_version: int | None = None):
        if expected_version is not None:
            if isinstance(expected_version, (bool, float)) or not isinstance(expected_version, int) or expected_version < 1:
                raise ValidationError("row_version debe ser un entero positivo")
        compra = self.repo.find_by_id(compra_id)
        if compra is None:
            raise NotFoundError("Compra no existe")
        if compra.estado == "ANULADA":
            raise ConflictError("La compra ya se encuentra anulada")
        if compra.estado != "CONFIRMADA":
            raise ConflictError("Solo se pueden anular compras confirmadas")
        if expected_version is not None and compra.row_version != expected_version:
            raise ConflictError(
                "Conflicto de concurrencia: la compra fue modificada por otro usuario. Recarga e intenta nuevamente."
            )

        # Transición atómica CONFIRMADA -> ANULADA para evitar doble anulación concurrente.
        if not self.repo.transition_estado(
            compra_id, from_estado="CONFIRMADA", to_estado="ANULADA", expected_version=expected_version
        ):
            if expected_version is not None:
                raise ConflictError(
                    "Conflicto de concurrencia: la compra fue modificada o cambió de estado. Recarga e intenta nuevamente."
                )
            raise ConflictError("La compra ya se encuentra anulada o cambió de estado")

        # Restaurar stock (compensación) y anular factura sin silenciar fallos.
        items = [{"tipo_entrada_id": d.tipo_entrada_id, "cantidad": d.cantidad} for d in compra.detalles]
        try:
            self.eventos_gw.restaurar(items, auth_header=auth_header)
        except Exception as exc:  # noqa: BLE001
            logger.error("No se pudo restaurar stock en anulación de compra %s: %s", compra_id, exc)
            self.repo.update_estado(compra_id, "CONFIRMADA")
            raise ServiceUnavailableError("No se pudo restaurar el stock; la compra sigue confirmada") from exc

        try:
            self.facturacion_gw.anular_por_compra(compra_id, auth_header=auth_header)
        except Exception as exc:  # noqa: BLE001
            logger.error("No se pudo anular factura en anulación de compra %s: %s", compra_id, exc)
            try:
                self.eventos_gw.descontar(items, auth_header=auth_header)
                self.repo.update_estado(compra_id, "CONFIRMADA")
            except Exception as comp_exc:  # noqa: BLE001
                logger.error("Error compensando anulación fallida de compra %s: %s", compra_id, comp_exc)
            raise ServiceUnavailableError("No se pudo anular la factura asociada") from exc

        return self.repo.find_by_id(compra_id)
