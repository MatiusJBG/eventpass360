"""Rutas de promociones."""
from flask import Blueprint, current_app, jsonify, request

from src.presentation.middlewares.auth_guard import require_role

promocion_bp = Blueprint("promociones", __name__)


def _c():
    return current_app.extensions["container"]


@promocion_bp.get("/promociones")
def list_promociones():
    solo_activas = request.args.get("activas") in ("true", "1")
    return jsonify([p.to_dict() for p in _c().listar_promociones.execute(solo_activas=solo_activas)]), 200


@promocion_bp.post("/promociones")
@require_role("ADMIN")
def create_promocion():
    data = request.get_json(silent=True) or {}
    p = _c().crear_promocion.execute(data.get("cantidad_min"), data.get("cantidad_max"), data.get("porcentaje"))
    return jsonify(p.to_dict()), 201


@promocion_bp.put("/promociones/<int:promocion_id>")
@require_role("ADMIN")
def update_promocion(promocion_id):
    data = request.get_json(silent=True) or {}
    p = _c().actualizar_promocion.execute(
        promocion_id, cantidad_min=data.get("cantidad_min"), cantidad_max=data.get("cantidad_max"),
        porcentaje=data.get("porcentaje"), estado=data.get("estado"),
    )
    return jsonify(p.to_dict()), 200


@promocion_bp.delete("/promociones/<int:promocion_id>")
@require_role("ADMIN")
def delete_promocion(promocion_id):
    _c().eliminar_promocion.execute(promocion_id)
    return jsonify({"message": "Promoción eliminada"}), 200


@promocion_bp.post("/promociones/calcular")
def calcular():
    data = request.get_json(silent=True) or {}
    return jsonify(_c().calcular_promocion.execute(data.get("subtotal"), data.get("cantidad_total"))), 200
