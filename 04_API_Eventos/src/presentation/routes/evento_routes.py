"""Rutas de eventos."""
from flask import Blueprint, current_app, jsonify, request

from src.presentation.middlewares.auth_guard import require_role
from src.presentation.schemas.validators import (
    get_json_body,
    optional_bool,
    optional_non_empty_str,
    optional_positive_int,
    optional_str,
    parse_optional_query_positive_int,
    parse_query_bool,
    require_fields,
    require_non_empty_str,
    require_positive_int,
)

evento_bp = Blueprint("eventos", __name__)


def _c():
    return current_app.extensions["container"]


@evento_bp.get("/eventos")
def list_eventos():
    categoria_id = parse_optional_query_positive_int(request.args.get("categoria_id"), "categoria_id")
    incluir = parse_query_bool(request.args.get("incluir_inactivos"))
    eventos = _c().listar_eventos.execute(
        q=request.args.get("q"), categoria_id=categoria_id, incluir_inactivos=incluir
    )
    return jsonify([e.to_dict() for e in eventos]), 200


@evento_bp.post("/eventos")
@require_role("ADMIN")
def create_evento():
    data = get_json_body(request)
    require_fields(data, ["categoria_id", "nombre", "lugar", "fecha", "imagen_url"])
    categoria_id = require_positive_int(data.get("categoria_id"), "categoria_id")
    nombre = require_non_empty_str(data.get("nombre"), "nombre")
    descripcion = optional_str(data.get("descripcion"), "descripcion") or ""
    lugar = require_non_empty_str(data.get("lugar"), "lugar")
    imagen_url = require_non_empty_str(data.get("imagen_url"), "imagen_url")
    evento = _c().crear_evento.execute(
        categoria_id=categoria_id,
        nombre=nombre,
        descripcion=descripcion,
        lugar=lugar,
        fecha=data.get("fecha"),
        imagen_url=imagen_url,
    )
    return jsonify(evento.to_dict()), 201


@evento_bp.get("/eventos/<int:evento_id>")
def get_evento(evento_id):
    return jsonify(_c().obtener_evento.execute(evento_id).to_dict()), 200


@evento_bp.put("/eventos/<int:evento_id>")
@require_role("ADMIN")
def update_evento(evento_id):
    data = get_json_body(request)
    categoria_id = optional_positive_int(data.get("categoria_id"), "categoria_id")
    nombre = optional_non_empty_str(data.get("nombre"), "nombre")
    descripcion = optional_str(data.get("descripcion"), "descripcion")
    lugar = optional_non_empty_str(data.get("lugar"), "lugar")
    imagen_url = optional_non_empty_str(data.get("imagen_url"), "imagen_url")
    estado = optional_bool(data.get("estado"), "estado")
    evento = _c().actualizar_evento.execute(
        evento_id,
        categoria_id=categoria_id,
        nombre=nombre,
        descripcion=descripcion,
        lugar=lugar,
        fecha=data.get("fecha"),
        imagen_url=imagen_url,
        estado=estado,
    )
    return jsonify(evento.to_dict()), 200


@evento_bp.delete("/eventos/<int:evento_id>")
@require_role("ADMIN")
def delete_evento(evento_id):
    result = _c().eliminar_evento.execute(evento_id)
    return jsonify(result), 200


@evento_bp.get("/eventos/<int:evento_id>/entradas")
def list_entradas(evento_id):
    entradas = _c().listar_entradas_evento.execute(evento_id)
    return jsonify([t.to_dict() for t in entradas]), 200
