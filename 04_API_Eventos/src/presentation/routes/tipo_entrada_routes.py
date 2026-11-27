"""Rutas de tipos de entrada."""
from flask import Blueprint, current_app, jsonify, request

from src.presentation.middlewares.auth_guard import require_role
from src.presentation.schemas.validators import (
    get_json_body,
    optional_bool,
    optional_non_negative_int,
    optional_positive_int,
    optional_precio,
    optional_tipo_entrada_tipo,
    parse_optional_query_positive_int,
    require_fields,
    require_positive_int,
    require_precio,
    require_tipo_entrada_tipo,
)

tipo_bp = Blueprint("tipos_entrada", __name__)


def _c():
    return current_app.extensions["container"]


@tipo_bp.get("/tipos-entrada")
def list_tipos():
    evento_id = parse_optional_query_positive_int(request.args.get("evento_id"), "evento_id")
    return jsonify([t.to_dict() for t in _c().listar_tipos_entrada.execute(evento_id=evento_id)]), 200


@tipo_bp.post("/tipos-entrada")
@require_role("ADMIN")
def create_tipo():
    data = get_json_body(request)
    require_fields(data, ["evento_id", "tipo", "precio"])
    evento_id = require_positive_int(data.get("evento_id"), "evento_id")
    tipo_nombre = require_tipo_entrada_tipo(data.get("tipo"))
    precio = require_precio(data.get("precio"))
    stock = optional_non_negative_int(data.get("stock"), "stock")
    tipo = _c().crear_tipo_entrada.execute(
        evento_id=evento_id, tipo=tipo_nombre, precio=precio, stock=stock,
    )
    return jsonify(tipo.to_dict()), 201


@tipo_bp.put("/tipos-entrada/<int:tipo_id>")
@require_role("ADMIN")
def update_tipo(tipo_id):
    data = get_json_body(request)
    tipo_nombre = optional_tipo_entrada_tipo(data.get("tipo"))
    precio = optional_precio(data.get("precio"))
    stock = optional_non_negative_int(data.get("stock"), "stock")
    estado = optional_bool(data.get("estado"), "estado")
    row_version = optional_positive_int(data.get("row_version"), "row_version")
    tipo = _c().actualizar_tipo_entrada.execute(
        tipo_id,
        tipo=tipo_nombre,
        precio=precio,
        stock=stock,
        estado=estado,
        row_version=row_version,
    )
    return jsonify(tipo.to_dict()), 200


@tipo_bp.delete("/tipos-entrada/<int:tipo_id>")
@require_role("ADMIN")
def delete_tipo(tipo_id):
    _c().eliminar_tipo_entrada.execute(tipo_id)
    return jsonify({"message": "Tipo de entrada eliminado"}), 200
