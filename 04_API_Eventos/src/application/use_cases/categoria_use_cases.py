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
        nombre = (nombre or "").strip()
        if not nombre:
            raise ValidationError("El nombre es obligatorio")
        if self.repo.find_by_nombre(nombre) is not None:
            raise ConflictError("La categoría ya existe")
        return self.repo.create(nombre, descripcion or "")


class ActualizarCategoriaUseCase:
    def __init__(self, repo: CategoriaRepository):
        self.repo = repo

    def execute(self, categoria_id: int, nombre=None, descripcion=None, estado=None):
        if self.repo.find_by_id(categoria_id) is None:
            raise NotFoundError("Categoría no existe")
        if nombre:
            existing = self.repo.find_by_nombre(nombre.strip())
            if existing is not None and existing.id != categoria_id:
                raise ConflictError("La categoría ya existe")
        return self.repo.update(categoria_id, nombre=nombre, descripcion=descripcion, estado=estado)


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
