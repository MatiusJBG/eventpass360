"""CRUD de usuarios (ADMIN)."""
from flask import Blueprint, current_app, jsonify, request

from src.presentation.middlewares.auth_guard import require_role
from src.presentation.schemas.validators import (
    get_json_body,
    optional_bool,
    optional_email,
    optional_nombre_usuario,
    optional_password,
    optional_positive_int,
    optional_search_query,
    require_email,
    require_fields,
    require_nombre_usuario,
    require_password,
    require_positive_int,
)

usuario_bp = Blueprint("usuarios", __name__)


def _container():
    return current_app.extensions["container"]


@usuario_bp.get("/usuarios")
@require_role("ADMIN")
def list_usuarios():
    q = optional_search_query(request.args.get("q"), "q")
    usuarios = _container().listar_usuarios_use_case.execute(q)
    return jsonify([u.to_dict() for u in usuarios]), 200


@usuario_bp.post("/usuarios")
@require_role("ADMIN")
def create_usuario():
    data = get_json_body(request)
    require_fields(data, ["rol_id", "nombre", "correo", "password"])
    rol_id = require_positive_int(data.get("rol_id"), "rol_id")
    nombre = require_nombre_usuario(data.get("nombre"), "nombre")
    correo = require_email(data.get("correo"))
    password = require_password(data.get("password"))
    usuario = _container().crear_usuario_use_case.execute(
        rol_id=rol_id,
        nombre=nombre,
        correo=correo,
        password=password,
    )
    return jsonify(usuario.to_dict()), 201


@usuario_bp.put("/usuarios/<int:usuario_id>")
@require_role("ADMIN")
def update_usuario(usuario_id):
    data = get_json_body(request)
    nombre = optional_nombre_usuario(data.get("nombre"), "nombre")
    correo = optional_email(data.get("correo"))
    rol_id = optional_positive_int(data.get("rol_id"), "rol_id")
    password = optional_password(data.get("password"))
    estado = optional_bool(data.get("estado"), "estado")
    row_version = optional_positive_int(data.get("row_version"), "row_version")
    usuario = _container().actualizar_usuario_use_case.execute(
        usuario_id,
        nombre=nombre,
        correo=correo,
        rol_id=rol_id,
        password=password,
        estado=estado,
        row_version=row_version,
    )
    return jsonify(usuario.to_dict()), 200


@usuario_bp.delete("/usuarios/<int:usuario_id>")
@require_role("ADMIN")
def delete_usuario(usuario_id):
    _container().desactivar_usuario_use_case.execute(usuario_id)
    return jsonify({"message": "Usuario eliminado"}), 200
