"""Configuración tipada de variables de entorno."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    database_url: str
    jwt_secret_key: str
    cors_origins: str

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        return cls(
            database_url=os.getenv("DATABASE_URL", ""),
            jwt_secret_key=os.getenv("JWT_SECRET_KEY", "dev-secret-inseguro"),
            cors_origins=os.getenv("CORS_ORIGINS", "*"),
        )
