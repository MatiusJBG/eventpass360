"""Casos de uso de CRUD de promociones (ADMIN)."""
from decimal import Decimal, InvalidOperation
from typing import Optional

from src.domain.exceptions import ConflictError, NotFoundError, ValidationError
from src.domain.repositories import PromocionRepository


def _parse_porcentaje(value) -> Decimal:
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError("porcentaje inválido")
    if d < 0 or d > 100:
        raise ValidationError("porcentaje debe estar entre 0 y 100")
    return d


def _parse_range(cantidad_min, cantidad_max):
    try:
        cmin = int(cantidad_min)
    except (TypeError, ValueError):
        raise ValidationError("cantidad_min debe ser entero")
    if cmin < 1:
        raise ValidationError("cantidad_min debe ser >= 1")
    cmax = None
    if cantidad_max not in (None, ""):
        try:
            cmax = int(cantidad_max)
        except (TypeError, ValueError):
            raise ValidationError("cantidad_max debe ser entero o nulo")
        if cmax < cmin:
            raise ValidationError("cantidad_max debe ser >= cantidad_min")
    return cmin, cmax


class ListarPromocionesUseCase:
    def __init__(self, repo: PromocionRepository):
        self.repo = repo

    def execute(self, solo_activas=False):
        return self.repo.list_all(solo_activas=solo_activas)


class CrearPromocionUseCase:
    def __init__(self, repo: PromocionRepository):
        self.repo = repo

    def execute(self, cantidad_min, cantidad_max, porcentaje):
        cmin, cmax = _parse_range(cantidad_min, cantidad_max)
        pct = _parse_porcentaje(porcentaje)
        if self.repo.find_overlaps(cmin, cmax):
            raise ConflictError("El rango se superpone con una promoción activa")
        return self.repo.create(cmin, cmax, pct)


class ActualizarPromocionUseCase:
    def __init__(self, repo: PromocionRepository):
        self.repo = repo

    def execute(self, promocion_id, cantidad_min=None, cantidad_max=None, porcentaje=None, estado=None):
        actual = self.repo.find_by_id(promocion_id)
        if actual is None:
            raise NotFoundError("Promoción no existe")
        fields = {}
        if cantidad_min is not None or cantidad_max is not None:
            cmin = int(cantidad_min) if cantidad_min is not None else actual.cantidad_min
            cmax = actual.cantidad_max
            if cantidad_max is not None:
                cmax = None if cantidad_max == "" else int(cantidad_max)
            cmin, cmax = _parse_range(cmin, cmax)
            # Solo valida solapamiento si queda activa (o ya estaba activa)
            if actual.estado and estado is not False:
                if self.repo.find_overlaps(cmin, cmax, exclude_id=promocion_id):
                    raise ConflictError("El rango se superpone con una promoción activa")
            fields["cantidad_min"] = cmin
            fields["cantidad_max"] = cmax
        if porcentaje is not None:
            fields["porcentaje"] = _parse_porcentaje(porcentaje)
        if estado is not None:
            fields["estado"] = estado
        if not fields:
            raise ValidationError("Nada que actualizar")
        return self.repo.update(promocion_id, **fields)


class EliminarPromocionUseCase:
    def __init__(self, repo: PromocionRepository):
        self.repo = repo

    def execute(self, promocion_id):
        if self.repo.find_by_id(promocion_id) is None:
            raise NotFoundError("Promoción no existe")
        self.repo.delete(promocion_id)
