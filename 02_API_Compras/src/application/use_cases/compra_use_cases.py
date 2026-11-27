"""Casos de uso de compras (orquestación SAGA)."""
import logging

from src.application.use_cases.previsualizar_use_cases import normalize_items
from src.domain.exceptions import ConflictError, NotFoundError, ServiceUnavailableError
from src.domain.repositories import CompraRepository

logger = logging.getLogger(__name__)


class CrearCompraUseCase:
    def __init__(self, repo: CompraRepository, eventos_gw, promociones_gw, facturacion_gw):
        self.repo = repo
        self.eventos_gw = eventos_gw
        self.promociones_gw = promociones_gw
        self.facturacion_gw = facturacion_gw

    def execute(self, usuario: dict, solicitud_id: str, items):
        normalized = normalize_items(items)
        if not solicitud_id:
            from src.domain.exceptions import ValidationError
            raise ValidationError("solicitud_id es obligatorio")

        # 1. Idempotencia: mismo solicitud_id -> misma compra, sin repetir efectos.
        existing = self.repo.find_by_solicitud_id(solicitud_id)
        if existing is not None:
            return existing.to_dict(), False

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
        self.eventos_gw.descontar(normalized)

        # 5. Persistir compra (PENDIENTE) + detalle.
        detalles_db = [
            {"tipo_entrada_id": it["tipo_entrada_id"], "cantidad": it["cantidad_solicitada"],
             "precio_unitario": it["precio_unitario"], "subtotal": it["subtotal"]}
            for it in cot_items
        ]
        compra = self.repo.create(
            usuario_id=usuario["sub"], solicitud_id=solicitud_id,
            subtotal=calculo["subtotal"], descuento=calculo["descuento"],
            base_imponible=calculo["base_imponible"], iva=calculo["iva"],
            total=calculo["total"], estado="PENDIENTE", detalles=detalles_db,
        )

        # 6. Emitir factura en API Facturación.
        factura_items = [
            {"descripcion": f"{it['evento_nombre']} - {it['tipo']}", "cantidad": it["cantidad_solicitada"],
             "precio_unitario": it["precio_unitario"], "subtotal": it["subtotal"]}
            for it in cot_items
        ]
        cliente = {"id": usuario["sub"], "nombre": usuario.get("nombre", ""), "correo": usuario.get("correo", "")}
        totales = {k: calculo[k] for k in ("subtotal", "descuento", "base_imponible", "iva", "total")}

        try:
            factura = self.facturacion_gw.emitir(compra.id, cliente, factura_items, totales)
        except Exception as exc:  # noqa: BLE001
            # 7. COMPENSACIÓN SAGA: restaurar stock y marcar FALLIDA (nunca confirmada incompleta).
            logger.warning("Facturación falló; compensando compra %s: %s", compra.id, exc)
            try:
                self.eventos_gw.restaurar(normalized)
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
    def __init__(self, repo: CompraRepository, eventos_gw, facturacion_gw):
        self.repo = repo
        self.eventos_gw = eventos_gw
        self.facturacion_gw = facturacion_gw

    def execute(self, compra_id: int):
        compra = self.repo.find_by_id(compra_id)
        if compra is None:
            raise NotFoundError("Compra no existe")
        if compra.estado == "ANULADA":
            return compra
        # Restaurar stock (compensación) y anular factura.
        items = [{"tipo_entrada_id": d.tipo_entrada_id, "cantidad": d.cantidad} for d in compra.detalles]
        try:
            self.eventos_gw.restaurar(items)
        except Exception as exc:  # noqa: BLE001
            logger.warning("No se pudo restaurar stock en anulación: %s", exc)
        try:
            self.facturacion_gw.anular_por_compra(compra_id)
        except Exception as exc:  # noqa: BLE001
            logger.warning("No se pudo anular factura: %s", exc)
        return self.repo.anular(compra_id)
