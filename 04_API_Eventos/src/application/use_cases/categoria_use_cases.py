"""Casos de uso de categorías."""
from src.domain.exceptions import ConflictError, NotFoundError, ValidationError
from src.domain.repositories import CategoriaRepository


class ListarCategoriasUseCase:
    def __init__(self, repo: CategoriaRepository):
        self.repo = repo

    def execute(self):
        return self.repo.list()


class CrearCategoriaUseCase:
    def __init__(self, repo: CategoriaRepository):
        self.repo = repo

    def execute(self, nombre: str, descripcion: str = ""):
        if not isinstance(nombre, str) or not nombre.strip():
            raise ValidationError("El nombre es obligatorio")
        nombre_norm = nombre.strip()
        if descripcion is None:
            descripcion = ""
        elif not isinstance(descripcion, str):
            raise ValidationError("La descripción debe ser texto")
        if self.repo.find_by_nombre(nombre_norm) is not None:
            raise ConflictError("La categoría ya existe")
        return self.repo.create(nombre_norm, descripcion.strip())


class ActualizarCategoriaUseCase:
    def __init__(self, repo: CategoriaRepository):
        self.repo = repo

    def execute(self, categoria_id: int, nombre=None, descripcion=None, estado=None):
        if self.repo.find_by_id(categoria_id) is None:
            raise NotFoundError("Categoría no existe")
        if nombre is None and descripcion is None and estado is None:
            raise ValidationError("Nada que actualizar")
        nombre_norm = None
        if nombre is not None:
            if not isinstance(nombre, str) or not nombre.strip():
                raise ValidationError("El nombre de la categoría no puede estar vacío")
            nombre_norm = nombre.strip()
            existing = self.repo.find_by_nombre(nombre_norm)
            if existing is not None and existing.id != categoria_id:
                raise ConflictError("La categoría ya existe")
        if descripcion is not None and not isinstance(descripcion, str):
            raise ValidationError("La descripción debe ser texto")
        if estado is not None and not isinstance(estado, bool):
            raise ValidationError("estado debe ser booleano")
        return self.repo.update(categoria_id, nombre=nombre_norm, descripcion=descripcion, estado=estado)


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
