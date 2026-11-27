"""Rutas públicas de autenticación y perfil propio."""
from flask import Blueprint, current_app, g, jsonify, request

from src.presentation.middlewares.auth_guard import require_auth
from src.presentation.schemas.validators import (
    get_json_body,
    optional_non_empty_str,
    optional_password,
    require_email,
    require_fields,
    require_non_empty_str,
)

auth_bp = Blueprint("auth", __name__)


def _container():
    return current_app.extensions["container"]


@auth_bp.get("/health")
def health():
    return jsonify({"status": "ok", "servicio": "api-usuarios"}), 200


@auth_bp.post("/login")
def login():
    data = get_json_body(request)
    require_fields(data, ["correo", "password"])
    correo = require_non_empty_str(data.get("correo"), "correo").lower()
    password = require_non_empty_str(data.get("password"), "password")
    result = _container().login_use_case.execute(correo, password)
    return jsonify(result), 200


@auth_bp.post("/registro")
def registro():
    data = get_json_body(request)
    require_fields(data, ["nombre", "correo", "password"])
    nombre = require_non_empty_str(data.get("nombre"), "nombre")
    correo = require_email(data.get("correo"))
    password = require_non_empty_str(data.get("password"), "password")
    usuario = _container().registro_use_case.execute(nombre, correo, password)
    return jsonify(usuario.to_dict()), 201


@auth_bp.get("/perfil")
@require_auth
def get_perfil():
    usuario = _container().get_perfil_use_case.execute(int(g.current_user["sub"]))
    return jsonify(usuario.to_dict()), 200


@auth_bp.put("/perfil")
@require_auth
def put_perfil():
    data = get_json_body(request)
    nombre = optional_non_empty_str(data.get("nombre"), "nombre")
    correo = require_email(data["correo"]) if data.get("correo") is not None else None
    password = optional_password(data.get("password"))
    usuario = _container().update_perfil_use_case.execute(
        int(g.current_user["sub"]),
        nombre=nombre,
        correo=correo,
        password=password,
    )
    return jsonify(usuario.to_dict()), 200
