"""Configuración tipada."""
import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class Settings:
    database_url: str
    cors_origins: str

    @classmethod
    def from_env(cls) -> "Settings":
        load_dotenv()
        return cls(
            database_url=os.getenv("DATABASE_URL", ""),
            cors_origins=os.getenv("CORS_ORIGINS", "*"),
        )
