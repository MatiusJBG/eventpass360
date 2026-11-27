"""Traductor de excepciones de dominio a JSON HTTP."""
from flask import jsonify

from src.domain.exceptions import DomainError


def register_error_handlers(app):
    @app.errorhandler(DomainError)
    def _handle_domain(err):
        return jsonify({"error": err.code, "message": err.message}), err.status

    @app.errorhandler(404)
    def _handle_404(err):
        return jsonify({"error": "NOT_FOUND", "message": "Recurso no encontrado"}), 404

    @app.errorhandler(405)
    def _handle_405(err):
        return jsonify({"error": "METHOD_NOT_ALLOWED", "message": "Método no permitido"}), 405

    @app.errorhandler(Exception)
    def _handle_unexpected(err):
        app.logger.exception("Error inesperado: %s", err)
        return jsonify({"error": "INTERNAL_ERROR", "message": "Error interno del servidor"}), 500
