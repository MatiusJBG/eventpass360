"""Rutas públicas de autenticación y perfil propio."""
from flask import Blueprint, current_app, g, jsonify, request

from src.presentation.middlewares.auth_guard import require_auth

auth_bp = Blueprint("auth", __name__)


def _container():
    return current_app.extensions["container"]


@auth_bp.get("/health")
def health():
    return jsonify({"status": "ok", "servicio": "api-usuarios"}), 200


@auth_bp.post("/login")
def login():
    data = request.get_json(silent=True) or {}
    result = _container().login_use_case.execute(data.get("correo", ""), data.get("password", ""))
    return jsonify(result), 200


@auth_bp.post("/registro")
def registro():
    data = request.get_json(silent=True) or {}
    usuario = _container().registro_use_case.execute(
        data.get("nombre", ""), data.get("correo", ""), data.get("password", "")
    )
    return jsonify(usuario.to_dict()), 201


@auth_bp.get("/perfil")
@require_auth
def get_perfil():
    usuario = _container().get_perfil_use_case.execute(int(g.current_user["sub"]))
    return jsonify(usuario.to_dict()), 200


@auth_bp.put("/perfil")
@require_auth
def put_perfil():
    data = request.get_json(silent=True) or {}
    usuario = _container().update_perfil_use_case.execute(
        int(g.current_user["sub"]),
        nombre=data.get("nombre"),
        correo=data.get("correo"),
        password=data.get("password"),
    )
    return jsonify(usuario.to_dict()), 200
