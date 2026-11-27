import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/api_client.dart';
import '../../core/format.dart';
import '../../core/session.dart';
import '../../core/theme.dart';
import '../../data/repositories.dart';
import '../../domain/entities.dart';
import '../widgets.dart';

class HistorialScreen extends StatefulWidget {
  const HistorialScreen({super.key});
  @override
  State<HistorialScreen> createState() => _HistorialScreenState();
}

class _HistorialScreenState extends State<HistorialScreen> {
  List<Compra>? _compras;
  List<Factura>? _facturas;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final session = context.read<Session>();
      final repo = ComprasRepository(ApiClient(session));
      final frepo = FacturacionRepository(ApiClient(session));
      final compras = await repo.listarCompras();
      final facturas = await frepo.listarFacturas();
      if (mounted) setState(() { _compras = compras; _facturas = facturas; });
    } catch (e) {
      if (mounted) setState(() => _error = e.toString());
    }
  }

  Factura? _facturaDe(int compraId) {
    for (final x in _facturas ?? []) {
      if (x.compraId == compraId) return x;
    }
    return null;
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Historial y Facturas')),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_error != null) return ErrorView(_error!, onRetry: _load);
    if (_compras == null) return const LoadingView();
    if (_compras!.isEmpty) return const EmptyView('Aún no tienes compras');
    return RefreshIndicator(
      onRefresh: _load,
      child: ListView.builder(
        padding: const EdgeInsets.all(12),
        itemCount: _compras!.length,
        itemBuilder: (context, i) {
          final c = _compras![i];
          final factura = _facturaDe(c.id);
          return Card(
            child: ExpansionTile(
              leading: const Icon(Icons.receipt_long, color: accent),
              title: Text('Compra #' + c.id.toString() + ' · ' + money(c.total)),
              subtitle: Row(children: [EstadoBadge(c.estado), const SizedBox(width: 8), Text(fecha(c.fecha))]),
              children: [
                for (final d in c.detalles)
                  ListTile(
                    dense: true,
                    title: Text(d.evento + ' - ' + d.tipo),
                    subtitle: Text(d.cantidad.toString() + ' × ' + money(d.precioUnitario)),
                    trailing: Text(money(d.subtotal)),
                  ),
                if (factura != null)
                  Padding(
                    padding: const EdgeInsets.all(8),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.end,
                      children: [
                        Text('Factura ' + factura.numero, style: const TextStyle(fontWeight: FontWeight.bold)),
                        const SizedBox(width: 8),
                        TextButton.icon(icon: const Icon(Icons.code), label: const Text('XML'), onPressed: () => _abrirUrl('http://localhost:5004/api/factura/' + factura.id.toString() + '/xml')),
                        TextButton.icon(icon: const Icon(Icons.picture_as_pdf), label: const Text('PDF'), onPressed: () => _abrirUrl('http://localhost:5004/api/factura/' + factura.id.toString() + '/pdf')),
                      ],
                    ),
                  ),
              ],
            ),
          );
        },
      ),
    );
  }

  void _abrirUrl(String url) {
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Documento de factura'),
        content: SelectableText(url),
        actions: [TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text('Cerrar'))],
      ),
    );
  }
}
