"""Configuración tipada."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    database_url: str
    jwt_secret_key: str
    cors_origins: str
    url_eventos: str
    url_promociones: str
    url_facturacion: str
    url_entradas: str
    http_timeout: int

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        return cls(
            database_url=os.getenv("DATABASE_URL", ""),
            jwt_secret_key=os.getenv("JWT_SECRET_KEY", "dev-secret-inseguro"),
            cors_origins=os.getenv("CORS_ORIGINS", "*"),
            url_eventos=os.getenv("URL_EVENTOS", "http://localhost:5002"),
            url_promociones=os.getenv("URL_PROMOCIONES", "http://localhost:5003"),
            url_facturacion=os.getenv("URL_FACTURACION", "http://localhost:5004"),
            url_entradas=os.getenv("URL_ENTRADAS", "http://localhost:5005"),
            http_timeout=int(os.getenv("HTTP_TIMEOUT", "10")),
        )
