import 'package:eventpass360/core/api_client.dart';
import 'package:eventpass360/core/app_config.dart';
import 'package:eventpass360/domain/entities.dart';

class UsuariosRepository {
  final ApiClient client;
  UsuariosRepository(this.client);

  Future<Map<String, dynamic>> login(String correo, String password) async {
    return await client.post(AppConfig.apiUsuarios + '/api/login', {'correo': correo, 'password': password});
  }

  Future<dynamic> registro(String nombre, String correo, String password) async {
    return await client.post(AppConfig.apiUsuarios + '/api/registro', {'nombre': nombre, 'correo': correo, 'password': password});
  }

  Future<List<Usuario>> listarUsuarios([String? q]) async {
    final url = q == null ? AppConfig.apiUsuarios + '/api/usuarios' : AppConfig.apiUsuarios + '/api/usuarios?q=' + Uri.encodeComponent(q);
    final data = await client.get(url);
    return ((data as List) ?? []).map((e) => Usuario.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<dynamic> crearUsuario(Map<String, dynamic> body) => client.post(AppConfig.apiUsuarios + '/api/usuarios', body);
  Future<dynamic> actualizarUsuario(int id, Map<String, dynamic> body) => client.put(AppConfig.apiUsuarios + '/api/usuarios/' + id.toString(), body);
  Future<dynamic> eliminarUsuario(int id) => client.delete(AppConfig.apiUsuarios + '/api/usuarios/' + id.toString());

  Future<List<Rol>> listarRoles() async {
    final data = await client.get(AppConfig.apiUsuarios + '/api/roles');
    return ((data as List) ?? []).map((e) => Rol.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<dynamic> crearRol(String nombre) => client.post(AppConfig.apiUsuarios + '/api/roles', {'nombre': nombre});
  Future<dynamic> actualizarRol(int id, Map<String, dynamic> body) => client.put(AppConfig.apiUsuarios + '/api/roles/' + id.toString(), body);
  Future<dynamic> eliminarRol(int id) => client.delete(AppConfig.apiUsuarios + '/api/roles/' + id.toString());
}

class EventosRepository {
  final ApiClient client;
  EventosRepository(this.client);

  Future<List<Categoria>> listarCategorias() async {
    final data = await client.get(AppConfig.apiEventos + '/api/categorias');
    return ((data as List) ?? []).map((e) => Categoria.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<dynamic> crearCategoria(Map<String, dynamic> body) => client.post(AppConfig.apiEventos + '/api/categorias', body);
  Future<dynamic> actualizarCategoria(int id, Map<String, dynamic> body) => client.put(AppConfig.apiEventos + '/api/categorias/' + id.toString(), body);
  Future<dynamic> eliminarCategoria(int id) => client.delete(AppConfig.apiEventos + '/api/categorias/' + id.toString());

  Future<List<Evento>> listarEventos({String? q, int? categoriaId}) async {
    var url = AppConfig.apiEventos + '/api/eventos';
    final params = <String>[];
    if (q != null && q.isNotEmpty) params.add('q=' + Uri.encodeComponent(q));
    if (categoriaId != null) params.add('categoria_id=' + categoriaId.toString());
    if (params.isNotEmpty) url += '?' + params.join('&');
    final data = await client.get(url);
    return ((data as List) ?? []).map((e) => Evento.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<List<TipoEntrada>> listarEntradas(int eventoId) async {
    final data = await client.get(AppConfig.apiEventos + '/api/eventos/' + eventoId.toString() + '/entradas');
    return ((data as List) ?? []).map((e) => TipoEntrada.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<dynamic> crearEvento(Map<String, dynamic> body) => client.post(AppConfig.apiEventos + '/api/eventos', body);
  Future<dynamic> actualizarEvento(int id, Map<String, dynamic> body) => client.put(AppConfig.apiEventos + '/api/eventos/' + id.toString(), body);
  Future<dynamic> eliminarEvento(int id) => client.delete(AppConfig.apiEventos + '/api/eventos/' + id.toString());

  Future<dynamic> crearTipoEntrada(Map<String, dynamic> body) => client.post(AppConfig.apiEventos + '/api/tipos-entrada', body);
  Future<dynamic> actualizarTipoEntrada(int id, Map<String, dynamic> body) => client.put(AppConfig.apiEventos + '/api/tipos-entrada/' + id.toString(), body);
  Future<dynamic> eliminarTipoEntrada(int id) => client.delete(AppConfig.apiEventos + '/api/tipos-entrada/' + id.toString());
}

class PromocionesRepository {
  final ApiClient client;
  PromocionesRepository(this.client);

  Future<List<Promocion>> listarPromociones() async {
    final data = await client.get(AppConfig.apiPromociones + '/api/promociones');
    return ((data as List) ?? []).map((e) => Promocion.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<dynamic> crearPromocion(Map<String, dynamic> body) => client.post(AppConfig.apiPromociones + '/api/promociones', body);
  Future<dynamic> actualizarPromocion(int id, Map<String, dynamic> body) => client.put(AppConfig.apiPromociones + '/api/promociones/' + id.toString(), body);
  Future<dynamic> eliminarPromocion(int id) => client.delete(AppConfig.apiPromociones + '/api/promociones/' + id.toString());
}

class ComprasRepository {
  final ApiClient client;
  ComprasRepository(this.client);

  Future<dynamic> previsualizar(List<Map<String, dynamic>> items) => client.post(AppConfig.apiCompras + '/api/compras/previsualizar', {'items': items});

  Future<dynamic> comprar(String solicitudId, List<Map<String, dynamic>> items) =>
      client.post(AppConfig.apiCompras + '/api/compras', {'solicitud_id': solicitudId, 'items': items});

  Future<List<Compra>> listarCompras() async {
    final data = await client.get(AppConfig.apiCompras + '/api/compras');
    return ((data as List) ?? []).map((e) => Compra.fromJson(e as Map<String, dynamic>)).toList();
  }

  Future<dynamic> estadisticas() => client.get(AppConfig.apiCompras + '/api/compras/estadisticas');

  Future<dynamic> anularCompra(int id) => client.patch(AppConfig.apiCompras + '/api/compras/' + id.toString() + '/anular');
}

class FacturacionRepository {
  final ApiClient client;
  FacturacionRepository(this.client);

  Future<List<Factura>> listarFacturas() async {
    final data = await client.get(AppConfig.apiFacturacion + '/api/factura');
    return ((data as List) ?? []).map((e) => Factura.fromJson(e as Map<String, dynamic>)).toList();
  }

  String urlXml(int facturaId) => AppConfig.apiFacturacion + '/api/factura/' + facturaId.toString() + '/xml';
  String urlPdf(int facturaId) => AppConfig.apiFacturacion + '/api/factura/' + facturaId.toString() + '/pdf';
}
