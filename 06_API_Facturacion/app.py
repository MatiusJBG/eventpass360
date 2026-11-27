"""EventPass 360 — API Facturación (:5004). Emisión y consulta de XML + PDF."""
from flask import Flask
from flask_cors import CORS

from src.config.container import build_container
from src.config.settings import Settings
from src.presentation.middlewares.error_handler import register_error_handlers
from src.presentation.routes.factura_routes import factura_bp


def create_app() -> Flask:
    settings = Settings.from_env()
    app = Flask(__name__)
    app.config["SETTINGS"] = settings
    app.json.ensure_ascii = False
    CORS(app, resources={r"/api/*": {"origins": settings.cors_origins.split(",")}})

    app.extensions["container"] = build_container(settings)
    app.register_blueprint(factura_bp, url_prefix="/api")

    @app.get("/api/health")
    def health():
        return {"status": "ok", "servicio": "api-facturacion"}

    register_error_handlers(app)
    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5004, debug=False, threaded=True)
