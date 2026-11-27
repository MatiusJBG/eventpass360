"""Gateway HTTP hacia API Promociones (:5003)."""
import requests

from src.domain.exceptions import ServiceUnavailableError


class PromocionesGateway:
    def __init__(self, base_url: str, timeout: int):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def calcular(self, subtotal, cantidad_total):
        try:
            r = requests.post(
                self.base_url + "/api/promociones/calcular",
                json={"subtotal": subtotal, "cantidad_total": cantidad_total},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise ServiceUnavailableError("API Promociones no disponible") from exc
        if r.status_code >= 400:
            raise ServiceUnavailableError(f"API Promociones respondió {r.status_code}")
        return r.json()
