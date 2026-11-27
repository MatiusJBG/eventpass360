"""CRUD de roles (ADMIN)."""
from flask import Blueprint, current_app, jsonify, request

from src.presentation.middlewares.auth_guard import require_role

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
    data = request.get_json(silent=True) or {}
    rol = _container().crear_rol_use_case.execute(data.get("nombre", ""))
    return jsonify(rol.to_dict()), 201


@rol_bp.put("/roles/<int:rol_id>")
@require_role("ADMIN")
def update_rol(rol_id):
    data = request.get_json(silent=True) or {}
    rol = _container().actualizar_rol_use_case.execute(
        rol_id, nombre=data.get("nombre"), estado=data.get("estado")
    )
    return jsonify(rol.to_dict()), 200


@rol_bp.delete("/roles/<int:rol_id>")
@require_role("ADMIN")
def delete_rol(rol_id):
    _container().eliminar_rol_use_case.execute(rol_id)
    return jsonify({"message": "Rol eliminado"}), 200
