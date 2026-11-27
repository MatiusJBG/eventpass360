import 'package:flutter/foundation.dart';

class Session extends ChangeNotifier {
  String? token;
  Map<String, dynamic>? user;

  bool get isAuthenticated => token != null && token!.isNotEmpty;
  bool get isAdmin => user != null && user!['rol'] == 'ADMIN';

  int get userId {
    final u = user;
    if (u == null) return 0;
    final id = u['id'];
    if (id is int) return id;
    return int.tryParse(id.toString()) ?? 0;
  }

  String get nombre {
    final u = user;
    if (u == null) return '';
    return u['nombre']?.toString() ?? '';
  }

  String get correo {
    final u = user;
    if (u == null) return '';
    return u['correo']?.toString() ?? '';
  }

  void setAuth(String t, Map<String, dynamic> u) {
    token = t;
    user = u;
    notifyListeners();
  }

  void clear() {
    token = null;
    user = null;
    notifyListeners();
  }
}
