"""Casos de uso de eventos y sus entradas."""
from typing import Optional

from src.domain.exceptions import NotFoundError, ValidationError
from src.domain.repositories import CategoriaRepository, EventoRepository, TipoEntradaRepository
from src.domain.validators import (
    validate_evento_descripcion,
    validate_evento_fecha,
    validate_evento_imagen_url,
    validate_evento_lugar,
    validate_evento_nombre,
    validate_positive_int,
    validate_search_query,
)


class ListarEventosUseCase:
    def __init__(self, repo: EventoRepository):
        self.repo = repo

    def execute(self, q=None, categoria_id=None, incluir_inactivos=False):
        q_valid = validate_search_query(q, "q")
        if categoria_id is not None:
            categoria_id = validate_positive_int(categoria_id, "categoria_id")
        return self.repo.list(q=q_valid, categoria_id=categoria_id, incluir_inactivos=incluir_inactivos)


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
        categoria_id_valid = validate_positive_int(categoria_id, "categoria_id")
        nombre_norm = validate_evento_nombre(nombre)
        descripcion_norm = validate_evento_descripcion(descripcion)
        lugar_norm = validate_evento_lugar(lugar)
        fecha_valid = validate_evento_fecha(fecha)
        imagen_norm = validate_evento_imagen_url(imagen_url)
        if self.categoria_repo.find_by_id(categoria_id_valid) is None:
            raise NotFoundError("Categoría no existe")
        return self.repo.create(
            categoria_id_valid, nombre_norm, descripcion_norm, lugar_norm, fecha_valid, imagen_norm
        )


class ActualizarEventoUseCase:
    def __init__(self, repo: EventoRepository, categoria_repo: CategoriaRepository):
        self.repo = repo
        self.categoria_repo = categoria_repo

    def execute(
        self,
        evento_id,
        categoria_id=None,
        nombre=None,
        descripcion=None,
        lugar=None,
        fecha=None,
        imagen_url=None,
        estado=None,
        row_version: Optional[int] = None,
    ):
        if self.repo.find_by_id(evento_id) is None:
            raise NotFoundError("Evento no existe")
        expected_version = validate_positive_int(row_version, "row_version") if row_version is not None else None
        fields = {}
        if categoria_id is not None:
            categoria_id_valid = validate_positive_int(categoria_id, "categoria_id")
            if self.categoria_repo.find_by_id(categoria_id_valid) is None:
                raise NotFoundError("Categoría no existe")
            fields["categoria_id"] = categoria_id_valid
        if nombre is not None:
            fields["nombre"] = validate_evento_nombre(nombre)
        if descripcion is not None:
            fields["descripcion"] = validate_evento_descripcion(descripcion)
        if lugar is not None:
            fields["lugar"] = validate_evento_lugar(lugar)
        if imagen_url is not None:
            fields["imagen_url"] = validate_evento_imagen_url(imagen_url)
        if fecha is not None:
            fields["fecha"] = validate_evento_fecha(fecha)
        if estado is not None:
            if not isinstance(estado, bool):
                raise ValidationError("estado debe ser booleano")
            fields["estado"] = estado
        if not fields:
            raise ValidationError("Nada que actualizar")
        return self.repo.update(evento_id, expected_version=expected_version, **fields)


class EliminarEventoUseCase:
    def __init__(self, repo: EventoRepository, tipo_repo: TipoEntradaRepository):
        self.repo = repo
        self.tipo_repo = tipo_repo

    def execute(self, evento_id: int) -> dict:
        if self.repo.find_by_id(evento_id) is None:
            raise NotFoundError("Evento no existe")
        entradas = self.tipo_repo.list(evento_id=evento_id)
        tiene_compras = any(self.tipo_repo.count_detalles(t.id) > 0 for t in entradas)
        if tiene_compras:
            self.repo.deactivate(evento_id)
            return {"accion": "desactivado", "message": "Evento desactivado porque tiene compras asociadas"}
        self.repo.delete(evento_id)
        return {"accion": "eliminado", "message": "Evento eliminado"}


class ListarEntradasEventoUseCase:
    def __init__(self, repo: EventoRepository, tipo_repo: TipoEntradaRepository):
        self.repo = repo
        self.tipo_repo = tipo_repo

    def execute(self, evento_id: int):
        if self.repo.find_by_id(evento_id) is None:
            raise NotFoundError("Evento no existe")
        return self.tipo_repo.list(evento_id=evento_id)
