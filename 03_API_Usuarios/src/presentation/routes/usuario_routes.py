"""CRUD de usuarios (ADMIN)."""
from flask import Blueprint, current_app, jsonify, request

from src.presentation.middlewares.auth_guard import require_role

usuario_bp = Blueprint("usuarios", __name__)


def _container():
    return current_app.extensions["container"]


@usuario_bp.get("/usuarios")
@require_role("ADMIN")
def list_usuarios():
    usuarios = _container().listar_usuarios_use_case.execute(request.args.get("q"))
    return jsonify([u.to_dict() for u in usuarios]), 200


@usuario_bp.post("/usuarios")
@require_role("ADMIN")
def create_usuario():
    data = request.get_json(silent=True) or {}
    usuario = _container().crear_usuario_use_case.execute(
        rol_id=data.get("rol_id"),
        nombre=data.get("nombre", ""),
        correo=data.get("correo", ""),
        password=data.get("password", ""),
    )
    return jsonify(usuario.to_dict()), 201


@usuario_bp.put("/usuarios/<int:usuario_id>")
@require_role("ADMIN")
def update_usuario(usuario_id):
    data = request.get_json(silent=True) or {}
    usuario = _container().actualizar_usuario_use_case.execute(
        usuario_id,
        nombre=data.get("nombre"),
        correo=data.get("correo"),
        rol_id=data.get("rol_id"),
        password=data.get("password"),
    )
    return jsonify(usuario.to_dict()), 200


@usuario_bp.delete("/usuarios/<int:usuario_id>")
@require_role("ADMIN")
def delete_usuario(usuario_id):
    _container().desactivar_usuario_use_case.execute(usuario_id)
    return jsonify({"message": "Usuario eliminado"}), 200
