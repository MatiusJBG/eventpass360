"""EventPass 360 — API Compras (:5000). Orquestador SAGA."""
from flask import Flask
from flask_cors import CORS

from src.config.container import build_container
from src.config.settings import Settings
from src.presentation.middlewares.error_handler import register_error_handlers
from src.presentation.routes.compra_routes import compra_bp


def create_app() -> Flask:
    settings = Settings.from_env()
    app = Flask(__name__)
    app.config["SETTINGS"] = settings
    app.json.ensure_ascii = False
    CORS(app, resources={r"/api/*": {"origins": settings.cors_origins.split(",")}})

    app.extensions["container"] = build_container(settings)
    app.register_blueprint(compra_bp, url_prefix="/api")

    @app.get("/api/health")
    def health():
        return {"status": "ok", "servicio": "api-compras"}

    register_error_handlers(app)
    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=False, threaded=True)
