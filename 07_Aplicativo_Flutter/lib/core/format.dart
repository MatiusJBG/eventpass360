import 'package:intl/intl.dart';

final _money = NumberFormat('#,##0.00', 'en_US');
final _date = DateFormat('yyyy-MM-dd HH:mm');

String money(num? value) => '\$${_money.format(value ?? 0)}';

String porcentaje(num? value) {
  final v = (value ?? 0).toDouble();
  if (v == v.truncateToDouble()) return '${v.toInt()}%';
  return '${v.toStringAsFixed(2)}%';
}

String fecha(String? iso) {
  if (iso == null || iso.isEmpty) return '';
  final dt = DateTime.tryParse(iso);
  return dt == null ? iso : _date.format(dt.toLocal());
}
