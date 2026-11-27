"""Rutas de categorías."""
from flask import Blueprint, current_app, jsonify, request

from src.presentation.middlewares.auth_guard import require_role

categoria_bp = Blueprint("categorias", __name__)


def _c():
    return current_app.extensions["container"]


@categoria_bp.get("/categorias")
def list_categorias():
    return jsonify([x.to_dict() for x in _c().listar_categorias.execute()]), 200


@categoria_bp.post("/categorias")
@require_role("ADMIN")
def create_categoria():
    data = request.get_json(silent=True) or {}
    return jsonify(_c().crear_categoria.execute(data.get("nombre", ""), data.get("descripcion", "")).to_dict()), 201


@categoria_bp.put("/categorias/<int:categoria_id>")
@require_role("ADMIN")
def update_categoria(categoria_id):
    data = request.get_json(silent=True) or {}
    return jsonify(_c().actualizar_categoria.execute(
        categoria_id, nombre=data.get("nombre"), descripcion=data.get("descripcion"), estado=data.get("estado")
    ).to_dict()), 200


@categoria_bp.delete("/categorias/<int:categoria_id>")
@require_role("ADMIN")
def delete_categoria(categoria_id):
    _c().eliminar_categoria.execute(categoria_id)
    return jsonify({"message": "Categoría eliminada"}), 200
