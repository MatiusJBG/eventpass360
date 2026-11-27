"""EventPass 360 — API Usuarios (:5001). Entrypoint limpio (Application Factory)."""
from flask import Flask
from flask_cors import CORS

from src.config.container import Container, build_container
from src.config.settings import Settings
from src.presentation.middlewares.error_handler import register_error_handlers
from src.presentation.routes.auth_routes import auth_bp
from src.presentation.routes.usuario_routes import usuario_bp
from src.presentation.routes.rol_routes import rol_bp


def create_app(container: Container | None = None, settings: Settings | None = None) -> Flask:
    settings = settings or Settings.from_env()
    app = Flask(__name__)
    app.config["SETTINGS"] = settings
    app.json.ensure_ascii = False
    CORS(app, resources={r"/api/*": {"origins": settings.cors_origins.split(",")}})

    app.extensions["container"] = container if container is not None else build_container(settings)

    app.register_blueprint(auth_bp, url_prefix="/api")
    app.register_blueprint(usuario_bp, url_prefix="/api")
    app.register_blueprint(rol_bp, url_prefix="/api")

    register_error_handlers(app)
    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=False, threaded=True)
