import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/api_client.dart';
import '../../core/app_dependencies.dart';
import '../../core/format.dart';
import '../../core/theme.dart';
import '../../domain/entities.dart';
import '../../domain/ui_state.dart';
import '../core/widgets/feedback_views.dart';
import '../core/widgets/invoice_actions.dart';
import '../core/widgets/status_badges.dart';

class HistorialScreen extends StatefulWidget {
  const HistorialScreen({super.key});

  @override
  State<HistorialScreen> createState() => HistorialScreenState();
}

class HistorialScreenState extends State<HistorialScreen> {
  UiState<List<Compra>> _state = const UiLoading();
  Map<int, Factura> _facturasPorCompra = const {};
  Map<int, List<Entrada>> _entradasPorCompra = const {};
  int? _anulandoId;

  @override
  void initState() {
    super.initState();
    reload();
  }

  Future<void> reload() async {
    if (!mounted) return;
    setState(() => _state = const UiLoading());
    final deps = context.read<AppDependencies>();
    try {
      final results = await Future.wait<dynamic>([
        deps.compras.listarCompras(),
        deps.facturacion.listarFacturas(),
        deps.entradas.listarEntradas(),
      ]);
      if (!mounted) return;
      final compras = results[0] as List<Compra>;
      final facturas = results[1] as List<Factura>;
      final entradas = results[2] as List<Entrada>;
      setState(() {
        _facturasPorCompra = {for (final f in facturas) f.compraId: f};
        _entradasPorCompra = <int, List<Entrada>>{};
        for (final e in entradas) {
          (_entradasPorCompra[e.compraId] ??= []).add(e);
        }
        _state = UiSuccess(compras);
      });
    } catch (e) {
      if (mounted) setState(() => _state = UiError(e.toString()));
    }
  }

  Future<void> _anularCompra(Compra compra) async {
    final confirmed = await ConfirmDialog.show(
      context,
      title: 'Anular compra #${compra.id}',
      message:
          'Se anulará la compra y su factura electrónica, y se restaurará el stock de las entradas. ¿Deseas continuar?',
      confirmLabel: 'Anular compra',
    );
    if (!confirmed || !mounted) return;

    setState(() => _anulandoId = compra.id);
    try {
      await context.read<AppDependencies>().compras.anularCompra(
            compra.id,
            rowVersion: compra.rowVersion,
          );
      if (!mounted) return;
      showAppSnack(context, 'Compra #${compra.id} anulada y stock restaurado');
      await reload();
    } on ApiException catch (e) {
      if (!mounted) return;
      showAppSnack(context, e.toString(), error: true);
      if (e.statusCode == 409) {
        await reload();
      }
    } catch (e) {
      if (mounted) showAppSnack(context, e.toString(), error: true);
    } finally {
      if (mounted) setState(() => _anulandoId = null);
    }
  }

  @override
  Widget build(BuildContext context) {
    final facturacionRepo = context.read<AppDependencies>().facturacion;

    return Scaffold(
      appBar: AppBar(
        title: const Text('Historial y Facturas'),
        actions: [
          IconButton(
            tooltip: 'Actualizar historial',
            icon: const Icon(Icons.refresh),
            onPressed: reload,
          ),
        ],
      ),
      body: switch (_state) {
        UiLoading() => const LoadingView(label: 'Cargando historial...'),
        UiError(:final message) => ErrorStateView(
            message: message,
            onRetry: reload,
          ),
        UiSuccess(:final data) when data.isEmpty => const EmptyStateView(
            message: 'Aún no has realizado compras.',
            icon: Icons.receipt_long_outlined,
          ),
        UiSuccess(:final data) => RefreshIndicator(
            onRefresh: reload,
            child: ListView.builder(
              padding: const EdgeInsets.all(12),
              itemCount: data.length,
              itemBuilder: (context, index) {
                final compra = data[index];
                final factura = _facturasPorCompra[compra.id];
                final facturaId = factura?.id ?? compra.facturaId;
                final facturaNumero =
                    factura?.numero ?? compra.facturaNumero ?? '';
                final facturaEstado = factura?.estado ?? compra.facturaEstado;
                final anulando = _anulandoId == compra.id;

                return Card(
                  margin: const EdgeInsets.only(bottom: 12),
                  child: ExpansionTile(
                    leading: const Icon(Icons.receipt_long, color: accent),
                    title: Wrap(
                      spacing: 8,
                      runSpacing: 4,
                      crossAxisAlignment: WrapCrossAlignment.center,
                      children: [
                        Text(
                          'Compra #${compra.id} · ${money(compra.total)}',
                          style: const TextStyle(fontWeight: FontWeight.bold),
                        ),
                        StatusBadge(compra.estado),
                      ],
                    ),
                    subtitle: Padding(
                      padding: const EdgeInsets.only(top: 4),
                      child: Wrap(
                        spacing: 10,
                        runSpacing: 4,
                        children: [
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
                    childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
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
                      if ((_entradasPorCompra[compra.id] ?? const []).isNotEmpty) ...[
                        const Divider(),
                        Padding(
                          padding: const EdgeInsets.symmetric(vertical: 4),
                          child: Text(
                            'Entradas',
                            style: const TextStyle(fontWeight: FontWeight.bold, color: brand),
                          ),
                        ),
                        for (final ent in _entradasPorCompra[compra.id]!)
                          Padding(
                            padding: const EdgeInsets.symmetric(vertical: 2),
                            child: Row(
                              children: [
                                Expanded(child: Text('${ent.codigo} · ${ent.evento}')),
                                StatusBadge(ent.estado),
                              ],
                            ),
                          ),
                      ],
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
                            style: const TextStyle(fontWeight: FontWeight.bold),
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
                              label: 'Anular compra',
                              loadingLabel: 'Anulando...',
                              onPressed: () => _anularCompra(compra),
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
    );
  }
}
