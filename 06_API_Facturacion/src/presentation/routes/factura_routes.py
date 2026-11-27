"""Rutas de facturación."""
import base64

from flask import Blueprint, Response, current_app, g, jsonify, request

from src.presentation.middlewares.auth_guard import require_auth
from src.presentation.schemas.validators import (
    parse_emitir_factura_payload,
    parse_optional_positive_int,
)

factura_bp = Blueprint("facturas", __name__)


def _c():
    return current_app.extensions["container"]


@factura_bp.post("/factura")
@require_auth
def emitir():
    payload = parse_emitir_factura_payload(request.get_json(silent=True))
    factura = _c().emitir_factura.execute(
        compra_id=payload["compra_id"],
        cliente=payload["cliente"],
        items=payload["items"],
        totales=payload["totales"],
    )
    return jsonify(factura.to_dict()), 201


@factura_bp.get("/factura")
@require_auth
def listar():
    compra_id = parse_optional_positive_int(request.args.get("compra_id"), "compra_id")
    user = g.current_user
    usuario_id = None if user.get("rol") == "ADMIN" else int(user["sub"])
    facturas = _c().listar_facturas.execute(compra_id=compra_id, usuario_id=usuario_id)
    return jsonify([x.to_dict() for x in facturas]), 200


@factura_bp.get("/factura/<int:factura_id>/xml")
@require_auth
def xml(factura_id):
    factura = _c().obtener_factura.execute(factura_id, usuario=g.current_user)
    return Response(factura.xml, mimetype="application/xml")


@factura_bp.get("/factura/<int:factura_id>/pdf")
@require_auth
def pdf(factura_id):
    factura = _c().obtener_factura.execute(factura_id, usuario=g.current_user)
    data = base64.b64decode(factura.pdf_base64)
    return Response(data, mimetype="application/pdf")


@factura_bp.patch("/factura/<int:factura_id>/anular")
@require_auth
def anular(factura_id):
    factura = _c().anular_factura.execute(factura_id, usuario=g.current_user)
    return jsonify(factura.to_dict()), 200
