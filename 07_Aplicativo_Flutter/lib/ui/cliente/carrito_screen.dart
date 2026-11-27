import 'dart:async';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/app_dependencies.dart';
import '../../core/format.dart';
import '../../core/theme.dart';
import '../../domain/entities.dart';
import '../core/widgets/feedback_views.dart';
import '../core/widgets/invoice_actions.dart';
import '../core/widgets/promo_tiers_table.dart';
import '../core/widgets/status_badges.dart';
import 'cart_controller.dart';

class CarritoScreen extends StatefulWidget {
  final VoidCallback? onPurchaseCompleted;

  const CarritoScreen({super.key, this.onPurchaseCompleted});

  @override
  State<CarritoScreen> createState() => _CarritoScreenState();
}

class _CarritoScreenState extends State<CarritoScreen> {
  List<Promocion> _promociones = const [];
  ResumenCompra? _resumen;
  String? _previewError;
  bool _previewLoading = false;
  bool _buying = false;

  String _lastSignature = '';
  int _previewSeq = 0;
  Timer? _previewDebounce;
  CartController? _cart;

  @override
  void initState() {
    super.initState();
    _loadPromociones();
  }

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final cart = context.read<CartController>();
    if (_cart != cart) {
      _cart?.removeListener(_onCartChanged);
      _cart = cart;
      _cart!.addListener(_onCartChanged);
      _onCartChanged();
    }
  }

  @override
  void dispose() {
    _previewDebounce?.cancel();
    _cart?.removeListener(_onCartChanged);
    super.dispose();
  }

  Future<void> _loadPromociones() async {
    try {
      final promos = await context
          .read<AppDependencies>()
          .promociones
          .listarPromociones(soloActivas: true);
      if (mounted) setState(() => _promociones = promos);
    } catch (_) {
      // Non-blocking: checkout still works via server preview.
    }
  }

  void _onCartChanged() {
    final cart = _cart;
    if (cart == null) return;
    final sig = cart.signature;
    if (sig == _lastSignature) return;
    _lastSignature = sig;
    _previewDebounce?.cancel();

    if (cart.items.isEmpty) {
      _previewSeq++;
      if (mounted) {
        setState(() {
          _resumen = null;
          _previewError = null;
          _previewLoading = false;
        });
      }
      return;
    }

    // Immediately invalidate stale preview totals when quantities change.
    if (mounted) {
      setState(() {
        _resumen = null;
        _previewError = null;
        _previewLoading = true;
      });
    }
    _previewDebounce = Timer(
      const Duration(milliseconds: 220),
      _previsualizar,
    );
  }

  Future<void> _previsualizar() async {
    final cart = _cart;
    if (cart == null || cart.items.isEmpty) return;
    final seq = ++_previewSeq;
    final repo = context.read<AppDependencies>().compras;

    if (mounted) {
      setState(() {
        _previewLoading = true;
        _previewError = null;
      });
    }

    try {
      final resumen = await repo.previsualizar(cart.toPayload());
      if (!mounted || seq != _previewSeq) return;
      setState(() {
        _resumen = resumen;
        _previewLoading = false;
      });
    } catch (e) {
      if (!mounted || seq != _previewSeq) return;
      setState(() {
        _resumen = null;
        _previewError = e.toString();
        _previewLoading = false;
      });
    }
  }

  Future<void> _comprar() async {
    final cart = context.read<CartController>();
    if (cart.items.isEmpty) return;

    final deps = context.read<AppDependencies>();
    final solicitudId = cart.getOrCreateSolicitudId();

    setState(() => _buying = true);
    try {
      final compra = await deps.compras.comprar(solicitudId, cart.toPayload());
      cart.clear();
      widget.onPurchaseCompleted?.call();
      if (!mounted) return;
      setState(() {
        _resumen = null;
        _previewError = null;
      });
      await _showCompraConfirmadaDialog(compra);
    } catch (e) {
      if (mounted) showAppSnack(context, e.toString(), error: true);
    } finally {
      if (mounted) setState(() => _buying = false);
    }
  }

  Future<void> _showCompraConfirmadaDialog(Compra compra) {
    final facturacionRepo = context.read<AppDependencies>().facturacion;
    return showDialog<void>(
      context: context,
      builder: (_) => AlertDialog(
        title: Row(
          children: [
            const Icon(Icons.check_circle, color: Color(0xFF15803D)),
            const SizedBox(width: 8),
            const Expanded(child: Text('Compra confirmada')),
          ],
        ),
        content: SingleChildScrollView(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Wrap(
                spacing: 8,
                runSpacing: 6,
                crossAxisAlignment: WrapCrossAlignment.center,
                children: [
                  Text(
                    'Compra #${compra.id}',
                    style: const TextStyle(fontWeight: FontWeight.bold),
                  ),
                  StatusBadge(compra.estado),
                ],
              ),
              if (compra.facturaNumero != null &&
                  compra.facturaNumero!.isNotEmpty) ...[
                const SizedBox(height: 8),
                Text(
                  'Factura: ${compra.facturaNumero}',
                  style: const TextStyle(fontWeight: FontWeight.w600),
                ),
              ],
              const Divider(height: 20),
              _TotalRow('Subtotal', money(compra.subtotal)),
              _TotalRow('Descuento', '-${money(compra.descuento)}'),
              _TotalRow('Base imponible', money(compra.baseImponible)),
              _TotalRow('IVA (15%)', money(compra.iva)),
              const Divider(height: 16),
              _TotalRow('Total pagado', money(compra.total), bold: true),
              if (compra.facturaId != null) ...[
                const SizedBox(height: 16),
                const Text(
                  'Comprobante electrónico:',
                  style: TextStyle(fontWeight: FontWeight.w600),
                ),
                const SizedBox(height: 8),
                InvoiceActionRow(
                  facturaId: compra.facturaId!,
                  facturaNumero: compra.facturaNumero ?? 'FAC-${compra.facturaId}',
                  facturacionRepo: facturacionRepo,
                ),
              ],
            ],
          ),
        ),
        actions: [
          FilledButton(
            onPressed: () => Navigator.of(context).pop(),
            child: const Text('Aceptar'),
          ),
        ],
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final cart = context.watch<CartController>();

    return Scaffold(
      appBar: AppBar(
        title: const Text('Carrito de Compras'),
        actions: [
          if (cart.items.isNotEmpty)
            IconButton(
              tooltip: 'Vaciar carrito',
              icon: const Icon(Icons.delete_sweep_outlined),
              onPressed: _buying
                  ? null
                  : () async {
                      final ok = await ConfirmDialog.show(
                        context,
                        title: 'Vaciar carrito',
                        message:
                            '¿Deseas eliminar todas las entradas seleccionadas del carrito?',
                        confirmLabel: 'Vaciar',
                      );
                      if (ok && context.mounted) {
                        context.read<CartController>().clear();
                      }
                    },
            ),
        ],
      ),
      body: cart.items.isEmpty
          ? Column(
              children: [
                if (_promociones.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.fromLTRB(12, 12, 12, 0),
                    child: PromoTiersTable(
                      promociones: _promociones,
                      currentQuantity: 0,
                    ),
                  ),
                const Expanded(
                  child: EmptyStateView(
                    message:
                        'Tu carrito está vacío. Agrega entradas desde el catálogo.',
                    icon: Icons.shopping_cart_outlined,
                  ),
                ),
              ],
            )
          : Column(
              children: [
                Expanded(
                  child: ListView(
                    padding: const EdgeInsets.all(12),
                    children: [
                      if (_promociones.isNotEmpty) ...[
                        PromoTiersTable(
                          promociones: _promociones,
                          currentQuantity: cart.totalCantidad,
                        ),
                        const SizedBox(height: 10),
                      ],
                      for (final item in cart.items)
                        Card(
                          margin: const EdgeInsets.only(bottom: 10),
                          child: Padding(
                            padding: const EdgeInsets.all(12),
                            child: Row(
                              children: [
                                Expanded(
                                  child: Column(
                                    crossAxisAlignment:
                                        CrossAxisAlignment.start,
                                    children: [
                                      Text(
                                        '${item.evento} · ${item.tipo}',
                                        style: Theme.of(context)
                                            .textTheme
                                            .titleSmall
                                            ?.copyWith(
                                              fontWeight: FontWeight.bold,
                                              color: brand,
                                            ),
                                      ),
                                      const SizedBox(height: 4),
                                      Text(
                                        '${money(item.precio)} c/u · Máx. ${item.stock}',
                                        style: Theme.of(context)
                                            .textTheme
                                            .bodySmall,
                                      ),
                                    ],
                                  ),
                                ),
                                Row(
                                  mainAxisSize: MainAxisSize.min,
                                  children: [
                                    IconButton(
                                      tooltip: 'Disminuir cantidad',
                                      onPressed: _buying
                                          ? null
                                          : () => context
                                              .read<CartController>()
                                              .decrement(item.tipoEntradaId),
                                      icon: const Icon(
                                          Icons.remove_circle_outline),
                                    ),
                                    SizedBox(
                                      width: 28,
                                      child: Text(
                                        '${item.cantidad}',
                                        textAlign: TextAlign.center,
                                        style: const TextStyle(
                                          fontWeight: FontWeight.bold,
                                        ),
                                      ),
                                    ),
                                    IconButton(
                                      tooltip: item.cantidad >= item.stock
                                          ? 'Stock máximo alcanzado'
                                          : 'Aumentar cantidad',
                                      onPressed: _buying ||
                                              item.cantidad >= item.stock
                                          ? null
                                          : () => context
                                              .read<CartController>()
                                              .increment(item.tipoEntradaId),
                                      icon:
                                          const Icon(Icons.add_circle_outline),
                                    ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ),
                    ],
                  ),
                ),
                Material(
                  elevation: 4,
                  color: Colors.white,
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        if (_previewLoading)
                          const Padding(
                            padding: EdgeInsets.symmetric(vertical: 10),
                            child: Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                SizedBox(
                                  width: 18,
                                  height: 18,
                                  child: CircularProgressIndicator(
                                      strokeWidth: 2),
                                ),
                                SizedBox(width: 10),
                                Text('Calculando descuento e IVA en vivo...'),
                              ],
                            ),
                          )
                        else if (_previewError != null)
                          Padding(
                            padding: const EdgeInsets.only(bottom: 10),
                            child: Row(
                              children: [
                                const Icon(Icons.error_outline,
                                    color: Colors.red),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: Text(
                                    _previewError!,
                                    style: const TextStyle(color: Colors.red),
                                  ),
                                ),
                                TextButton(
                                  onPressed: _previsualizar,
                                  child: const Text('Reintentar'),
                                ),
                              ],
                            ),
                          )
                        else if (_resumen != null) ...[
                          _TotalRow(
                            'Subtotal (${_resumen!.cantidadTotal} entradas)',
                            money(_resumen!.subtotal),
                          ),
                          _TotalRow(
                            'Descuento (${porcentaje(_resumen!.porcentajeDescuento)})',
                            '-${money(_resumen!.descuento)}',
                          ),
                          _TotalRow(
                            'Base imponible',
                            money(_resumen!.baseImponible),
                          ),
                          _TotalRow('IVA (15%)', money(_resumen!.iva)),
                          const Divider(height: 16),
                          _TotalRow(
                            'Total a pagar',
                            money(_resumen!.total),
                            bold: true,
                          ),
                          const SizedBox(height: 12),
                        ] else ...[
                          _TotalRow(
                            'Subtotal estimado (${cart.totalCantidad})',
                            money(cart.subtotal),
                          ),
                          const SizedBox(height: 12),
                        ],
                        LoadingButton(
                          loading: _buying,
                          onPressed:
                              (!_previewLoading && _resumen != null)
                                  ? _comprar
                                  : null,
                          label: 'Confirmar compra',
                          loadingLabel: 'Procesando compra...',
                          icon: Icons.check_circle_outline,
                          expand: true,
                        ),
                      ],
                    ),
                  ),
                ),
              ],
            ),
    );
  }
}

class _TotalRow extends StatelessWidget {
  final String label;
  final String value;
  final bool bold;

  const _TotalRow(this.label, this.value, {this.bold = false});

  @override
  Widget build(BuildContext context) {
    final style = bold
        ? const TextStyle(fontWeight: FontWeight.bold, fontSize: 16, color: brand)
        : Theme.of(context).textTheme.bodyMedium;
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 2),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceBetween,
        children: [
          Text(label, style: style),
          Text(value, style: style),
        ],
      ),
    );
  }
}
