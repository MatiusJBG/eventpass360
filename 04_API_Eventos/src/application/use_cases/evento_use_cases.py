"""Casos de uso de eventos y sus entradas."""
from datetime import datetime

from src.domain.exceptions import NotFoundError, ValidationError
from src.domain.repositories import CategoriaRepository, EventoRepository, TipoEntradaRepository


def _parse_fecha(fecha) -> datetime:
    if isinstance(fecha, datetime):
        return fecha
    if isinstance(fecha, str) and fecha.strip():
        try:
            return datetime.fromisoformat(fecha.replace("Z", "+00:00"))
        except ValueError:
            raise ValidationError("Fecha inválida (use formato ISO 8601)")
    raise ValidationError("Fecha obligatoria")


class ListarEventosUseCase:
    def __init__(self, repo: EventoRepository):
        self.repo = repo

    def execute(self, q=None, categoria_id=None, incluir_inactivos=False):
        return self.repo.list(q=q, categoria_id=categoria_id, incluir_inactivos=incluir_inactivos)


class ObtenerEventoUseCase:
    def __init__(self, repo: EventoRepository):
        self.repo = repo

    def execute(self, evento_id: int):
        evento = self.repo.find_by_id(evento_id)
        if evento is None:
            raise NotFoundError("Evento no existe")
        return evento


class CrearEventoUseCase:
    def __init__(self, repo: EventoRepository, categoria_repo: CategoriaRepository):
        self.repo = repo
        self.categoria_repo = categoria_repo

    def execute(self, categoria_id, nombre, descripcion, lugar, fecha, imagen_url):
        if not nombre or not lugar or not imagen_url:
            raise ValidationError("nombre, lugar e imagen_url son obligatorios")
        if self.categoria_repo.find_by_id(categoria_id) is None:
            raise NotFoundError("Categoría no existe")
        return self.repo.create(categoria_id, nombre, descripcion or "", lugar, _parse_fecha(fecha), imagen_url)


class ActualizarEventoUseCase:
    def __init__(self, repo: EventoRepository, categoria_repo: CategoriaRepository):
        self.repo = repo
        self.categoria_repo = categoria_repo

    def execute(self, evento_id, categoria_id=None, nombre=None, descripcion=None, lugar=None, fecha=None, imagen_url=None, estado=None):
        if self.repo.find_by_id(evento_id) is None:
            raise NotFoundError("Evento no existe")
        fields = {}
        if categoria_id is not None:
            if self.categoria_repo.find_by_id(categoria_id) is None:
                raise NotFoundError("Categoría no existe")
            fields["categoria_id"] = categoria_id
        if nombre:
            fields["nombre"] = nombre
        if descripcion is not None:
            fields["descripcion"] = descripcion
        if lugar:
            fields["lugar"] = lugar
        if imagen_url:
            fields["imagen_url"] = imagen_url
        if fecha:
            fields["fecha"] = _parse_fecha(fecha)
        if estado is not None:
            fields["estado"] = estado
        if not fields:
            raise ValidationError("Nada que actualizar")
        return self.repo.update(evento_id, **fields)


class EliminarEventoUseCase:
    def __init__(self, repo: EventoRepository, tipo_repo: TipoEntradaRepository):
        self.repo = repo
        self.tipo_repo = tipo_repo

    def execute(self, evento_id: int):
        if self.repo.find_by_id(evento_id) is None:
            raise NotFoundError("Evento no existe")
        entradas = self.tipo_repo.list(evento_id=evento_id)
        tiene_compras = any(self.tipo_repo.count_detalles(t.id) > 0 for t in entradas)
        if entradas and tiene_compras:
            self.repo.deactivate(evento_id)
        else:
            self.repo.delete(evento_id)


class ListarEntradasEventoUseCase:
    def __init__(self, repo: EventoRepository, tipo_repo: TipoEntradaRepository):
        self.repo = repo
        self.tipo_repo = tipo_repo

    def execute(self, evento_id: int):
        if self.repo.find_by_id(evento_id) is None:
            raise NotFoundError("Evento no existe")
        return self.tipo_repo.list(evento_id=evento_id)
