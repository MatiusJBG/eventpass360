"""Casos de uso de entradas electrónicas."""
from src.domain.exceptions import ConflictError, NotFoundError
from src.domain.repositories import EntradaRepository
from src.domain.validators import validate_codigo, validate_positive_int


class GenerarEntradasUseCase:
    def __init__(self, repo: EntradaRepository):
        self.repo = repo

    def execute(self, compra_id):
        compra_id = validate_positive_int(compra_id, "compra_id")
        return self.repo.generar(compra_id)


class ValidarEntradaUseCase:
    def __init__(self, repo: EntradaRepository):
        self.repo = repo

    def execute(self, codigo, evento_id):
        codigo = validate_codigo(codigo)
        evento_id = validate_positive_int(evento_id, "evento_id")
        entrada = self.repo.find_by_codigo(codigo)
        if entrada is None:
            raise NotFoundError("Código inexistente")
        if entrada.evento_id != evento_id:
            raise ConflictError("El código pertenece a otro evento")
        if entrada.estado != "DISPONIBLE":
            raise ConflictError("El código ya fue utilizado")
        updated = self.repo.validar(codigo, evento_id)
        if updated is None:
            raise ConflictError("El código ya fue utilizado")
        return updated


class ListarEntradasUseCase:
    def __init__(self, repo: EntradaRepository):
        self.repo = repo

    def execute(self, compra_id=None, usuario_id=None):
        if compra_id is not None:
            compra_id = validate_positive_int(compra_id, "compra_id")
        if usuario_id is not None:
            usuario_id = validate_positive_int(usuario_id, "usuario_id")
        return self.repo.list_all(compra_id=compra_id, usuario_id=usuario_id)


class AnularEntradasUseCase:
    def __init__(self, repo: EntradaRepository):
        self.repo = repo

    def execute(self, compra_id):
        compra_id = validate_positive_int(compra_id, "compra_id")
        self.repo.anular_por_compra(compra_id)
        return {"message": "Entradas anuladas"}
