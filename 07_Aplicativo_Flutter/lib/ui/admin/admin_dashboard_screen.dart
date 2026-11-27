import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/app_dependencies.dart';
import '../../core/format.dart';
import '../../core/theme.dart';
import '../../domain/entities.dart';
import '../../domain/ui_state.dart';
import '../core/widgets/feedback_views.dart';
import '../core/widgets/status_badges.dart';

class AdminDashboardScreen extends StatefulWidget {
  const AdminDashboardScreen({super.key});

  @override
  State<AdminDashboardScreen> createState() => _AdminDashboardScreenState();
}

class _AdminDashboardScreenState extends State<AdminDashboardScreen> {
  UiState<Estadisticas> _state = const UiLoading();

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _state = const UiLoading());
    try {
      final stats = await context.read<AppDependencies>().compras.estadisticas();
      if (mounted) setState(() => _state = UiSuccess(stats));
    } catch (e) {
      if (mounted) setState(() => _state = UiError(e.toString()));
    }
  }

  @override
  Widget build(BuildContext context) {
    return switch (_state) {
      UiLoading() => const LoadingView(label: 'Cargando estadísticas...'),
      UiError(:final message) => ErrorStateView(
          message: message,
          onRetry: _load,
        ),
      UiSuccess(:final data) => RefreshIndicator(
          onRefresh: _load,
          child: SingleChildScrollView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.all(20),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Expanded(
                      child: Text(
                        'Resumen de ventas',
                        style: Theme.of(context).textTheme.titleLarge?.copyWith(
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
                const SizedBox(height: 16),
                Wrap(
                  spacing: 16,
                  runSpacing: 16,
                  children: [
                    _KpiCard(
                      label: 'Total compras',
                      value: '${data.totalCompras}',
                      icon: Icons.receipt_long,
                    ),
                    _KpiCard(
                      label: 'Ingresos confirmados',
                      value: money(data.ingresosTotales),
                      icon: Icons.payments_outlined,
                    ),
                    _KpiCard(
                      label: 'Entradas vendidas',
                      value: '${data.entradasVendidas}',
                      icon: Icons.confirmation_number_outlined,
                    ),
                  ],
                ),
                const SizedBox(height: 24),
                Text(
                  'Compras por estado',
                  style: Theme.of(context).textTheme.titleMedium?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: brand,
                      ),
                ),
                const SizedBox(height: 10),
                if (data.porEstado.isEmpty)
                  const Card(
                    child: Padding(
                      padding: EdgeInsets.all(16),
                      child: Text('Aún no existen compras registradas.'),
                    ),
                  )
                else
                  Card(
                    child: Column(
                      children: [
                        for (final entry in data.porEstado.entries)
                          ListTile(
                            leading: StatusBadge(entry.key),
                            title: Text('Estado ${entry.key}'),
                            trailing: Text(
                              '${entry.value}',
                              style: Theme.of(context)
                                  .textTheme
                                  .titleMedium
                                  ?.copyWith(fontWeight: FontWeight.bold),
                            ),
                          ),
                      ],
                    ),
                  ),
              ],
            ),
          ),
        ),
    };
  }
}

class _KpiCard extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;

  const _KpiCard({
    required this.label,
    required this.value,
    required this.icon,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      child: SizedBox(
        width: 220,
        child: Padding(
          padding: const EdgeInsets.all(18),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              CircleAvatar(
                backgroundColor: surfaceTint,
                child: Icon(icon, color: accent),
              ),
              const SizedBox(height: 12),
              Text(
                value,
                style: Theme.of(context).textTheme.headlineSmall?.copyWith(
                      fontWeight: FontWeight.bold,
                      color: brand,
                    ),
              ),
              const SizedBox(height: 4),
              Text(
                label,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: Colors.grey.shade700,
                    ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}
