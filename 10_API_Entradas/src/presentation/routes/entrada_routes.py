"""Rutas de entradas electrónicas."""
from flask import Blueprint, current_app, g, jsonify, request

from src.presentation.middlewares.auth_guard import require_auth
from src.presentation.schemas.validators import (
    parse_generar_payload,
    parse_optional_positive_int,
    parse_validar_payload,
)

entrada_bp = Blueprint("entradas", __name__)


def _c():
    return current_app.extensions["container"]


@entrada_bp.post("/entradas/generar")
@require_auth
def generar():
    payload = parse_generar_payload(request.get_json(silent=True))
    entradas = _c().generar_entradas.execute(compra_id=payload["compra_id"])
    return jsonify([e.to_dict() for e in entradas]), 200


@entrada_bp.post("/entradas/validar")
def validar():
    payload = parse_validar_payload(request.get_json(silent=True))
    entrada = _c().validar_entrada.execute(codigo=payload["codigo"], evento_id=payload["evento_id"])
    return jsonify(entrada.to_dict()), 200


@entrada_bp.get("/entradas")
@require_auth
def listar():
    compra_id = parse_optional_positive_int(request.args.get("compra_id"), "compra_id")
    user = g.current_user
    usuario_id = None if user.get("rol") == "ADMIN" else int(user["sub"])
    entradas = _c().listar_entradas.execute(compra_id=compra_id, usuario_id=usuario_id)
    return jsonify([e.to_dict() for e in entradas]), 200


@entrada_bp.patch("/entradas/compra/<int:compra_id>/anular")
@require_auth
def anular(compra_id):
    return jsonify(_c().anular_entradas.execute(compra_id=compra_id)), 200
