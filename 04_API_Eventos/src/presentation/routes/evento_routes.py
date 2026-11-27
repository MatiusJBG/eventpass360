"""Rutas de eventos."""
from flask import Blueprint, current_app, jsonify, request

from src.presentation.middlewares.auth_guard import require_role

evento_bp = Blueprint("eventos", __name__)


def _c():
    return current_app.extensions["container"]


def _parse_bool(value):
    return str(value).lower() in ("true", "1", "yes")


@evento_bp.get("/eventos")
def list_eventos():
    categoria_id = request.args.get("categoria_id")
    categoria_id = int(categoria_id) if categoria_id not in (None, "") else None
    incluir = _parse_bool(request.args.get("incluir_inactivos"))
    eventos = _c().listar_eventos.execute(
        q=request.args.get("q"), categoria_id=categoria_id, incluir_inactivos=incluir
    )
    return jsonify([e.to_dict() for e in eventos]), 200


@evento_bp.post("/eventos")
@require_role("ADMIN")
def create_evento():
    data = request.get_json(silent=True) or {}
    evento = _c().crear_evento.execute(
        categoria_id=data.get("categoria_id"), nombre=data.get("nombre", ""), descripcion=data.get("descripcion", ""),
        lugar=data.get("lugar", ""), fecha=data.get("fecha"), imagen_url=data.get("imagen_url", ""),
    )
    return jsonify(evento.to_dict()), 201


@evento_bp.get("/eventos/<int:evento_id>")
def get_evento(evento_id):
    return jsonify(_c().obtener_evento.execute(evento_id).to_dict()), 200


@evento_bp.put("/eventos/<int:evento_id>")
@require_role("ADMIN")
def update_evento(evento_id):
    data = request.get_json(silent=True) or {}
    evento = _c().actualizar_evento.execute(
        evento_id, categoria_id=data.get("categoria_id"), nombre=data.get("nombre"), descripcion=data.get("descripcion"),
        lugar=data.get("lugar"), fecha=data.get("fecha"), imagen_url=data.get("imagen_url"), estado=data.get("estado"),
    )
    return jsonify(evento.to_dict()), 200


@evento_bp.delete("/eventos/<int:evento_id>")
@require_role("ADMIN")
def delete_evento(evento_id):
    _c().eliminar_evento.execute(evento_id)
    return jsonify({"message": "Evento eliminado"}), 200


@evento_bp.get("/eventos/<int:evento_id>/entradas")
def list_entradas(evento_id):
    entradas = _c().listar_entradas_evento.execute(evento_id)
    return jsonify([t.to_dict() for t in entradas]), 200
