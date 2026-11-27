"""Rutas de compras."""
from flask import Blueprint, current_app, g, jsonify, request

from src.domain.exceptions import ForbiddenError
from src.presentation.middlewares.auth_guard import require_auth, require_role
from src.presentation.schemas.validators import (
    extract_auth_header,
    parse_anular_compra_payload,
    parse_crear_compra_payload,
    parse_previsualizar_payload,
)

compra_bp = Blueprint("compras", __name__)


def _c():
    return current_app.extensions["container"]


@compra_bp.post("/compras/previsualizar")
@require_auth
def previsualizar():
    items = parse_previsualizar_payload(request.get_json(silent=True))
    return jsonify(_c().previsualizar.execute(items)), 200


@compra_bp.post("/compras")
@require_auth
def comprar():
    solicitud_id, items = parse_crear_compra_payload(request.get_json(silent=True))
    user = g.current_user
    usuario = {"sub": int(user["sub"]), "nombre": user.get("nombre", ""), "correo": user.get("correo", "")}
    auth_header = extract_auth_header(request.headers)
    resultado, created = _c().crear_compra.execute(
        usuario, solicitud_id, items, auth_header=auth_header
    )
    return jsonify(resultado), 201 if created else 200


@compra_bp.get("/compras")
@require_auth
def listar():
    user = g.current_user
    if user.get("rol") == "ADMIN":
        compras = _c().listar_compras.execute()
    else:
        compras = _c().listar_compras.execute(usuario_id=int(user["sub"]))
    return jsonify([c.to_dict() for c in compras]), 200


@compra_bp.get("/compras/estadisticas")
@require_role("ADMIN")
def estadisticas():
    return jsonify(_c().estadisticas.execute()), 200


@compra_bp.get("/compras/<int:compra_id>")
@require_auth
def obtener(compra_id):
    compra = _c().obtener_compra.execute(compra_id)
    user = g.current_user
    if user.get("rol") != "ADMIN" and int(user["sub"]) != compra.usuario_id:
        raise ForbiddenError("Sin permiso para ver esta compra")
    return jsonify(compra.to_dict()), 200


@compra_bp.patch("/compras/<int:compra_id>/anular")
@require_auth
def anular(compra_id):
    expected_version = parse_anular_compra_payload(request.get_json(silent=True))
    compra = _c().obtener_compra.execute(compra_id)
    user = g.current_user
    if user.get("rol") != "ADMIN" and int(user["sub"]) != compra.usuario_id:
        raise ForbiddenError("Sin permiso para anular esta compra")
    auth_header = extract_auth_header(request.headers)
    resultado = _c().anular_compra.execute(
        compra_id, auth_header=auth_header, expected_version=expected_version
    )
    return jsonify(resultado.to_dict()), 200
