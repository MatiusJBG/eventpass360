import 'package:flutter/foundation.dart';

class CartItem {
  final int tipoEntradaId;
  final String tipo;
  final String evento;
  final double precio;
  int cantidad;
  CartItem({required this.tipoEntradaId, required this.tipo, required this.evento, required this.precio, this.cantidad = 1});
}

class CartController extends ChangeNotifier {
  final List<CartItem> items = [];

  int get totalCantidad => items.fold(0, (a, b) => a + b.cantidad);
  double get subtotal => items.fold(0.0, (a, b) => a + b.precio * b.cantidad);

  CartItem? find(int tipoEntradaId) {
    for (final i in items) {
      if (i.tipoEntradaId == tipoEntradaId) return i;
    }
    return null;
  }

  void add(CartItem item) {
    final existing = find(item.tipoEntradaId);
    if (existing != null) {
      existing.cantidad += item.cantidad;
    } else {
      items.add(item);
    }
    notifyListeners();
  }

  void increment(int tipoEntradaId) {
    find(tipoEntradaId)?.cantidad++;
    notifyListeners();
  }

  void decrement(int tipoEntradaId) {
    final item = find(tipoEntradaId);
    if (item == null) return;
    item.cantidad--;
    if (item.cantidad <= 0) items.remove(item);
    notifyListeners();
  }

  void clear() {
    items.clear();
    notifyListeners();
  }

  List<Map<String, dynamic>> toPayload() =>
      items.map((i) => {'tipo_entrada_id': i.tipoEntradaId, 'cantidad': i.cantidad}).toList();
}
