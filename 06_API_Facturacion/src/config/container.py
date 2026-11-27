"""Contenedor de Inyección de Dependencias."""
from src.application.use_cases.factura_use_cases import (
    AnularFacturaUseCase, EmitirFacturaUseCase, ListarFacturasUseCase, ObtenerFacturaUseCase,
)
from src.config.settings import Settings
from src.infrastructure.db.postgres_repository import PostgresFacturaRepository
from src.infrastructure.gateways.pdf_service import GenerarFacturaPdfService
from src.infrastructure.gateways.xml_service import GenerarFacturaXmlService


class Container:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.repo = PostgresFacturaRepository(settings.database_url)
        self.xml_service = GenerarFacturaXmlService()
        self.pdf_service = GenerarFacturaPdfService()
        self.emitir_factura = EmitirFacturaUseCase(self.repo, self.xml_service, self.pdf_service)
        self.listar_facturas = ListarFacturasUseCase(self.repo)
        self.obtener_factura = ObtenerFacturaUseCase(self.repo)
        self.anular_factura = AnularFacturaUseCase(self.repo)


def build_container(settings: Settings) -> Container:
    return Container(settings)
