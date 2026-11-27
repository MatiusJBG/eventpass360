"""Rutas de tipos de entrada."""
from flask import Blueprint, current_app, jsonify, request

from src.presentation.middlewares.auth_guard import require_role

tipo_bp = Blueprint("tipos_entrada", __name__)


def _c():
    return current_app.extensions["container"]


@tipo_bp.get("/tipos-entrada")
def list_tipos():
    evento_id = request.args.get("evento_id")
    evento_id = int(evento_id) if evento_id not in (None, "") else None
    return jsonify([t.to_dict() for t in _c().listar_tipos_entrada.execute(evento_id=evento_id)]), 200


@tipo_bp.post("/tipos-entrada")
@require_role("ADMIN")
def create_tipo():
    data = request.get_json(silent=True) or {}
    tipo = _c().crear_tipo_entrada.execute(
        evento_id=data.get("evento_id"), tipo=data.get("tipo", ""), precio=data.get("precio"), stock=data.get("stock"),
    )
    return jsonify(tipo.to_dict()), 201


@tipo_bp.put("/tipos-entrada/<int:tipo_id>")
@require_role("ADMIN")
def update_tipo(tipo_id):
    data = request.get_json(silent=True) or {}
    tipo = _c().actualizar_tipo_entrada.execute(
        tipo_id, tipo=data.get("tipo"), precio=data.get("precio"), stock=data.get("stock"), estado=data.get("estado"),
    )
    return jsonify(tipo.to_dict()), 200


@tipo_bp.delete("/tipos-entrada/<int:tipo_id>")
@require_role("ADMIN")
def delete_tipo(tipo_id):
    _c().eliminar_tipo_entrada.execute(tipo_id)
    return jsonify({"message": "Tipo de entrada eliminado"}), 200
