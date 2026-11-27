"""Generador de factura XML (esquema exacto del PDF)."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import xml.dom.minidom as minidom
import xml.etree.ElementTree as ET

from src.domain.repositories import XmlGenerator

MONEY = Decimal("0.01")


class GenerarFacturaXmlService(XmlGenerator):
    def generar(self, numero, fecha, cliente, items, totales, codigos=None) -> str:
        factura = ET.Element("Factura")

        cabecera = ET.SubElement(factura, "Cabecera")
        ET.SubElement(cabecera, "Numero").text = str(numero)
        ET.SubElement(cabecera, "Fecha").text = fecha.isoformat()
        ET.SubElement(cabecera, "Estado").text = "EMITIDA"

        cli = ET.SubElement(factura, "Cliente")
        ET.SubElement(cli, "Id").text = str(cliente.get("id", ""))
        ET.SubElement(cli, "Nombre").text = str(cliente.get("nombre", ""))
        ET.SubElement(cli, "Correo").text = str(cliente.get("correo", ""))

        detalle = ET.SubElement(factura, "Detalle")
        for it in items:
            item = ET.SubElement(detalle, "Item")
            ET.SubElement(item, "Descripcion").text = str(it.get("descripcion", ""))
            ET.SubElement(item, "Cantidad").text = str(it.get("cantidad", ""))
            ET.SubElement(item, "PrecioUnitario").text = self._money(it.get("precio_unitario", 0))
            ET.SubElement(item, "Subtotal").text = self._money(it.get("subtotal", 0))

        if codigos:
            entradas_el = ET.SubElement(factura, "Entradas")
            for c in codigos:
                entrada_el = ET.SubElement(entradas_el, "Entrada")
                ET.SubElement(entrada_el, "Codigo").text = str(c.get("codigo", ""))
                ET.SubElement(entrada_el, "Evento").text = str(c.get("evento", ""))

        totales_el = ET.SubElement(factura, "Totales")
        ET.SubElement(totales_el, "Subtotal").text = self._money(totales.get("subtotal", 0))
        ET.SubElement(totales_el, "Descuento").text = self._money(totales.get("descuento", 0))
        ET.SubElement(totales_el, "BaseImponible").text = self._money(totales.get("base_imponible", 0))
        ET.SubElement(totales_el, "IVA").text = self._money(totales.get("iva", 0))
        ET.SubElement(totales_el, "Total").text = self._money(totales.get("total", 0))

        rough = ET.tostring(factura, encoding="utf-8")
        parsed = minidom.parseString(rough)
        return parsed.toprettyxml(indent="  ", encoding="utf-8").decode("utf-8")

    @staticmethod
    def _money(value) -> str:
        if isinstance(value, bool) or value is None:
            return "0.00"
        try:
            d = Decimal(str(value))
            if not d.is_finite():
                return "0.00"
            return f"{d.quantize(MONEY, rounding=ROUND_HALF_UP):.2f}"
        except (InvalidOperation, TypeError, ValueError):
            return "0.00"
