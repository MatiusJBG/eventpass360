"""Rutas internas de stock (cotizar / descontar / restaurar)."""
from flask import Blueprint, current_app, jsonify, request

stock_bp = Blueprint("stock", __name__)


def _c():
    return current_app.extensions["container"]


@stock_bp.post("/stock/cotizar")
def cotizar():
    data = request.get_json(silent=True) or {}
    return jsonify(_c().cotizar_stock.execute(data.get("items", []))), 200


@stock_bp.post("/stock/descontar")
def descontar():
    data = request.get_json(silent=True) or {}
    return jsonify(_c().descontar_stock.execute(data.get("items", []))), 200


@stock_bp.post("/stock/restaurar")
def restaurar():
    data = request.get_json(silent=True) or {}
    return jsonify(_c().restaurar_stock.execute(data.get("items", []))), 200
