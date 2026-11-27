"""Contenedor de Inyección de Dependencias (DIP)."""
from src.application.use_cases.compra_use_cases import (
    AnularCompraUseCase, CrearCompraUseCase, EstadisticasComprasUseCase,
    ListarComprasUseCase, ObtenerCompraUseCase,
)
from src.application.use_cases.previsualizar_use_cases import PrevisualizarCompraUseCase
from src.config.settings import Settings
from src.infrastructure.db.postgres_repository import PostgresCompraRepository
from src.infrastructure.gateways.eventos_gateway import EventosGateway
from src.infrastructure.gateways.facturacion_gateway import FacturacionGateway
from src.infrastructure.gateways.promociones_gateway import PromocionesGateway


class Container:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.repo = PostgresCompraRepository(settings.database_url)
        self.eventos_gw = EventosGateway(settings.url_eventos, settings.http_timeout)
        self.promociones_gw = PromocionesGateway(settings.url_promociones, settings.http_timeout)
        self.facturacion_gw = FacturacionGateway(settings.url_facturacion, settings.http_timeout)

        self.previsualizar = PrevisualizarCompraUseCase(self.eventos_gw, self.promociones_gw)
        self.crear_compra = CrearCompraUseCase(self.repo, self.eventos_gw, self.promociones_gw, self.facturacion_gw)
        self.listar_compras = ListarComprasUseCase(self.repo)
        self.obtener_compra = ObtenerCompraUseCase(self.repo)
        self.estadisticas = EstadisticasComprasUseCase(self.repo)
        self.anular_compra = AnularCompraUseCase(self.repo, self.eventos_gw, self.facturacion_gw)


def build_container(settings: Settings) -> Container:
    return Container(settings)
