import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'carrito_screen.dart';
import 'cart_controller.dart';
import 'catalogo_screen.dart';
import 'historial_screen.dart';
import 'perfil_screen.dart';

class ClienteHome extends StatefulWidget {
  const ClienteHome({super.key});

  @override
  State<ClienteHome> createState() => _ClienteHomeState();
}

class _ClienteHomeState extends State<ClienteHome> {
  final _historialKey = GlobalKey<HistorialScreenState>();
  int _index = 0;

  void _selectTab(int nextIndex) {
    setState(() => _index = nextIndex);
    if (nextIndex == 2) {
      _historialKey.currentState?.reload();
    }
  }

  @override
  Widget build(BuildContext context) {
    final cartCount = context.watch<CartController>().totalCantidad;

    return Scaffold(
      body: IndexedStack(
        index: _index,
        children: [
          const CatalogoScreen(),
          CarritoScreen(
            onPurchaseCompleted: () => _historialKey.currentState?.reload(),
          ),
          HistorialScreen(key: _historialKey),
          const PerfilScreen(),
        ],
      ),
      bottomNavigationBar: NavigationBar(
        selectedIndex: _index,
        onDestinationSelected: _selectTab,
        destinations: [
          const NavigationDestination(
            icon: Icon(Icons.storefront_outlined),
            selectedIcon: Icon(Icons.storefront),
            label: 'Catálogo',
          ),
          NavigationDestination(
            icon: Badge.count(
              count: cartCount,
              isLabelVisible: cartCount > 0,
              child: const Icon(Icons.shopping_cart_outlined),
            ),
            selectedIcon: Badge.count(
              count: cartCount,
              isLabelVisible: cartCount > 0,
              child: const Icon(Icons.shopping_cart),
            ),
            label: 'Carrito',
          ),
          const NavigationDestination(
            icon: Icon(Icons.receipt_long_outlined),
            selectedIcon: Icon(Icons.receipt_long),
            label: 'Historial y Facturas',
          ),
          const NavigationDestination(
            icon: Icon(Icons.person_outline),
            selectedIcon: Icon(Icons.person),
            label: 'Perfil',
          ),
        ],
      ),
    );
  }
}
