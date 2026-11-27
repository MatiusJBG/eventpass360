import 'package:flutter/material.dart';
import 'package:flutter/services.dart';

import '../../../core/file_downloader.dart';
import '../../../domain/repositories.dart';
import 'feedback_views.dart';

class XmlViewerDialog extends StatelessWidget {
  final String numeroFactura;
  final String xmlContent;

  const XmlViewerDialog({
    super.key,
    required this.numeroFactura,
    required this.xmlContent,
  });

  @override
  Widget build(BuildContext context) {
    final safeName =
        numeroFactura.isNotEmpty ? '$numeroFactura.xml' : 'factura.xml';
    return AlertDialog(
      title: Row(
        children: [
          const Icon(Icons.code, size: 22),
          const SizedBox(width: 8),
          Expanded(
            child: Text(
              numeroFactura.isNotEmpty
                  ? 'XML · $numeroFactura'
                  : 'Comprobante XML',
              overflow: TextOverflow.ellipsis,
            ),
          ),
        ],
      ),
      content: SizedBox(
        width: 560,
        height: 360,
        child: Container(
          padding: const EdgeInsets.all(12),
          decoration: BoxDecoration(
            color: const Color(0xFF0F172A),
            borderRadius: BorderRadius.circular(8),
          ),
          child: SingleChildScrollView(
            child: SelectableText(
              xmlContent,
              style: const TextStyle(
                fontFamily: 'monospace',
                fontSize: 12,
                color: Color(0xFFE2E8F0),
              ),
            ),
          ),
        ),
      ),
      actions: [
        TextButton.icon(
          icon: const Icon(Icons.copy, size: 18),
          label: const Text('Copiar'),
          onPressed: () async {
            await Clipboard.setData(ClipboardData(text: xmlContent));
            if (context.mounted) {
              showAppSnack(context, 'XML copiado al portapapeles');
            }
          },
        ),
        FilledButton.icon(
          icon: const Icon(Icons.download, size: 18),
          label: const Text('Descargar XML'),
          onPressed: () async {
            await downloadTextFile(
              content: xmlContent,
              filename: safeName,
              mimeType: 'application/xml;charset=utf-8',
            );
            if (context.mounted) {
              showAppSnack(context, 'Descarga iniciada: $safeName');
            }
          },
        ),
        TextButton(
          onPressed: () => Navigator.of(context).pop(),
          child: const Text('Cerrar'),
        ),
      ],
    );
  }
}

class InvoiceActionRow extends StatefulWidget {
  final int facturaId;
  final String facturaNumero;
  final FacturacionRepositoryPort facturacionRepo;

  const InvoiceActionRow({
    super.key,
    required this.facturaId,
    required this.facturaNumero,
    required this.facturacionRepo,
  });

  @override
  State<InvoiceActionRow> createState() => _InvoiceActionRowState();
}

class _InvoiceActionRowState extends State<InvoiceActionRow> {
  String? _busyAction;

  String get _baseFilename => widget.facturaNumero.isNotEmpty
      ? widget.facturaNumero
      : 'factura_${widget.facturaId}';

  Future<void> _verXml() async {
    setState(() => _busyAction = 'ver_xml');
    try {
      final xml = await widget.facturacionRepo.obtenerXml(widget.facturaId);
      if (!mounted) return;
      await showDialog<void>(
        context: context,
        builder: (_) => XmlViewerDialog(
          numeroFactura: widget.facturaNumero,
          xmlContent: xml,
        ),
      );
    } catch (e) {
      if (mounted) showAppSnack(context, e.toString(), error: true);
    } finally {
      if (mounted) setState(() => _busyAction = null);
    }
  }

  Future<void> _descargarXml() async {
    setState(() => _busyAction = 'desc_xml');
    try {
      final xml = await widget.facturacionRepo.obtenerXml(widget.facturaId);
      final filename = '$_baseFilename.xml';
      await downloadTextFile(
        content: xml,
        filename: filename,
        mimeType: 'application/xml;charset=utf-8',
      );
      if (mounted) {
        showAppSnack(context, 'XML descargado: $filename');
      }
    } catch (e) {
      if (mounted) showAppSnack(context, e.toString(), error: true);
    } finally {
      if (mounted) setState(() => _busyAction = null);
    }
  }

  Future<void> _descargarPdf() async {
    setState(() => _busyAction = 'desc_pdf');
    try {
      final bytes =
          await widget.facturacionRepo.obtenerPdfBytes(widget.facturaId);
      final filename = '$_baseFilename.pdf';
      await downloadFileBytes(
        bytes: bytes,
        filename: filename,
        mimeType: 'application/pdf',
      );
      if (mounted) {
        showAppSnack(context, 'PDF descargado: $filename');
      }
    } catch (e) {
      if (mounted) showAppSnack(context, e.toString(), error: true);
    } finally {
      if (mounted) setState(() => _busyAction = null);
    }
  }

  Widget _actionButton({
    required String actionKey,
    required IconData icon,
    required String label,
    required VoidCallback onPressed,
  }) {
    final isLoading = _busyAction == actionKey;
    return OutlinedButton.icon(
      onPressed: _busyAction != null ? null : onPressed,
      icon: isLoading
          ? const SizedBox(
              width: 14,
              height: 14,
              child: CircularProgressIndicator(strokeWidth: 2),
            )
          : Icon(icon, size: 16),
      label: Text(label),
    );
  }

  @override
  Widget build(BuildContext context) {
    return Wrap(
      spacing: 8,
      runSpacing: 8,
      children: [
        _actionButton(
          actionKey: 'ver_xml',
          icon: Icons.visibility_outlined,
          label: 'Ver XML',
          onPressed: _verXml,
        ),
        _actionButton(
          actionKey: 'desc_xml',
          icon: Icons.code,
          label: 'Descargar XML',
          onPressed: _descargarXml,
        ),
        _actionButton(
          actionKey: 'desc_pdf',
          icon: Icons.picture_as_pdf_outlined,
          label: 'Descargar PDF',
          onPressed: _descargarPdf,
        ),
      ],
    );
  }
}
