import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'cart_controller.dart';
import 'catalogo_screen.dart';
import 'carrito_screen.dart';
import 'historial_screen.dart';
import 'perfil_screen.dart';

class ClienteHome extends StatefulWidget {
  const ClienteHome({super.key});
  @override
  State<ClienteHome> createState() => _ClienteHomeState();
}

class _ClienteHomeState extends State<ClienteHome> {
  int _index = 0;

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => CartController(),
      child: Scaffold(
        body: IndexedStack(
          index: _index,
          children: const [CatalogoScreen(), CarritoScreen(), HistorialScreen(), PerfilScreen()],
        ),
        bottomNavigationBar: NavigationBar(
          selectedIndex: _index,
          onDestinationSelected: (i) => setState(() => _index = i),
          destinations: const [
            NavigationDestination(icon: Icon(Icons.storefront), label: 'Catálogo'),
            NavigationDestination(icon: Icon(Icons.shopping_cart), label: 'Carrito'),
            NavigationDestination(icon: Icon(Icons.receipt_long), label: 'Historial'),
            NavigationDestination(icon: Icon(Icons.person), label: 'Perfil'),
          ],
        ),
      ),
    );
  }
}
