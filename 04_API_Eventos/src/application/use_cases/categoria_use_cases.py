"""Casos de uso de categorías."""
from typing import Optional

from src.domain.exceptions import ConflictError, NotFoundError, ValidationError
from src.domain.repositories import CategoriaRepository
from src.domain.validators import (
    validate_categoria_descripcion,
    validate_categoria_nombre,
    validate_positive_int,
)


class ListarCategoriasUseCase:
    def __init__(self, repo: CategoriaRepository):
        self.repo = repo

    def execute(self):
        return self.repo.list()


class CrearCategoriaUseCase:
    def __init__(self, repo: CategoriaRepository):
        self.repo = repo

    def execute(self, nombre: str, descripcion: str = ""):
        nombre_norm = validate_categoria_nombre(nombre)
        desc_norm = validate_categoria_descripcion(descripcion)
        if self.repo.find_by_nombre(nombre_norm) is not None:
            raise ConflictError("La categoría ya existe")
        return self.repo.create(nombre_norm, desc_norm)


class ActualizarCategoriaUseCase:
    def __init__(self, repo: CategoriaRepository):
        self.repo = repo

    def execute(
        self,
        categoria_id: int,
        nombre=None,
        descripcion=None,
        estado=None,
        row_version: Optional[int] = None,
    ):
        if self.repo.find_by_id(categoria_id) is None:
            raise NotFoundError("Categoría no existe")
        expected_version = validate_positive_int(row_version, "row_version") if row_version is not None else None
        if nombre is None and descripcion is None and estado is None:
            raise ValidationError("Nada que actualizar")
        nombre_norm = None
        if nombre is not None:
            nombre_norm = validate_categoria_nombre(nombre)
            existing = self.repo.find_by_nombre(nombre_norm)
            if existing is not None and existing.id != categoria_id:
                raise ConflictError("La categoría ya existe")
        desc_norm = None
        if descripcion is not None:
            desc_norm = validate_categoria_descripcion(descripcion)
        if estado is not None and not isinstance(estado, bool):
            raise ValidationError("estado debe ser booleano")
        return self.repo.update(
            categoria_id,
            nombre=nombre_norm,
            descripcion=desc_norm,
            estado=estado,
            expected_version=expected_version,
        )


class EliminarCategoriaUseCase:
    def __init__(self, repo: CategoriaRepository):
        self.repo = repo

    def execute(self, categoria_id: int):
        if self.repo.find_by_id(categoria_id) is None:
            raise NotFoundError("Categoría no existe")
        if self.repo.count_eventos(categoria_id) > 0:
            self.repo.deactivate(categoria_id)
        else:
            self.repo.delete(categoria_id)
