"""Rutas de promociones."""
from flask import Blueprint, current_app, jsonify, request

from src.presentation.middlewares.auth_guard import require_role
from src.presentation.schemas.validators import (
    parse_calcular_payload,
    parse_create_promocion_payload,
    parse_update_promocion_payload,
)

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
    cantidad_min, cantidad_max, porcentaje = parse_create_promocion_payload(request.get_json(silent=True))
    p = _c().crear_promocion.execute(cantidad_min, cantidad_max, porcentaje)
    return jsonify(p.to_dict()), 201


@promocion_bp.put("/promociones/<int:promocion_id>")
@require_role("ADMIN")
def update_promocion(promocion_id):
    kwargs = parse_update_promocion_payload(request.get_json(silent=True))
    p = _c().actualizar_promocion.execute(promocion_id, **kwargs)
    return jsonify(p.to_dict()), 200


@promocion_bp.delete("/promociones/<int:promocion_id>")
@require_role("ADMIN")
def delete_promocion(promocion_id):
    _c().eliminar_promocion.execute(promocion_id)
    return jsonify({"message": "Promoción eliminada"}), 200


@promocion_bp.post("/promociones/calcular")
def calcular():
    kwargs = parse_calcular_payload(request.get_json(silent=True))
    return jsonify(_c().calcular_promocion.execute(**kwargs)), 200
