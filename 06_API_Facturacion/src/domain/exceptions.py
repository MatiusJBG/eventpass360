"""Excepciones semánticas del dominio."""


class DomainError(Exception):
    status = 500
    code = "DOMAIN_ERROR"

    def __init__(self, message: str, status: int | None = None, code: str | None = None):
        super().__init__(message)
        self.message = message
        if status is not None:
            self.status = status
        if code is not None:
            self.code = code


class NotFoundError(DomainError):
    status = 404
    code = "NOT_FOUND"


class ValidationError(DomainError):
    status = 400
    code = "VALIDATION_ERROR"


class ConflictError(DomainError):
    status = 409
    code = "CONFLICT"
