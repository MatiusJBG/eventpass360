"""CRUD de roles (ADMIN)."""
from flask import Blueprint, current_app, jsonify, request

from src.presentation.middlewares.auth_guard import require_role
from src.presentation.schemas.validators import (
    get_json_body,
    optional_bool,
    optional_nombre_rol,
    optional_positive_int,
    require_fields,
    require_nombre_rol,
)

rol_bp = Blueprint("roles", __name__)


def _container():
    return current_app.extensions["container"]


@rol_bp.get("/roles")
@require_role("ADMIN")
def list_roles():
    roles = _container().listar_roles_use_case.execute()
    return jsonify([r.to_dict() for r in roles]), 200


@rol_bp.post("/roles")
@require_role("ADMIN")
def create_rol():
    data = get_json_body(request)
    require_fields(data, ["nombre"])
    nombre = require_nombre_rol(data.get("nombre"), "nombre")
    rol = _container().crear_rol_use_case.execute(nombre)
    return jsonify(rol.to_dict()), 201


@rol_bp.put("/roles/<int:rol_id>")
@require_role("ADMIN")
def update_rol(rol_id):
    data = get_json_body(request)
    nombre = optional_nombre_rol(data.get("nombre"), "nombre")
    estado = optional_bool(data.get("estado"), "estado")
    row_version = optional_positive_int(data.get("row_version"), "row_version")
    rol = _container().actualizar_rol_use_case.execute(
        rol_id, nombre=nombre, estado=estado, row_version=row_version
    )
    return jsonify(rol.to_dict()), 200


@rol_bp.delete("/roles/<int:rol_id>")
@require_role("ADMIN")
def delete_rol(rol_id):
    _container().eliminar_rol_use_case.execute(rol_id)
    return jsonify({"message": "Rol eliminado"}), 200
