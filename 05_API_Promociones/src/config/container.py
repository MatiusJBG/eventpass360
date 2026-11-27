"""Contenedor de Inyección de Dependencias."""
from src.application.use_cases.calculo_use_cases import CalcularPromocionUseCase
from src.application.use_cases.promocion_use_cases import (
    ActualizarPromocionUseCase, CrearPromocionUseCase, EliminarPromocionUseCase, ListarPromocionesUseCase,
)
from src.config.settings import Settings
from src.infrastructure.db.postgres_repository import PostgresPromocionRepository


class Container:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.repo = PostgresPromocionRepository(settings.database_url)
        self.listar_promociones = ListarPromocionesUseCase(self.repo)
        self.crear_promocion = CrearPromocionUseCase(self.repo)
        self.actualizar_promocion = ActualizarPromocionUseCase(self.repo)
        self.eliminar_promocion = EliminarPromocionUseCase(self.repo)
        self.calcular_promocion = CalcularPromocionUseCase(self.repo)


def build_container(settings: Settings) -> Container:
    return Container(settings)
