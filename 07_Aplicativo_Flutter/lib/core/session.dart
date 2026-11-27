import 'package:flutter/foundation.dart';

import '../domain/entities.dart';

class Session extends ChangeNotifier {
  String? _token;
  Usuario? _usuario;

  String? get token => _token;
  Usuario? get usuario => _usuario;

  bool get isAuthenticated => _token != null && _token!.isNotEmpty;
  bool get isAdmin => _usuario?.rol.toUpperCase() == 'ADMIN';

  int get userId => _usuario?.id ?? 0;
  String get nombre => _usuario?.nombre ?? '';
  String get correo => _usuario?.correo ?? '';
  String get rol => _usuario?.rol ?? '';

  void setAuth(String token, Usuario usuario) {
    _token = token;
    _usuario = usuario;
    notifyListeners();
  }

  void updateUser(Usuario usuario) {
    _usuario = usuario;
    notifyListeners();
  }

  void clear() {
    if (_token == null && _usuario == null) return;
    _token = null;
    _usuario = null;
    notifyListeners();
  }
}
