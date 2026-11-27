"""Casos de uso de tipos de entrada."""
from decimal import Decimal, InvalidOperation

from src.domain.exceptions import ConflictError, NotFoundError, ValidationError
from src.domain.repositories import EventoRepository, TipoEntradaRepository


def _parse_decimal(value, field="precio") -> Decimal:
    if isinstance(value, bool) or value is None:
        raise ValidationError(f"{field} inválido")
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError(f"{field} inválido")
    if not d.is_finite() or d < 0:
        raise ValidationError(f"{field} no puede ser negativo")
    return d


def _validate_positive_int(value, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValidationError(f"{field} debe ser un entero positivo")
    return value


def _validate_non_negative_int(value, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value < 0:
        raise ValidationError(f"{field} debe ser un entero mayor o igual a 0")
    return value


class ListarTiposEntradaUseCase:
    def __init__(self, repo: TipoEntradaRepository):
        self.repo = repo

    def execute(self, evento_id=None):
        if evento_id is not None:
            evento_id = _validate_positive_int(evento_id, "evento_id")
        return self.repo.list(evento_id=evento_id)


class CrearTipoEntradaUseCase:
    def __init__(self, repo: TipoEntradaRepository, evento_repo: EventoRepository):
        self.repo = repo
        self.evento_repo = evento_repo

    def execute(self, evento_id, tipo, precio, stock):
        evento_id_valid = _validate_positive_int(evento_id, "evento_id")
        if not isinstance(tipo, str) or not tipo.strip():
            raise ValidationError("El tipo es obligatorio")
        tipo_norm = tipo.strip()
        if self.evento_repo.find_by_id(evento_id_valid) is None:
            raise NotFoundError("Evento no existe")
        if self.repo.find_by_evento_tipo(evento_id_valid, tipo_norm) is not None:
            raise ConflictError("Ya existe ese tipo de entrada para el evento")
        stock_valid = 0 if stock is None else _validate_non_negative_int(stock, "stock")
        return self.repo.create(evento_id_valid, tipo_norm, _parse_decimal(precio), stock_valid)


class ActualizarTipoEntradaUseCase:
    def __init__(self, repo: TipoEntradaRepository, evento_repo: EventoRepository):
        self.repo = repo
        self.evento_repo = evento_repo

    def execute(self, tipo_id, tipo=None, precio=None, stock=None, estado=None):
        actual = self.repo.find_by_id(tipo_id)
        if actual is None:
            raise NotFoundError("Tipo de entrada no existe")
        fields = {}
        if tipo is not None:
            if not isinstance(tipo, str) or not tipo.strip():
                raise ValidationError("El tipo no puede estar vacío")
            nuevo_tipo = tipo.strip()
            existing = self.repo.find_by_evento_tipo(actual.evento_id, nuevo_tipo)
            if existing is not None and existing.id != tipo_id:
                raise ConflictError("Ya existe ese tipo de entrada para el evento")
            fields["tipo"] = nuevo_tipo
        if precio is not None:
            fields["precio"] = _parse_decimal(precio)
        if stock is not None:
            fields["stock"] = _validate_non_negative_int(stock, "stock")
        if estado is not None:
            if not isinstance(estado, bool):
                raise ValidationError("estado debe ser booleano")
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
