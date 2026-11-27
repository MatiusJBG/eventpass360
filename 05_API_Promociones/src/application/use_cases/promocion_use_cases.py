"""Casos de uso de CRUD de promociones (ADMIN)."""
from decimal import Decimal, InvalidOperation

from src.domain.exceptions import ConflictError, NotFoundError, ValidationError
from src.domain.repositories import PromocionRepository

UNSET = object()


def _parse_int(value, field_name: str) -> int:
    if isinstance(value, (bool, float)) or value is None:
        raise ValidationError(f"{field_name} debe ser entero")
    try:
        return int(value)
    except (TypeError, ValueError):
        raise ValidationError(f"{field_name} debe ser entero")


def _parse_porcentaje(value) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise ValidationError("porcentaje inválido")
    try:
        d = Decimal(str(value))
    except (InvalidOperation, ValueError, TypeError):
        raise ValidationError("porcentaje inválido")
    if not d.is_finite() or d < 0 or d > 100:
        raise ValidationError("porcentaje debe estar entre 0 y 100")
    return d


def _parse_range(cantidad_min, cantidad_max):
    cmin = _parse_int(cantidad_min, "cantidad_min")
    if cmin < 1:
        raise ValidationError("cantidad_min debe ser >= 1")
    cmax = None
    if cantidad_max not in (None, ""):
        cmax = _parse_int(cantidad_max, "cantidad_max")
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

    def execute(
        self,
        promocion_id,
        cantidad_min=UNSET,
        cantidad_max=UNSET,
        porcentaje=UNSET,
        estado=UNSET,
    ):
        actual = self.repo.find_by_id(promocion_id)
        if actual is None:
            raise NotFoundError("Promoción no existe")

        fields = {}
        cmin = actual.cantidad_min
        cmax = actual.cantidad_max
        range_changed = False

        if cantidad_min is not UNSET:
            cmin = _parse_int(cantidad_min, "cantidad_min")
            range_changed = True
        if cantidad_max is not UNSET:
            cmax = None if cantidad_max in (None, "") else _parse_int(cantidad_max, "cantidad_max")
            range_changed = True

        if range_changed:
            cmin, cmax = _parse_range(cmin, cmax)
            fields["cantidad_min"] = cmin
            fields["cantidad_max"] = cmax

        if porcentaje is not UNSET:
            fields["porcentaje"] = _parse_porcentaje(porcentaje)

        if estado is UNSET or estado is None:
            nuevo_estado = actual.estado
        else:
            if not isinstance(estado, bool):
                raise ValidationError("estado debe ser booleano")
            nuevo_estado = estado
            fields["estado"] = nuevo_estado

        if not fields:
            raise ValidationError("Nada que actualizar")

        if nuevo_estado:
            if self.repo.find_overlaps(cmin, cmax, exclude_id=promocion_id):
                raise ConflictError("El rango se superpone con una promoción activa")

        return self.repo.update(promocion_id, **fields)


class EliminarPromocionUseCase:
    def __init__(self, repo: PromocionRepository):
        self.repo = repo

    def execute(self, promocion_id):
        if self.repo.find_by_id(promocion_id) is None:
            raise NotFoundError("Promoción no existe")
        self.repo.delete(promocion_id)
