import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/session.dart';
import '../../core/theme.dart';
import 'admin_screens.dart';

class AdminHome extends StatefulWidget {
  const AdminHome({super.key});
  @override
  State<AdminHome> createState() => _AdminHomeState();
}

class _AdminHomeState extends State<AdminHome> {
  int _index = 0;

  @override
  Widget build(BuildContext context) {
    final session = context.read<Session>();
    final repos = AdminRepos(session);
    return Scaffold(
      body: Row(
        children: [
          NavigationRail(
            selectedIndex: _index,
            onDestinationSelected: (i) => setState(() => _index = i),
            labelType: NavigationRailLabelType.all,
            groupAlignment: -0.9,
            leading: const Padding(
              padding: EdgeInsets.symmetric(vertical: 12),
              child: Column(children: [Icon(Icons.confirmation_number, color: accent, size: 32)]),
            ),
            destinations: const [
              NavigationRailDestination(icon: Icon(Icons.dashboard_outlined), selectedIcon: Icon(Icons.dashboard), label: Text('Dashboard')),
              NavigationRailDestination(icon: Icon(Icons.people_outline), selectedIcon: Icon(Icons.people), label: Text('Usuarios')),
              NavigationRailDestination(icon: Icon(Icons.badge_outlined), selectedIcon: Icon(Icons.badge), label: Text('Roles')),
              NavigationRailDestination(icon: Icon(Icons.category_outlined), selectedIcon: Icon(Icons.category), label: Text('Categorías')),
              NavigationRailDestination(icon: Icon(Icons.event_outlined), selectedIcon: Icon(Icons.event), label: Text('Eventos')),
              NavigationRailDestination(icon: Icon(Icons.confirmation_num_outlined), selectedIcon: Icon(Icons.confirmation_num), label: Text('Entradas')),
              NavigationRailDestination(icon: Icon(Icons.percent_outlined), selectedIcon: Icon(Icons.percent), label: Text('Promociones')),
              NavigationRailDestination(icon: Icon(Icons.point_of_sale_outlined), selectedIcon: Icon(Icons.point_of_sale), label: Text('Ventas')),
            ],
          ),
          const VerticalDivider(width: 1),
          Expanded(
            child: IndexedStack(
              index: _index,
              children: [
                DashboardScreen(repos: repos),
                UsuariosCrud(repos: repos),
                RolesCrud(repos: repos),
                CategoriasCrud(repos: repos),
                EventosCrud(repos: repos),
                TiposEntradaCrud(repos: repos),
                PromocionesCrud(repos: repos),
                VentasScreen(repos: repos),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
