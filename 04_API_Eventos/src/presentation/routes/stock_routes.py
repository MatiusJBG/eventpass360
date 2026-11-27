"""Rutas internas de stock (cotizar / descontar / restaurar)."""
from flask import Blueprint, current_app, jsonify, request

from src.presentation.middlewares.auth_guard import require_auth
from src.presentation.schemas.validators import get_json_body, require_items_list

stock_bp = Blueprint("stock", __name__)


def _c():
    return current_app.extensions["container"]


@stock_bp.post("/stock/cotizar")
def cotizar():
    data = get_json_body(request)
    items = require_items_list(data)
    return jsonify(_c().cotizar_stock.execute(items)), 200


@stock_bp.post("/stock/descontar")
@require_auth
def descontar():
    data = get_json_body(request)
    items = require_items_list(data)
    return jsonify(_c().descontar_stock.execute(items)), 200


@stock_bp.post("/stock/restaurar")
@require_auth
def restaurar():
    data = get_json_body(request)
    items = require_items_list(data)
    return jsonify(_c().restaurar_stock.execute(items)), 200
