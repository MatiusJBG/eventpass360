"""Gateway HTTP hacia API Eventos (:5002)."""
import requests

from src.domain.exceptions import ConflictError, ServiceUnavailableError
from src.domain.repositories import EventosGateway as EventosGatewayPort


class EventosGateway(EventosGatewayPort):
    def __init__(self, base_url: str, timeout: int):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def _post(self, path, payload, auth_header: str = ""):
        headers = {"Authorization": auth_header} if auth_header else None
        try:
            r = requests.post(self.base_url + path, json=payload, headers=headers, timeout=self.timeout)
        except requests.RequestException as exc:
            raise ServiceUnavailableError("API Eventos no disponible") from exc
        if r.status_code == 409:
            try:
                msg = r.json().get("message", "Stock insuficiente")
            except ValueError:
                msg = "Stock insuficiente"
            raise ConflictError(msg)
        if r.status_code >= 400:
            raise ServiceUnavailableError(f"API Eventos respondió {r.status_code}")
        return r.json()

    def cotizar(self, items):
        return self._post("/api/stock/cotizar", {"items": items})

    def descontar(self, items, auth_header: str = ""):
        return self._post("/api/stock/descontar", {"items": items}, auth_header=auth_header)

    def restaurar(self, items, auth_header: str = ""):
        return self._post("/api/stock/restaurar", {"items": items}, auth_header=auth_header)
