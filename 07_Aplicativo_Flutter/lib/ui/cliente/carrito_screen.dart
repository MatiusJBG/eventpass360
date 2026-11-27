import 'dart:math';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/api_client.dart';
import '../../core/format.dart';
import '../../core/session.dart';
import '../../data/repositories.dart';
import '../widgets.dart';
import 'cart_controller.dart';

class CarritoScreen extends StatefulWidget {
  const CarritoScreen({super.key});
  @override
  State<CarritoScreen> createState() => _CarritoScreenState();
}

class _CarritoScreenState extends State<CarritoScreen> {
  bool _loading = false;
  Map<String, dynamic>? _resumen;

  Future<void> _previsualizar() async {
    final cart = context.read<CartController>();
    if (cart.items.isEmpty) { showSnack(context, 'El carrito está vacío'); return; }
    setState(() => _loading = true);
    try {
      final session = context.read<Session>();
      final repo = ComprasRepository(ApiClient(session));
      final r = await repo.previsualizar(cart.toPayload());
      if (mounted) setState(() => _resumen = r as Map<String, dynamic>);
    } catch (e) {
      if (mounted) showSnack(context, e.toString(), error: true);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  Future<void> _comprar() async {
    final cart = context.read<CartController>();
    final session = context.read<Session>();
    final repo = ComprasRepository(ApiClient(session));
    setState(() => _loading = true);
    try {
      final sid = DateTime.now().microsecondsSinceEpoch.toString() + '-' + Random().nextInt(99999).toString();
      final r = await repo.comprar(sid, cart.toPayload());
      final mapa = r as Map<String, dynamic>;
      cart.clear();
      if (mounted) {
        setState(() => _resumen = null);
        _showResultado(mapa);
      }
    } catch (e) {
      if (mounted) showSnack(context, e.toString(), error: true);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _showResultado(Map<String, dynamic> mapa) {
    final factura = mapa['factura'] as Map<String, dynamic>?;
    showDialog(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Compra confirmada'),
        content: Column(
          mainAxisSize: MainAxisSize.min,
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text('Estado: ' + (mapa['estado']?.toString() ?? '')),
            Text('Total: ' + money((mapa['total'] as num?)?.toDouble() ?? 0)),
            if (factura != null) Text('Factura: ' + (factura['numero']?.toString() ?? '')),
          ],
        ),
        actions: [TextButton(onPressed: () => Navigator.of(context).pop(), child: const Text('Aceptar'))],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final cart = context.watch<CartController>();
    return Scaffold(
      appBar: AppBar(title: const Text('Carrito')),
      body: cart.items.isEmpty
          ? const EmptyView('Tu carrito está vacío')
          : Column(
              children: [
                Expanded(
                  child: ListView.builder(
                    padding: const EdgeInsets.all(12),
                    itemCount: cart.items.length,
                    itemBuilder: (context, i) {
                      final item = cart.items[i];
                      return Card(
                        child: ListTile(
                          title: Text(item.evento + ' - ' + item.tipo),
                          subtitle: Text(money(item.precio) + ' c/u'),
                          trailing: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              IconButton(onPressed: () => context.read<CartController>().decrement(item.tipoEntradaId), icon: const Icon(Icons.remove_circle_outline)),
                              Text(item.cantidad.toString()),
                              IconButton(onPressed: () => context.read<CartController>().increment(item.tipoEntradaId), icon: const Icon(Icons.add_circle_outline)),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ),
                Padding(
                  padding: const EdgeInsets.all(12),
                  child: Column(
                    children: [
                      Row(
                        mainAxisAlignment: MainAxisAlignment.spaceBetween,
                        children: [
                          Text('Subtotal', style: Theme.of(context).textTheme.titleMedium),
                          Text(money(cart.subtotal), style: Theme.of(context).textTheme.titleMedium),
                        ],
                      ),
                      if (_resumen != null) _Resumen(resumen: _resumen!),
                      const SizedBox(height: 12),
                      SizedBox(
                        width: double.infinity,
                        child: _resumen == null
                            ? ElevatedButton(onPressed: _loading ? null : _previsualizar, child: Text(_loading ? 'Calculando...' : 'Ver resumen'))
                            : ElevatedButton(onPressed: _loading ? null : _comprar, child: Text(_loading ? 'Procesando...' : 'Confirmar compra')),
                      ),
                    ],
                  ),
                ),
              ],
            ),
    );
  }
}

class _Resumen extends StatelessWidget {
  final Map<String, dynamic> resumen;
  const _Resumen({required this.resumen});
  @override
  Widget build(BuildContext context) {
    double d(String k) => (resumen[k] as num?)?.toDouble() ?? 0;
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          children: [
            _row(context, 'Descuento (' + d('porcentaje_descuento').toString() + '%)', '-' + money(d('descuento'))),
            _row(context, 'Base imponible', money(d('base_imponible'))),
            _row(context, 'IVA (15%)', money(d('iva'))),
            const Divider(),
            _row(context, 'Total', money(d('total')), bold: true),
          ],
        ),
      ),
    );
  }

  Widget _row(BuildContext context, String label, String value, {bool bold = false}) {
    final style = bold ? const TextStyle(fontWeight: FontWeight.bold, fontSize: 16) : null;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(mainAxisAlignment: MainAxisAlignment.spaceBetween, children: [Text(label, style: style), Text(value, style: style)]),
    );
  }
}
