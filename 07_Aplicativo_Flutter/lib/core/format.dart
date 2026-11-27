import 'package:intl/intl.dart';

final _money = NumberFormat('#,##0.00', 'en_US');
final _date = DateFormat('yyyy-MM-dd HH:mm');

String money(num? v) => String.fromCharCode(36) + _money.format(v ?? 0);
String fecha(String? iso) {
  if (iso == null) return '';
  final dt = DateTime.tryParse(iso);
  return dt == null ? iso : _date.format(dt.toLocal());
}
