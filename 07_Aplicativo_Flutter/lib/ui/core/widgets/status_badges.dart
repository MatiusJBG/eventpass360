import 'package:flutter/material.dart';

class StatusBadge extends StatelessWidget {
  final String status;

  const StatusBadge(this.status, {super.key});

  factory StatusBadge.fromBool(bool activo, {Key? key}) =>
      StatusBadge(activo ? 'Activo' : 'Inactivo', key: key);

  @override
  Widget build(BuildContext context) {
    final normalized = status.trim().toUpperCase();
    final (Color color, IconData icon) = switch (normalized) {
      'CONFIRMADA' || 'EMITIDA' || 'ACTIVO' => (
          const Color(0xFF15803D),
          Icons.check_circle_outline,
        ),
      'ANULADA' || 'INACTIVO' => (
          const Color(0xFFB91C1C),
          Icons.cancel_outlined,
        ),
      'FALLIDA' => (
          const Color(0xFFC2410C),
          Icons.warning_amber_rounded,
        ),
      'PENDIENTE' => (
          const Color(0xFFB45309),
          Icons.schedule,
        ),
      _ => (
          Colors.blueGrey,
          Icons.info_outline,
        ),
    };

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withValues(alpha: 0.35)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 14, color: color),
          const SizedBox(width: 4),
          Text(
            status,
            style: TextStyle(
              color: color,
              fontWeight: FontWeight.w600,
              fontSize: 12,
            ),
          ),
        ],
      ),
    );
  }
}

class StockBadge extends StatelessWidget {
  final int stock;

  const StockBadge({super.key, required this.stock});

  @override
  Widget build(BuildContext context) {
    final agotado = stock <= 0;
    final bajo = !agotado && stock <= 5;
    final color = agotado
        ? const Color(0xFFB91C1C)
        : bajo
            ? const Color(0xFFB45309)
            : const Color(0xFF15803D);
    final label = agotado ? 'Agotado' : '$stock disponibles';

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(20),
        border: Border.all(color: color.withValues(alpha: 0.35)),
      ),
      child: Text(
        label,
        style: TextStyle(
          color: color,
          fontWeight: FontWeight.w600,
          fontSize: 12,
        ),
      ),
    );
  }
}
