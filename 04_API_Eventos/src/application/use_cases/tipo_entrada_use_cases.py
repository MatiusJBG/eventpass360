"""Casos de uso de tipos de entrada."""
from typing import Optional

from src.domain.exceptions import ConflictError, NotFoundError, ValidationError
from src.domain.repositories import EventoRepository, TipoEntradaRepository
from src.domain.validators import (
    validate_positive_int,
    validate_precio,
    validate_stock,
    validate_tipo_entrada_tipo,
)


class ListarTiposEntradaUseCase:
    def __init__(self, repo: TipoEntradaRepository):
        self.repo = repo

    def execute(self, evento_id=None):
        if evento_id is not None:
            evento_id = validate_positive_int(evento_id, "evento_id")
        return self.repo.list(evento_id=evento_id)


class CrearTipoEntradaUseCase:
    def __init__(self, repo: TipoEntradaRepository, evento_repo: EventoRepository):
        self.repo = repo
        self.evento_repo = evento_repo

    def execute(self, evento_id, tipo, precio, stock):
        evento_id_valid = validate_positive_int(evento_id, "evento_id")
        tipo_norm = validate_tipo_entrada_tipo(tipo)
        precio_valid = validate_precio(precio, "precio")
        stock_valid = 0 if stock is None else validate_stock(stock, "stock")
        if self.evento_repo.find_by_id(evento_id_valid) is None:
            raise NotFoundError("Evento no existe")
        if self.repo.find_by_evento_tipo(evento_id_valid, tipo_norm) is not None:
            raise ConflictError("Ya existe ese tipo de entrada para el evento")
        return self.repo.create(evento_id_valid, tipo_norm, precio_valid, stock_valid)


class ActualizarTipoEntradaUseCase:
    def __init__(self, repo: TipoEntradaRepository, evento_repo: EventoRepository):
        self.repo = repo
        self.evento_repo = evento_repo

    def execute(
        self,
        tipo_id,
        tipo=None,
        precio=None,
        stock=None,
        estado=None,
        row_version: Optional[int] = None,
    ):
        actual = self.repo.find_by_id(tipo_id)
        if actual is None:
            raise NotFoundError("Tipo de entrada no existe")
        expected_version = validate_positive_int(row_version, "row_version") if row_version is not None else None
        fields = {}
        if tipo is not None:
            nuevo_tipo = validate_tipo_entrada_tipo(tipo)
            existing = self.repo.find_by_evento_tipo(actual.evento_id, nuevo_tipo)
            if existing is not None and existing.id != tipo_id:
                raise ConflictError("Ya existe ese tipo de entrada para el evento")
            fields["tipo"] = nuevo_tipo
        if precio is not None:
            fields["precio"] = validate_precio(precio, "precio")
        if stock is not None:
            fields["stock"] = validate_stock(stock, "stock")
        if estado is not None:
            if not isinstance(estado, bool):
                raise ValidationError("estado debe ser booleano")
            fields["estado"] = estado
        if not fields:
            raise ValidationError("Nada que actualizar")
        return self.repo.update(tipo_id, expected_version=expected_version, **fields)


class EliminarTipoEntradaUseCase:
    def __init__(self, repo: TipoEntradaRepository):
        self.repo = repo

    def execute(self, tipo_id):
        if self.repo.find_by_id(tipo_id) is None:
            raise NotFoundError("Tipo de entrada no existe")
        if self.repo.count_detalles(tipo_id) > 0:
            self.repo.deactivate(tipo_id)
        else:
            self.repo.delete(tipo_id)
