import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/session.dart';
import '../../core/theme.dart';
import '../cliente/cart_controller.dart';
import 'admin_catalogs.dart';
import 'admin_dashboard_screen.dart';
import 'admin_ventas_screen.dart';

class AdminHome extends StatefulWidget {
  const AdminHome({super.key});

  @override
  State<AdminHome> createState() => _AdminHomeState();
}

class _AdminHomeState extends State<AdminHome> {
  static const _titles = [
    'Dashboard · EventPass 360',
    'Catálogos CRUD · EventPass 360',
    'Ventas y Facturas · EventPass 360',
  ];

  int _blockIndex = 0;

  void _logout() {
    context.read<CartController>().clear();
    context.read<Session>().clear();
  }

  Widget _buildContent() {
    return IndexedStack(
      index: _blockIndex,
      children: const [
        AdminDashboardScreen(),
        AdminCatalogsHub(),
        AdminVentasScreen(),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final session = context.watch<Session>();

    return LayoutBuilder(
      builder: (context, constraints) {
        final isWide = constraints.maxWidth >= 700;

        return Scaffold(
          appBar: AppBar(
            title: Text(_titles[_blockIndex]),
            actions: [
              if (session.nombre.isNotEmpty)
                Center(
                  child: Padding(
                    padding: const EdgeInsets.symmetric(horizontal: 8),
                    child: Text(
                      session.nombre,
                      style: const TextStyle(fontSize: 13),
                    ),
                  ),
                ),
              TextButton.icon(
                style: TextButton.styleFrom(foregroundColor: Colors.white),
                onPressed: _logout,
                icon: const Icon(Icons.logout, size: 18),
                label: const Text('Cerrar sesión'),
              ),
              const SizedBox(width: 8),
            ],
          ),
          body: isWide
              ? Row(
                  children: [
                    SingleChildScrollView(
                      child: ConstrainedBox(
                        constraints: BoxConstraints(
                          minHeight: constraints.maxHeight - kToolbarHeight,
                        ),
                        child: IntrinsicHeight(
                          child: NavigationRail(
                            selectedIndex: _blockIndex,
                            onDestinationSelected: (i) =>
                                setState(() => _blockIndex = i),
                            labelType: NavigationRailLabelType.all,
                            leading: const Padding(
                              padding: EdgeInsets.symmetric(vertical: 12),
                              child: Icon(
                                Icons.confirmation_number,
                                color: accent,
                                size: 32,
                              ),
                            ),
                            trailing: Expanded(
                              child: Align(
                                alignment: Alignment.bottomCenter,
                                child: Padding(
                                  padding: const EdgeInsets.only(bottom: 16),
                                  child: IconButton(
                                    tooltip: 'Cerrar sesión',
                                    icon: const Icon(Icons.logout),
                                    onPressed: _logout,
                                  ),
                                ),
                              ),
                            ),
                            destinations: const [
                              NavigationRailDestination(
                                icon: Icon(Icons.dashboard_outlined),
                                selectedIcon: Icon(Icons.dashboard),
                                label: Text('Dashboard'),
                              ),
                              NavigationRailDestination(
                                icon: Icon(Icons.folder_copy_outlined),
                                selectedIcon: Icon(Icons.folder_copy),
                                label: Text('Catálogos'),
                              ),
                              NavigationRailDestination(
                                icon: Icon(Icons.point_of_sale_outlined),
                                selectedIcon: Icon(Icons.point_of_sale),
                                label: Text('Ventas'),
                              ),
                            ],
                          ),
                        ),
                      ),
                    ),
                    const VerticalDivider(width: 1),
                    Expanded(child: _buildContent()),
                  ],
                )
              : _buildContent(),
          bottomNavigationBar: isWide
              ? null
              : NavigationBar(
                  selectedIndex: _blockIndex,
                  onDestinationSelected: (i) => setState(() => _blockIndex = i),
                  destinations: const [
                    NavigationDestination(
                      icon: Icon(Icons.dashboard_outlined),
                      selectedIcon: Icon(Icons.dashboard),
                      label: 'Dashboard',
                    ),
                    NavigationDestination(
                      icon: Icon(Icons.folder_copy_outlined),
                      selectedIcon: Icon(Icons.folder_copy),
                      label: 'Catálogos CRUD',
                    ),
                    NavigationDestination(
                      icon: Icon(Icons.point_of_sale_outlined),
                      selectedIcon: Icon(Icons.point_of_sale),
                      label: 'Ventas y Facturas',
                    ),
                  ],
                ),
        );
      },
    );
  }
}
