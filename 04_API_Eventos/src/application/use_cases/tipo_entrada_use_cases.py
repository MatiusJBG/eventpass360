"""Casos de uso de tipos de entrada."""
from decimal import Decimal, InvalidOperation

from src.domain.exceptions import ConflictError, NotFoundError, ValidationError
from src.domain.repositories import EventoRepository, TipoEntradaRepository


def _parse_decimal(value, field="precio") -> Decimal:
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError(f"{field} inválido")
    if d < 0:
        raise ValidationError(f"{field} no puede ser negativo")
    return d


class ListarTiposEntradaUseCase:
    def __init__(self, repo: TipoEntradaRepository):
        self.repo = repo

    def execute(self, evento_id=None):
        return self.repo.list(evento_id=evento_id)


class CrearTipoEntradaUseCase:
    def __init__(self, repo: TipoEntradaRepository, evento_repo: EventoRepository):
        self.repo = repo
        self.evento_repo = evento_repo

    def execute(self, evento_id, tipo, precio, stock):
        if not tipo:
            raise ValidationError("El tipo es obligatorio")
        if self.evento_repo.find_by_id(evento_id) is None:
            raise NotFoundError("Evento no existe")
        if self.repo.find_by_evento_tipo(evento_id, tipo) is not None:
            raise ConflictError("Ya existe ese tipo de entrada para el evento")
        stock = int(stock) if stock is not None else 0
        if stock < 0:
            raise ValidationError("El stock no puede ser negativo")
        return self.repo.create(evento_id, tipo, _parse_decimal(precio), stock)


class ActualizarTipoEntradaUseCase:
    def __init__(self, repo: TipoEntradaRepository, evento_repo: EventoRepository):
        self.repo = repo
        self.evento_repo = evento_repo

    def execute(self, tipo_id, tipo=None, precio=None, stock=None, estado=None):
        if self.repo.find_by_id(tipo_id) is None:
            raise NotFoundError("Tipo de entrada no existe")
        fields = {}
        if tipo:
            fields["tipo"] = tipo
        if precio is not None:
            fields["precio"] = _parse_decimal(precio)
        if stock is not None:
            stock = int(stock)
            if stock < 0:
                raise ValidationError("El stock no puede ser negativo")
            fields["stock"] = stock
        if estado is not None:
            fields["estado"] = estado
        if not fields:
            raise ValidationError("Nada que actualizar")
        return self.repo.update(tipo_id, **fields)


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
