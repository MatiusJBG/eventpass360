"""Rutas de categorías."""
from flask import Blueprint, current_app, jsonify, request

from src.presentation.middlewares.auth_guard import require_role
from src.presentation.schemas.validators import (
    get_json_body,
    optional_bool,
    optional_non_empty_str,
    optional_str,
    require_fields,
    require_non_empty_str,
)

categoria_bp = Blueprint("categorias", __name__)


def _c():
    return current_app.extensions["container"]


@categoria_bp.get("/categorias")
def list_categorias():
    return jsonify([x.to_dict() for x in _c().listar_categorias.execute()]), 200


@categoria_bp.post("/categorias")
@require_role("ADMIN")
def create_categoria():
    data = get_json_body(request)
    require_fields(data, ["nombre"])
    nombre = require_non_empty_str(data.get("nombre"), "nombre")
    descripcion = optional_str(data.get("descripcion"), "descripcion") or ""
    return jsonify(_c().crear_categoria.execute(nombre, descripcion).to_dict()), 201


@categoria_bp.put("/categorias/<int:categoria_id>")
@require_role("ADMIN")
def update_categoria(categoria_id):
    data = get_json_body(request)
    nombre = optional_non_empty_str(data.get("nombre"), "nombre")
    descripcion = optional_str(data.get("descripcion"), "descripcion")
    estado = optional_bool(data.get("estado"), "estado")
    return jsonify(
        _c().actualizar_categoria.execute(
            categoria_id, nombre=nombre, descripcion=descripcion, estado=estado
        ).to_dict()
    ), 200


@categoria_bp.delete("/categorias/<int:categoria_id>")
@require_role("ADMIN")
def delete_categoria(categoria_id):
    _c().eliminar_categoria.execute(categoria_id)
    return jsonify({"message": "Categoría eliminada"}), 200
