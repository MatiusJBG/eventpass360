"""Contenedor de Inyección de Dependencias (DIP)."""
from src.application.use_cases.entrada_use_cases import (
    AnularEntradasUseCase,
    GenerarEntradasUseCase,
    ListarEntradasUseCase,
    ValidarEntradaUseCase,
)
from src.config.settings import Settings
from src.infrastructure.db.postgres_repository import PostgresEntradaRepository


class Container:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.repo = PostgresEntradaRepository(settings.database_url)
        self.generar_entradas = GenerarEntradasUseCase(self.repo)
        self.validar_entrada = ValidarEntradaUseCase(self.repo)
        self.listar_entradas = ListarEntradasUseCase(self.repo)
        self.anular_entradas = AnularEntradasUseCase(self.repo)


def build_container(settings: Settings) -> Container:
    return Container(settings)
