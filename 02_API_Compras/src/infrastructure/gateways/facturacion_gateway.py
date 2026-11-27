"""Gateway HTTP hacia API Facturación (:5004)."""
import requests

from src.domain.exceptions import ServiceUnavailableError


class FacturacionGateway:
    def __init__(self, base_url: str, timeout: int):
        self.base_url = base_url.rstrip("/")
        self.timeout = timeout

    def emitir(self, compra_id, cliente, items, totales):
        try:
            r = requests.post(
                self.base_url + "/api/factura",
                json={"compra_id": compra_id, "cliente": cliente, "items": items, "totales": totales},
                timeout=self.timeout,
            )
        except requests.RequestException as exc:
            raise ServiceUnavailableError("API Facturación no disponible") from exc
        if r.status_code >= 400:
            raise ServiceUnavailableError(f"API Facturación respondió {r.status_code}")
        return r.json()

    def anular_por_compra(self, compra_id):
        try:
            r = requests.get(self.base_url + "/api/factura", params={"compra_id": compra_id}, timeout=self.timeout)
        except requests.RequestException as exc:
            raise ServiceUnavailableError("API Facturación no disponible") from exc
        if r.status_code >= 400:
            return
        for factura in r.json():
            if factura.get("compra_id") == compra_id:
                try:
                    requests.patch(self.base_url + f"/api/factura/{factura['id']}/anular", timeout=self.timeout)
                except requests.RequestException:
                    pass
                return
