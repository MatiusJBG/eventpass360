"""Gateway HTTP hacia API Entradas (:5005)."""
from typing import Optional

import requests

from src.domain.exceptions import ServiceUnavailableError
from src.domain.repositories import EntradasGateway as EntradasGatewayPort


class EntradasGateway(EntradasGatewayPort):
    def __init__(self, base_url: str, timeout: int):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    @staticmethod
    def _headers(auth_header: str) -> Optional[dict]:
        return {"Authorization": auth_header} if auth_header else None

    def generar(self, compra_id, auth_header: str = "") -> list:
        try:
            r = requests.post(
                self.base_url + "/api/entradas/generar",
                json={"compra_id": compra_id},
                headers=self._headers(auth_header),
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise ServiceUnavailableError("API Entradas no disponible") from exc
        if r.status_code >= 400:
            raise ServiceUnavailableError(f"API Entradas respondió {r.status_code}")
        data = r.json()
        return data if isinstance(data, list) else []

    def anular_por_compra(self, compra_id, auth_header: str = "") -> None:
        try:
            requests.patch(
                self.base_url + f"/api/entradas/compra/{compra_id}/anular",
                headers=self._headers(auth_header),
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise ServiceUnavailableError("API Entradas no disponible") from exc
