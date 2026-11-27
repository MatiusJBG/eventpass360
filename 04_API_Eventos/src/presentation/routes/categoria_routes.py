"""Rutas de categorías."""
from flask import Blueprint, current_app, jsonify, request

from src.presentation.middlewares.auth_guard import require_role
from src.presentation.schemas.validators import (
    get_json_body,
    optional_bool,
    optional_categoria_descripcion,
    optional_categoria_nombre,
    optional_positive_int,
    require_categoria_nombre,
    require_fields,
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
    nombre = require_categoria_nombre(data.get("nombre"))
    descripcion = optional_categoria_descripcion(data.get("descripcion"))
    if descripcion is None:
        descripcion = ""
    return jsonify(_c().crear_categoria.execute(nombre, descripcion).to_dict()), 201


@categoria_bp.put("/categorias/<int:categoria_id>")
@require_role("ADMIN")
def update_categoria(categoria_id):
    data = get_json_body(request)
    nombre = optional_categoria_nombre(data.get("nombre"))
    descripcion = optional_categoria_descripcion(data.get("descripcion"))
    estado = optional_bool(data.get("estado"), "estado")
    row_version = optional_positive_int(data.get("row_version"), "row_version")
    return jsonify(
        _c().actualizar_categoria.execute(
            categoria_id,
            nombre=nombre,
            descripcion=descripcion,
            estado=estado,
            row_version=row_version,
        ).to_dict()
    ), 200


@categoria_bp.delete("/categorias/<int:categoria_id>")
@require_role("ADMIN")
def delete_categoria(categoria_id):
    _c().eliminar_categoria.execute(categoria_id)
    return jsonify({"message": "Categoría eliminada"}), 200
