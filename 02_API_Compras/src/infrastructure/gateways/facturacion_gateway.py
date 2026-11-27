"""Gateway HTTP hacia API Facturación (:5004)."""
from typing import Optional

import requests

from src.domain.exceptions import ServiceUnavailableError
from src.domain.repositories import FacturacionGateway as FacturacionGatewayPort


class FacturacionGateway(FacturacionGatewayPort):
    def __init__(self, base_url: str, timeout: int):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    @staticmethod
    def _headers(auth_header: str) -> Optional[dict]:
        return {"Authorization": auth_header} if auth_header else None

    def emitir(self, compra_id, cliente, items, totales, auth_header: str = "", codigos=None) -> dict:
        try:
            r = requests.post(
                self.base_url + "/api/factura",
                json={"compra_id": compra_id, "cliente": cliente, "items": items, "totales": totales, "codigos": codigos},
                headers=self._headers(auth_header),
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise ServiceUnavailableError("API Facturación no disponible") from exc
        if r.status_code >= 400:
            raise ServiceUnavailableError(f"API Facturación respondió {r.status_code}")
        return r.json()

    def buscar_por_compra(self, compra_id: int, auth_header: str = "") -> Optional[dict]:
        try:
            r = requests.get(
                self.base_url + "/api/factura",
                params={"compra_id": compra_id},
                headers=self._headers(auth_header),
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise ServiceUnavailableError("API Facturación no disponible") from exc
        if r.status_code >= 400:
            raise ServiceUnavailableError(f"API Facturación respondió {r.status_code}")
        facturas = r.json()
        if not isinstance(facturas, list):
            return None
        for factura in facturas:
            if isinstance(factura, dict) and factura.get("compra_id") == compra_id:
                return factura
        return None

    def anular_por_compra(self, compra_id: int, auth_header: str = "") -> None:
        factura = self.buscar_por_compra(compra_id, auth_header=auth_header)
        if factura is None:
            return
        if factura.get("estado") == "ANULADA":
            return
        try:
            r = requests.patch(
                self.base_url + f"/api/factura/{factura['id']}/anular",
                headers=self._headers(auth_header),
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise ServiceUnavailableError("API Facturación no disponible") from exc
        if r.status_code == 409:
            return
        if r.status_code >= 400:
            raise ServiceUnavailableError(f"API Facturación respondió {r.status_code}")
