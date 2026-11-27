"""Generador de factura PDF académica con logo vectorial (ReportLab)."""
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from io import BytesIO
from xml.sax.saxutils import escape

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle

from src.domain.repositories import PdfGenerator

BRAND = colors.HexColor("#1e1b4b")
ACCENT = colors.HexColor("#7c3aed")
MONEY = Decimal("0.01")


class GenerarFacturaPdfService(PdfGenerator):
    def generar(self, numero, fecha, cliente, items, totales, codigos=None) -> bytes:
        buf = BytesIO()
        doc = SimpleDocTemplate(
            buf, pagesize=A4, topMargin=22 * mm, bottomMargin=20 * mm,
            leftMargin=18 * mm, rightMargin=18 * mm,
        )
        styles = getSampleStyleSheet()
        title = ParagraphStyle("t", parent=styles["Title"], fontSize=24, textColor=BRAND, spaceAfter=2)
        sub = ParagraphStyle("s", parent=styles["Normal"], fontSize=10, textColor=colors.HexColor("#555555"))
        cell_style = ParagraphStyle("c", parent=styles["Normal"], fontSize=9, leading=11)

        safe_numero = escape(str(numero))
        safe_fecha = escape(fecha.isoformat())
        safe_nombre = escape(str(cliente.get("nombre", "")))
        safe_correo = escape(str(cliente.get("correo", "")))

        story = []
        story.append(Paragraph("EventPass 360", title))
        story.append(Paragraph("FACTURA ELECTRÓNICA ACADÉMICA", sub))
        story.append(Spacer(1, 6 * mm))
        story.append(Paragraph(f"<b>Número:</b> {safe_numero} &nbsp;&nbsp;&nbsp; <b>Fecha:</b> {safe_fecha}", styles["Normal"]))
        story.append(Paragraph(f"<b>Cliente:</b> {safe_nombre} &nbsp;&nbsp;&nbsp; <b>Correo:</b> {safe_correo}", styles["Normal"]))
        story.append(Spacer(1, 8 * mm))

        data = [["Descripción", "Cantidad", "Precio Unit.", "Subtotal"]]
        for it in items:
            data.append([
                Paragraph(escape(str(it.get("descripcion", ""))), cell_style),
                str(it.get("cantidad", "")),
                self._money(it.get("precio_unitario", 0)),
                self._money(it.get("subtotal", 0)),
            ])
        table = Table(data, colWidths=[78 * mm, 24 * mm, 32 * mm, 32 * mm], repeatRows=1)
        table.setStyle(TableStyle([
            ("BACKGROUND", (0, 0), (-1, 0), BRAND),
            ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
            ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE", (0, 0), (-1, -1), 9),
            ("TOPPADDING", (0, 0), (-1, -1), 5),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f4f1fb")]),
        ]))
        story.append(table)

        if codigos:
            story.append(Spacer(1, 6 * mm))
            story.append(Paragraph("<b>Entradas</b>", styles["Normal"]))
            story.append(Spacer(1, 2 * mm))
            cdata = [["Código", "Evento"]]
            for c in codigos:
                cdata.append([escape(str(c.get("codigo", ""))), escape(str(c.get("evento", "")))])
            ctable = Table(cdata, colWidths=[78 * mm, 88 * mm])
            ctable.setStyle(TableStyle([
                ("BACKGROUND", (0, 0), (-1, 0), ACCENT),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 3),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
            ]))
            story.append(ctable)

        story.append(Spacer(1, 8 * mm))

        tdata = [
            ["Subtotal", self._money(totales.get("subtotal", 0))],
            ["Descuento", self._money(totales.get("descuento", 0))],
            ["Base Imponible", self._money(totales.get("base_imponible", 0))],
            ["IVA (15%)", self._money(totales.get("iva", 0))],
            ["Total", self._money(totales.get("total", 0))],
        ]
        ttable = Table(tdata, colWidths=[130 * mm, 36 * mm], hAlign="RIGHT")
        ttable.setStyle(TableStyle([
            ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ("FONTNAME", (0, 4), (1, 4), "Helvetica-Bold"),
            ("BACKGROUND", (0, 4), (-1, 4), colors.HexColor("#ede9fe")),
            ("TEXTCOLOR", (0, 4), (-1, 4), BRAND),
            ("FONTSIZE", (0, 0), (-1, -1), 10),
            ("TOPPADDING", (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ]))
        story.append(ttable)
        story.append(Spacer(1, 12 * mm))
        story.append(Paragraph("Gracias por su compra. Documento emitido con fines académicos.", sub))

        doc.build(story, onFirstPage=self._draw_logo, onLaterPages=self._draw_logo)
        return buf.getvalue()

    def _draw_logo(self, canvas, doc):
        canvas.saveState()
        cx, cy = 25 * mm, A4[1] - 17 * mm
        canvas.setFillColor(BRAND)
        canvas.circle(cx, cy, 6 * mm, stroke=0, fill=1)
        canvas.setFillColor(colors.white)
        canvas.setFont("Helvetica-Bold", 9)
        canvas.drawCentredString(cx, cy - 3, "EP360")
        canvas.setFillColor(ACCENT)
        canvas.setFont("Helvetica-Bold", 11)
        canvas.drawString(35 * mm, A4[1] - 19 * mm, "EventPass 360")
        canvas.restoreState()

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
