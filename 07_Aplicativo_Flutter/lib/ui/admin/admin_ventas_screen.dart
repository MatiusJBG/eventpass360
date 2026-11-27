import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/app_dependencies.dart';
import '../../core/format.dart';
import '../../core/theme.dart';
import '../../domain/entities.dart';
import '../../domain/ui_state.dart';
import '../core/widgets/feedback_views.dart';
import '../core/widgets/invoice_actions.dart';
import '../core/widgets/status_badges.dart';

class AdminVentasScreen extends StatefulWidget {
  const AdminVentasScreen({super.key});

  @override
  State<AdminVentasScreen> createState() => _AdminVentasScreenState();
}

class _AdminVentasScreenState extends State<AdminVentasScreen> {
  UiState<List<Compra>> _state = const UiLoading();
  Map<int, Factura> _facturasPorCompra = const {};
  int? _anulandoId;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _state = const UiLoading());
    final deps = context.read<AppDependencies>();
    try {
      final results = await Future.wait<dynamic>([
        deps.compras.listarCompras(),
        deps.facturacion.listarFacturas(),
      ]);
      if (!mounted) return;
      final compras = results[0] as List<Compra>;
      final facturas = results[1] as List<Factura>;
      setState(() {
        _facturasPorCompra = {for (final f in facturas) f.compraId: f};
        _state = UiSuccess(compras);
      });
    } catch (e) {
      if (mounted) setState(() => _state = UiError(e.toString()));
    }
  }

  Future<void> _anular(Compra compra) async {
    final confirmed = await ConfirmDialog.show(
      context,
      title: 'Anular compra #${compra.id}',
      message:
          'Se anulará la compra de ${compra.usuarioNombre.isNotEmpty ? compra.usuarioNombre : 'Usuario #${compra.usuarioId}'}, se anulará su factura y se restaurará el stock. ¿Confirmas la anulación?',
      confirmLabel: 'Anular compra',
    );
    if (!confirmed || !mounted) return;

    setState(() => _anulandoId = compra.id);
    try {
      await context.read<AppDependencies>().compras.anularCompra(compra.id);
      if (!mounted) return;
      showAppSnack(context, 'Compra #${compra.id} anulada y stock restaurado');
      await _load();
    } catch (e) {
      if (mounted) showAppSnack(context, e.toString(), error: true);
    } finally {
      if (mounted) setState(() => _anulandoId = null);
    }
  }

  @override
  Widget build(BuildContext context) {
    final facturacionRepo = context.read<AppDependencies>().facturacion;

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 12, 16, 4),
          child: Row(
            children: [
              Expanded(
                child: Text(
                  'Ventas y Facturas emitidas',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: brand,
                      ),
                ),
              ),
              OutlinedButton.icon(
                onPressed: _load,
                icon: const Icon(Icons.refresh, size: 18),
                label: const Text('Actualizar'),
              ),
            ],
          ),
        ),
        Expanded(
          child: switch (_state) {
            UiLoading() => const LoadingView(label: 'Cargando ventas...'),
            UiError(:final message) => ErrorStateView(
                message: message,
                onRetry: _load,
              ),
            UiSuccess(:final data) when data.isEmpty => const EmptyStateView(
                message: 'No hay ventas registradas todavía.',
                icon: Icons.point_of_sale_outlined,
              ),
            UiSuccess(:final data) => RefreshIndicator(
                onRefresh: _load,
                child: ListView.builder(
                  padding: const EdgeInsets.all(12),
                  itemCount: data.length,
                  itemBuilder: (context, index) {
                    final compra = data[index];
                    final factura = _facturasPorCompra[compra.id];
                    final facturaId = factura?.id ?? compra.facturaId;
                    final facturaNumero =
                        factura?.numero ?? compra.facturaNumero ?? '';
                    final facturaEstado =
                        factura?.estado ?? compra.facturaEstado;
                    final anulando = _anulandoId == compra.id;

                    final clienteLabel = compra.usuarioNombre.isNotEmpty
                        ? '${compra.usuarioNombre} (${compra.usuarioCorreo})'
                        : 'Usuario #${compra.usuarioId}';

                    return Card(
                      margin: const EdgeInsets.only(bottom: 12),
                      child: ExpansionTile(
                        leading: const Icon(Icons.point_of_sale, color: accent),
                        title: Wrap(
                          spacing: 8,
                          runSpacing: 4,
                          crossAxisAlignment: WrapCrossAlignment.center,
                          children: [
                            Text(
                              'Compra #${compra.id} · ${money(compra.total)}',
                              style:
                                  const TextStyle(fontWeight: FontWeight.bold),
                            ),
                            StatusBadge(compra.estado),
                          ],
                        ),
                        subtitle: Padding(
                          padding: const EdgeInsets.only(top: 4),
                          child: Wrap(
                            spacing: 12,
                            runSpacing: 4,
                            children: [
                              Text(clienteLabel),
                              Text(fecha(compra.fecha)),
                              if (facturaNumero.isNotEmpty)
                                Text(
                                  'Factura: $facturaNumero',
                                  style: const TextStyle(
                                    fontWeight: FontWeight.w600,
                                    color: brand,
                                  ),
                                ),
                            ],
                          ),
                        ),
                        childrenPadding:
                            const EdgeInsets.fromLTRB(16, 0, 16, 16),
                        children: [
                          const Divider(),
                          for (final d in compra.detalles)
                            Padding(
                              padding: const EdgeInsets.symmetric(vertical: 4),
                              child: Row(
                                children: [
                                  Expanded(
                                    child: Text(
                                      '${d.evento} · ${d.tipo} (${d.cantidad} × ${money(d.precioUnitario)})',
                                    ),
                                  ),
                                  Text(
                                    money(d.subtotal),
                                    style: const TextStyle(
                                        fontWeight: FontWeight.w600),
                                  ),
                                ],
                              ),
                            ),
                          const Divider(),
                          Wrap(
                            spacing: 16,
                            runSpacing: 4,
                            children: [
                              Text('Subtotal: ${money(compra.subtotal)}'),
                              Text('Descuento: -${money(compra.descuento)}'),
                              Text('Base: ${money(compra.baseImponible)}'),
                              Text('IVA: ${money(compra.iva)}'),
                              Text(
                                'Total: ${money(compra.total)}',
                                style: const TextStyle(
                                    fontWeight: FontWeight.bold),
                              ),
                            ],
                          ),
                          const SizedBox(height: 12),
                          Wrap(
                            spacing: 10,
                            runSpacing: 8,
                            crossAxisAlignment: WrapCrossAlignment.center,
                            children: [
                              if (facturaId != null) ...[
                                if (facturaEstado != null &&
                                    facturaEstado.isNotEmpty)
                                  StatusBadge(facturaEstado),
                                InvoiceActionRow(
                                  facturaId: facturaId,
                                  facturaNumero: facturaNumero,
                                  facturacionRepo: facturacionRepo,
                                ),
                              ],
                              if (compra.estado == 'CONFIRMADA')
                                LoadingButton(
                                  loading: anulando,
                                  destructive: true,
                                  icon: Icons.block,
                                  label: 'Anular',
                                  loadingLabel: 'Anulando...',
                                  onPressed: () => _anular(compra),
                                ),
                            ],
                          ),
                        ],
                      ),
                    );
                  },
                ),
              ),
          },
        ),
      ],
    );
  }
}
