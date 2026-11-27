import 'package:flutter_test/flutter_test.dart';
import 'package:eventpass360/ui/cliente/cart_controller.dart';

void main() {
  test('CartController suma items y subtotal correctamente', () {
    final cart = CartController();
    cart.add(CartItem(tipoEntradaId: 1, tipo: 'General', evento: 'Rock Fest', precio: 25.0, cantidad: 3));
    expect(cart.totalCantidad, 3);
    expect(cart.subtotal, 75.0);
    cart.increment(1);
    expect(cart.totalCantidad, 4);
    expect(cart.subtotal, 100.0);
    cart.clear();
    expect(cart.items, isEmpty);
  });
}
