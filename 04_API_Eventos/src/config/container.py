"""Contenedor de Inyección de Dependencias (DIP)."""
from src.application.use_cases.categoria_use_cases import (
    ActualizarCategoriaUseCase, CrearCategoriaUseCase, EliminarCategoriaUseCase, ListarCategoriasUseCase,
)
from src.application.use_cases.evento_use_cases import (
    ActualizarEventoUseCase, CrearEventoUseCase, EliminarEventoUseCase, ListarEntradasEventoUseCase,
    ListarEventosUseCase, ObtenerEventoUseCase,
)
from src.application.use_cases.stock_use_cases import CotizarStockUseCase, DescontarStockUseCase, RestaurarStockUseCase
from src.application.use_cases.tipo_entrada_use_cases import (
    ActualizarTipoEntradaUseCase, CrearTipoEntradaUseCase, EliminarTipoEntradaUseCase, ListarTiposEntradaUseCase,
)
from src.config.settings import Settings
from src.domain.repositories import (
    CategoriaRepository, EventoRepository, StockRepository, TipoEntradaRepository,
)
from src.infrastructure.db.postgres_repository import (
    PostgresCategoriaRepository, PostgresEventoRepository, PostgresStockRepository, PostgresTipoEntradaRepository,
)


class Container:
    def __init__(
        self,
        settings: Settings,
        categoria_repo: CategoriaRepository,
        evento_repo: EventoRepository,
        tipo_entrada_repo: TipoEntradaRepository,
        stock_repo: StockRepository,
    ):
        self.settings = settings
        self.categoria_repo = categoria_repo
        self.evento_repo = evento_repo
        self.tipo_entrada_repo = tipo_entrada_repo
        self.stock_repo = stock_repo

        self.listar_categorias = ListarCategoriasUseCase(self.categoria_repo)
        self.crear_categoria = CrearCategoriaUseCase(self.categoria_repo)
        self.actualizar_categoria = ActualizarCategoriaUseCase(self.categoria_repo)
        self.eliminar_categoria = EliminarCategoriaUseCase(self.categoria_repo)

        self.listar_eventos = ListarEventosUseCase(self.evento_repo)
        self.obtener_evento = ObtenerEventoUseCase(self.evento_repo)
        self.crear_evento = CrearEventoUseCase(self.evento_repo, self.categoria_repo)
        self.actualizar_evento = ActualizarEventoUseCase(self.evento_repo, self.categoria_repo)
        self.eliminar_evento = EliminarEventoUseCase(self.evento_repo, self.tipo_entrada_repo)
        self.listar_entradas_evento = ListarEntradasEventoUseCase(self.evento_repo, self.tipo_entrada_repo)

        self.listar_tipos_entrada = ListarTiposEntradaUseCase(self.tipo_entrada_repo)
        self.crear_tipo_entrada = CrearTipoEntradaUseCase(self.tipo_entrada_repo, self.evento_repo)
        self.actualizar_tipo_entrada = ActualizarTipoEntradaUseCase(self.tipo_entrada_repo, self.evento_repo)
        self.eliminar_tipo_entrada = EliminarTipoEntradaUseCase(self.tipo_entrada_repo)

        self.cotizar_stock = CotizarStockUseCase(self.stock_repo)
        self.descontar_stock = DescontarStockUseCase(self.stock_repo)
        self.restaurar_stock = RestaurarStockUseCase(self.stock_repo)


def build_container(settings: Settings) -> Container:
    return Container(
        settings=settings,
        categoria_repo=PostgresCategoriaRepository(settings.database_url),
        evento_repo=PostgresEventoRepository(settings.database_url),
        tipo_entrada_repo=PostgresTipoEntradaRepository(settings.database_url),
        stock_repo=PostgresStockRepository(settings.database_url),
    )
