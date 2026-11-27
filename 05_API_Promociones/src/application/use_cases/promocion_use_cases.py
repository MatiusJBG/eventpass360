"""Casos de uso de CRUD de promociones (ADMIN)."""
from decimal import Decimal, InvalidOperation
import math
import re

from src.domain.exceptions import ConflictError, NotFoundError, ValidationError
from src.domain.repositories import PromocionRepository

UNSET = object()
MAX_CANTIDAD = 1_000_000
_EMOJI_RE = re.compile(
    "[\U0001F000-\U0001FAFF\U00002600-\U000027BF\U00002300-\U000023FF"
    "\U00002B00-\U00002BFF\uFE00-\uFE0F\u200D\u20E3\U0001F1E6-\U0001F1FF]"
)
_DIGITS_RE = re.compile(r"^[0-9]+$")
_DECIMAL_RE = re.compile(r"^[+-]?\d+(?:\.\d+)?$")


def _check_no_emojis(value: str, field_name: str) -> None:
    if _EMOJI_RE.search(value):
        raise ValidationError(f"No se permiten emojis en el campo '{field_name}'")


def _parse_int(value, field_name: str) -> int:
    if isinstance(value, (bool, float)) or value is None:
        raise ValidationError(f"{field_name} debe ser entero")
    if isinstance(value, str):
        _check_no_emojis(value, field_name)
        s = value.strip()
        if not _DIGITS_RE.fullmatch(s):
            raise ValidationError(f"{field_name} debe ser entero")
        return int(s)
    if isinstance(value, int):
        return value
    raise ValidationError(f"{field_name} debe ser entero")


def _parse_porcentaje(value) -> Decimal:
    if isinstance(value, bool) or value is None:
        raise ValidationError("porcentaje inválido")
    if isinstance(value, str):
        _check_no_emojis(value, "porcentaje")
        s = value.strip()
        if not _DECIMAL_RE.fullmatch(s):
            raise ValidationError("porcentaje inválido")
        try:
            d = Decimal(s)
        except InvalidOperation:
            raise ValidationError("porcentaje inválido")
    elif isinstance(value, float):
        if math.isnan(value) or math.isinf(value):
            raise ValidationError("porcentaje inválido")
        d = Decimal(str(value))
    elif isinstance(value, (int, Decimal)):
        d = Decimal(str(value))
    else:
        raise ValidationError("porcentaje inválido")
    if not d.is_finite() or d < 0 or d > 100:
        raise ValidationError("porcentaje debe estar entre 0 y 100")
    if d.as_tuple().exponent < -2:
        raise ValidationError("porcentaje admite máximo 2 decimales")
    return d


def _parse_range(cantidad_min, cantidad_max):
    cmin = _parse_int(cantidad_min, "cantidad_min")
    if cmin < 1 or cmin > MAX_CANTIDAD:
        raise ValidationError(f"cantidad_min debe estar entre 1 y {MAX_CANTIDAD}")
    cmax = None
    if cantidad_max not in (None, ""):
        cmax = _parse_int(cantidad_max, "cantidad_max")
        if cmax < cmin:
            raise ValidationError("cantidad_max debe ser >= cantidad_min")
        if cmax > MAX_CANTIDAD:
            raise ValidationError(f"cantidad_max debe ser <= {MAX_CANTIDAD}")
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
        expected_version=None,
    ):
        if expected_version is not None:
            expected_version = _parse_int(expected_version, "row_version")
            if expected_version < 1:
                raise ValidationError("row_version debe ser un entero positivo")

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

        if expected_version is not None and actual.row_version != expected_version:
            raise ConflictError(
                "Conflicto de concurrencia: la promoción fue modificada por otro usuario. Recarga e intenta nuevamente."
            )

        if nuevo_estado:
            if self.repo.find_overlaps(cmin, cmax, exclude_id=promocion_id):
                raise ConflictError("El rango se superpone con una promoción activa")

        updated = self.repo.update(promocion_id, expected_version=expected_version, **fields)
        if updated is None:
            raise NotFoundError("Promoción no existe")
        return updated


class EliminarPromocionUseCase:
    def __init__(self, repo: PromocionRepository):
        self.repo = repo

    def execute(self, promocion_id):
        if self.repo.find_by_id(promocion_id) is None:
            raise NotFoundError("Promoción no existe")
        self.repo.delete(promocion_id)
