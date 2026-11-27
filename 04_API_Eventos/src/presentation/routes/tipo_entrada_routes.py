"""Rutas de tipos de entrada."""
from flask import Blueprint, current_app, jsonify, request

from src.presentation.middlewares.auth_guard import require_role
from src.presentation.schemas.validators import (
    get_json_body,
    optional_bool,
    optional_non_empty_str,
    optional_non_negative_int,
    parse_optional_query_positive_int,
    require_fields,
    require_non_empty_str,
    require_positive_int,
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
    tipo_nombre = require_non_empty_str(data.get("tipo"), "tipo")
    stock = optional_non_negative_int(data.get("stock"), "stock")
    tipo = _c().crear_tipo_entrada.execute(
        evento_id=evento_id, tipo=tipo_nombre, precio=data.get("precio"), stock=stock,
    )
    return jsonify(tipo.to_dict()), 201


@tipo_bp.put("/tipos-entrada/<int:tipo_id>")
@require_role("ADMIN")
def update_tipo(tipo_id):
    data = get_json_body(request)
    tipo_nombre = optional_non_empty_str(data.get("tipo"), "tipo")
    stock = optional_non_negative_int(data.get("stock"), "stock")
    estado = optional_bool(data.get("estado"), "estado")
    tipo = _c().actualizar_tipo_entrada.execute(
        tipo_id, tipo=tipo_nombre, precio=data.get("precio"), stock=stock, estado=estado,
    )
    return jsonify(tipo.to_dict()), 200


@tipo_bp.delete("/tipos-entrada/<int:tipo_id>")
@require_role("ADMIN")
def delete_tipo(tipo_id):
    _c().eliminar_tipo_entrada.execute(tipo_id)
    return jsonify({"message": "Tipo de entrada eliminado"}), 200
