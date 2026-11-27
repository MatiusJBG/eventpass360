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


def _validate_positive_int(value, field: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or value <= 0:
        raise ValidationError(f"{field} debe ser un entero positivo")
    return value


class ListarEventosUseCase:
    def __init__(self, repo: EventoRepository):
        self.repo = repo

    def execute(self, q=None, categoria_id=None, incluir_inactivos=False):
        if categoria_id is not None:
            categoria_id = _validate_positive_int(categoria_id, "categoria_id")
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
        categoria_id_valid = _validate_positive_int(categoria_id, "categoria_id")
        nombre_norm = nombre.strip() if isinstance(nombre, str) else ""
        lugar_norm = lugar.strip() if isinstance(lugar, str) else ""
        imagen_norm = imagen_url.strip() if isinstance(imagen_url, str) else ""
        if not nombre_norm or not lugar_norm or not imagen_norm:
            raise ValidationError("nombre, lugar e imagen_url son obligatorios")
        if descripcion is None:
            descripcion = ""
        elif not isinstance(descripcion, str):
            raise ValidationError("descripcion debe ser texto")
        if self.categoria_repo.find_by_id(categoria_id_valid) is None:
            raise NotFoundError("Categoría no existe")
        return self.repo.create(
            categoria_id_valid, nombre_norm, descripcion.strip(), lugar_norm, _parse_fecha(fecha), imagen_norm
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
    ):
        if self.repo.find_by_id(evento_id) is None:
            raise NotFoundError("Evento no existe")
        fields = {}
        if categoria_id is not None:
            categoria_id_valid = _validate_positive_int(categoria_id, "categoria_id")
            if self.categoria_repo.find_by_id(categoria_id_valid) is None:
                raise NotFoundError("Categoría no existe")
            fields["categoria_id"] = categoria_id_valid
        if nombre is not None:
            if not isinstance(nombre, str) or not nombre.strip():
                raise ValidationError("El nombre no puede estar vacío")
            fields["nombre"] = nombre.strip()
        if descripcion is not None:
            if not isinstance(descripcion, str):
                raise ValidationError("descripcion debe ser texto")
            fields["descripcion"] = descripcion
        if lugar is not None:
            if not isinstance(lugar, str) or not lugar.strip():
                raise ValidationError("El lugar no puede estar vacío")
            fields["lugar"] = lugar.strip()
        if imagen_url is not None:
            if not isinstance(imagen_url, str) or not imagen_url.strip():
                raise ValidationError("imagen_url no puede estar vacío")
            fields["imagen_url"] = imagen_url.strip()
        if fecha is not None:
            fields["fecha"] = _parse_fecha(fecha)
        if estado is not None:
            if not isinstance(estado, bool):
                raise ValidationError("estado debe ser booleano")
            fields["estado"] = estado
        if not fields:
            raise ValidationError("Nada que actualizar")
        return self.repo.update(evento_id, **fields)


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
