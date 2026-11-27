"""Rutas de facturación."""
import base64

from flask import Blueprint, current_app, jsonify, request, Response

factura_bp = Blueprint("facturas", __name__)


def _c():
    return current_app.extensions["container"]


@factura_bp.post("/factura")
def emitir():
    data = request.get_json(silent=True) or {}
    factura = _c().emitir_factura.execute(
        compra_id=data.get("compra_id"),
        cliente=data.get("cliente") or {},
        items=data.get("items") or [],
        totales=data.get("totales") or {},
    )
    return jsonify(factura.to_dict()), 201


@factura_bp.get("/factura")
def listar():
    compra_id = request.args.get("compra_id")
    compra_id = int(compra_id) if compra_id not in (None, "") else None
    facturas = _c().listar_facturas.execute(compra_id=compra_id)
    return jsonify([x.to_dict() for x in facturas]), 200


@factura_bp.get("/factura/<int:factura_id>/xml")
def xml(factura_id):
    factura = _c().obtener_factura.execute(factura_id)
    return Response(factura.xml, mimetype="application/xml")


@factura_bp.get("/factura/<int:factura_id>/pdf")
def pdf(factura_id):
    factura = _c().obtener_factura.execute(factura_id)
    data = base64.b64decode(factura.pdf_base64)
    return Response(data, mimetype="application/pdf")


@factura_bp.patch("/factura/<int:factura_id>/anular")
def anular(factura_id):
    factura = _c().anular_factura.execute(factura_id)
    return jsonify(factura.to_dict()), 200
