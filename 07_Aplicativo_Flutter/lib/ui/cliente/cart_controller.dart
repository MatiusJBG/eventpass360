import 'dart:math';

import 'package:flutter/foundation.dart';

class CartItem {
  final int tipoEntradaId;
  final String tipo;
  final String evento;
  final double precio;
  int stock;
  int cantidad;

  CartItem({
    required this.tipoEntradaId,
    required this.tipo,
    required this.evento,
    required this.precio,
    required this.stock,
    this.cantidad = 1,
  });
}

class CartController extends ChangeNotifier {
  final List<CartItem> _items = [];
  final Random _random = Random();
  String? _solicitudId;

  List<CartItem> get items => List.unmodifiable(_items);

  int get totalCantidad => _items.fold(0, (acc, item) => acc + item.cantidad);

  double get subtotal =>
      _items.fold(0.0, (acc, item) => acc + (item.precio * item.cantidad));

  String? get currentSolicitudId => _solicitudId;

  /// Deterministic signature used to detect cart mutations and invalidate previews.
  String get signature {
    final sorted = [..._items]
      ..sort((a, b) => a.tipoEntradaId.compareTo(b.tipoEntradaId));
    return sorted.map((i) => '${i.tipoEntradaId}:${i.cantidad}').join('|');
  }

  CartItem? find(int tipoEntradaId) {
    for (final item in _items) {
      if (item.tipoEntradaId == tipoEntradaId) return item;
    }
    return null;
  }

  int quantityOf(int tipoEntradaId) => find(tipoEntradaId)?.cantidad ?? 0;

  bool canAddMore(int tipoEntradaId, int stock) {
    if (stock <= 0) return false;
    return quantityOf(tipoEntradaId) < stock;
  }

  /// Returns a stable idempotency key for the current checkout attempt.
  /// It is only regenerated when cart items change or after [clear].
  String getOrCreateSolicitudId() {
    _solicitudId ??=
        'ep360-${DateTime.now().microsecondsSinceEpoch}-${_random.nextInt(999999).toString().padLeft(6, '0')}';
    return _solicitudId!;
  }

  /// Adds an item bounded strictly to [1..stock]. Returns true if quantity changed.
  bool add(CartItem item) {
    if (item.stock <= 0) return false;
    final desired = item.cantidad < 1 ? 1 : item.cantidad;
    final existing = find(item.tipoEntradaId);
    if (existing != null) {
      existing.stock = item.stock;
      if (existing.cantidad >= existing.stock) return false;
      existing.cantidad = min(existing.stock, existing.cantidad + desired);
    } else {
      _items.add(
        CartItem(
          tipoEntradaId: item.tipoEntradaId,
          tipo: item.tipo,
          evento: item.evento,
          precio: item.precio,
          stock: item.stock,
          cantidad: min(item.stock, desired),
        ),
      );
    }
    _solicitudId = null;
    notifyListeners();
    return true;
  }

  /// Increments quantity if strictly below available [CartItem.stock].
  bool increment(int tipoEntradaId) {
    final item = find(tipoEntradaId);
    if (item == null || item.cantidad >= item.stock) return false;
    item.cantidad++;
    _solicitudId = null;
    notifyListeners();
    return true;
  }

  /// Decrements quantity; removes item when quantity drops below 1.
  void decrement(int tipoEntradaId) {
    final item = find(tipoEntradaId);
    if (item == null) return;
    item.cantidad--;
    if (item.cantidad <= 0) {
      _items.remove(item);
    }
    _solicitudId = null;
    notifyListeners();
  }

  void remove(int tipoEntradaId) {
    final before = _items.length;
    _items.removeWhere((i) => i.tipoEntradaId == tipoEntradaId);
    if (_items.length != before) {
      _solicitudId = null;
      notifyListeners();
    }
  }

  void clear() {
    if (_items.isEmpty && _solicitudId == null) return;
    _items.clear();
    _solicitudId = null;
    notifyListeners();
  }

  List<Map<String, dynamic>> toPayload() => _items
      .map((i) => {'tipo_entrada_id': i.tipoEntradaId, 'cantidad': i.cantidad})
      .toList();
}
