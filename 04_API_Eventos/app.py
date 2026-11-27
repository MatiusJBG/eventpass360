"""EventPass 360 — API Eventos (:5002). Categorías + Eventos + Entradas + Stock."""
from flask import Flask
from flask_cors import CORS

from src.config.container import build_container
from src.config.settings import Settings
from src.presentation.middlewares.error_handler import register_error_handlers
from src.presentation.routes.categoria_routes import categoria_bp
from src.presentation.routes.evento_routes import evento_bp
from src.presentation.routes.stock_routes import stock_bp
from src.presentation.routes.tipo_entrada_routes import tipo_bp


def create_app() -> Flask:
    settings = Settings.from_env()
    app = Flask(__name__)
    app.config["SETTINGS"] = settings
    app.json.ensure_ascii = False
    CORS(app, resources={r"/api/*": {"origins": settings.cors_origins.split(",")}})

    app.extensions["container"] = build_container(settings)

    app.register_blueprint(categoria_bp, url_prefix="/api")
    app.register_blueprint(evento_bp, url_prefix="/api")
    app.register_blueprint(tipo_bp, url_prefix="/api")
    app.register_blueprint(stock_bp, url_prefix="/api")

    @app.get("/api/health")
    def health():
        return {"status": "ok", "servicio": "api-eventos"}

    register_error_handlers(app)
    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002, debug=False, threaded=True)
