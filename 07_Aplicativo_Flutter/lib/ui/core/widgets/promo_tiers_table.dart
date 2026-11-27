import 'package:flutter/material.dart';

import '../../../core/format.dart';
import '../../../core/theme.dart';
import '../../../domain/entities.dart';

class PromoTiersTable extends StatelessWidget {
  final List<Promocion> promociones;
  final int currentQuantity;

  const PromoTiersTable({
    super.key,
    required this.promociones,
    this.currentQuantity = 0,
  });

  String _rangoLabel(Promocion p) {
    if (p.cantidadMax == null) return '${p.cantidadMin}+ entradas';
    if (p.cantidadMin == p.cantidadMax) return '${p.cantidadMin} entrada';
    return '${p.cantidadMin}–${p.cantidadMax} entradas';
  }

  @override
  Widget build(BuildContext context) {
    final activas = promociones.where((p) => p.estado).toList()
      ..sort((a, b) => a.cantidadMin.compareTo(b.cantidadMin));

    if (activas.isEmpty) return const SizedBox.shrink();

    return Card(
      color: surfaceTint,
      child: Padding(
        padding: const EdgeInsets.all(12),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                const Icon(Icons.local_offer_outlined, size: 18, color: accent),
                const SizedBox(width: 8),
                Text(
                  'Descuentos por volumen',
                  style: Theme.of(context).textTheme.titleSmall?.copyWith(
                        fontWeight: FontWeight.bold,
                        color: brand,
                      ),
                ),
              ],
            ),
            const SizedBox(height: 8),
            Wrap(
              spacing: 8,
              runSpacing: 8,
              children: activas.map((p) {
                final active =
                    currentQuantity > 0 && p.aplicaPara(currentQuantity);
                return Container(
                  padding:
                      const EdgeInsets.symmetric(horizontal: 10, vertical: 6),
                  decoration: BoxDecoration(
                    color: active ? accent : Colors.white,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(
                      color: active ? accent : Colors.grey.shade300,
                    ),
                  ),
                  child: Text(
                    '${_rangoLabel(p)}: ${porcentaje(p.porcentaje)}',
                    style: TextStyle(
                      fontSize: 12,
                      fontWeight: active ? FontWeight.bold : FontWeight.w500,
                      color: active ? Colors.white : brand,
                    ),
                  ),
                );
              }).toList(),
            ),
          ],
        ),
      ),
    );
  }
}
