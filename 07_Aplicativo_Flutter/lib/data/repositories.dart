import 'dart:typed_data';

import '../core/api_client.dart';
import '../core/app_config.dart';
import '../domain/entities.dart';
import '../domain/repositories.dart';
import 'models.dart';

List<Map<String, dynamic>> _asMapList(dynamic data) {
  if (data is! List) return const [];
  return data.whereType<Map<String, dynamic>>().toList();
}

Map<String, dynamic> _asMap(dynamic data) {
  if (data is Map<String, dynamic>) return data;
  return const {};
}

class UsuariosRepository implements UsuariosRepositoryPort {
  final ApiClient client;
  const UsuariosRepository(this.client);

  @override
  Future<AuthResult> login(String correo, String password) async {
    final raw = await client.post(
      '${AppConfig.apiUsuarios}/api/login',
      {'correo': correo, 'password': password},
    );
    final map = _asMap(raw);
    final token = map['token']?.toString() ?? '';
    final usuario = UsuarioModel.fromJson(_asMap(map['usuario']));
    return AuthResult(token: token, usuario: usuario);
  }

  @override
  Future<Usuario> registro(String nombre, String correo, String password) async {
    final raw = await client.post(
      '${AppConfig.apiUsuarios}/api/registro',
      {'nombre': nombre, 'correo': correo, 'password': password},
    );
    return UsuarioModel.fromJson(_asMap(raw));
  }

  @override
  Future<Usuario> getPerfil() async {
    final raw = await client.get('${AppConfig.apiUsuarios}/api/perfil');
    return UsuarioModel.fromJson(_asMap(raw));
  }

  @override
  Future<Usuario> actualizarPerfil({
    String? nombre,
    String? correo,
    String? password,
    int? rowVersion,
  }) async {
    final body = <String, dynamic>{};
    if (nombre != null && nombre.isNotEmpty) body['nombre'] = nombre;
    if (correo != null && correo.isNotEmpty) body['correo'] = correo;
    if (password != null && password.isNotEmpty) body['password'] = password;
    if (rowVersion != null) body['row_version'] = rowVersion;
    final raw = await client.put('${AppConfig.apiUsuarios}/api/perfil', body);
    return UsuarioModel.fromJson(_asMap(raw));
  }

  @override
  Future<List<Usuario>> listarUsuarios([String? q]) async {
    final query = (q != null && q.trim().isNotEmpty)
        ? '?q=${Uri.encodeQueryComponent(q.trim())}'
        : '';
    final raw = await client.get('${AppConfig.apiUsuarios}/api/usuarios$query');
    return _asMapList(raw).map(UsuarioModel.fromJson).toList();
  }

  @override
  Future<Usuario> crearUsuario(Map<String, dynamic> body) async {
    final raw = await client.post('${AppConfig.apiUsuarios}/api/usuarios', body);
    return UsuarioModel.fromJson(_asMap(raw));
  }

  @override
  Future<Usuario> actualizarUsuario(int id, Map<String, dynamic> body) async {
    final raw =
        await client.put('${AppConfig.apiUsuarios}/api/usuarios/$id', body);
    return UsuarioModel.fromJson(_asMap(raw));
  }

  @override
  Future<void> eliminarUsuario(int id) async {
    await client.delete('${AppConfig.apiUsuarios}/api/usuarios/$id');
  }

  @override
  Future<List<Rol>> listarRoles() async {
    final raw = await client.get('${AppConfig.apiUsuarios}/api/roles');
    return _asMapList(raw).map(RolModel.fromJson).toList();
  }

  @override
  Future<Rol> crearRol(String nombre) async {
    final raw = await client.post(
      '${AppConfig.apiUsuarios}/api/roles',
      {'nombre': nombre},
    );
    return RolModel.fromJson(_asMap(raw));
  }

  @override
  Future<Rol> actualizarRol(int id, Map<String, dynamic> body) async {
    final raw = await client.put('${AppConfig.apiUsuarios}/api/roles/$id', body);
    return RolModel.fromJson(_asMap(raw));
  }

  @override
  Future<void> eliminarRol(int id) async {
    await client.delete('${AppConfig.apiUsuarios}/api/roles/$id');
  }
}

class EventosRepository implements EventosRepositoryPort {
  final ApiClient client;
  const EventosRepository(this.client);

  @override
  Future<List<Categoria>> listarCategorias() async {
    final raw = await client.get('${AppConfig.apiEventos}/api/categorias');
    return _asMapList(raw).map(CategoriaModel.fromJson).toList();
  }

  @override
  Future<Categoria> crearCategoria(Map<String, dynamic> body) async {
    final raw =
        await client.post('${AppConfig.apiEventos}/api/categorias', body);
    return CategoriaModel.fromJson(_asMap(raw));
  }

  @override
  Future<Categoria> actualizarCategoria(int id, Map<String, dynamic> body) async {
    final raw =
        await client.put('${AppConfig.apiEventos}/api/categorias/$id', body);
    return CategoriaModel.fromJson(_asMap(raw));
  }

  @override
  Future<void> eliminarCategoria(int id) async {
    await client.delete('${AppConfig.apiEventos}/api/categorias/$id');
  }

  @override
  Future<List<Evento>> listarEventos({
    String? q,
    int? categoriaId,
    bool incluirInactivos = false,
  }) async {
    final params = <String>[];
    if (q != null && q.trim().isNotEmpty) {
      params.add('q=${Uri.encodeQueryComponent(q.trim())}');
    }
    if (categoriaId != null) {
      params.add('categoria_id=$categoriaId');
    }
    if (incluirInactivos) {
      params.add('incluir_inactivos=true');
    }
    final query = params.isEmpty ? '' : '?${params.join('&')}';
    final raw = await client.get('${AppConfig.apiEventos}/api/eventos$query');
    return _asMapList(raw).map(EventoModel.fromJson).toList();
  }

  @override
  Future<Evento> crearEvento(Map<String, dynamic> body) async {
    final raw = await client.post('${AppConfig.apiEventos}/api/eventos', body);
    return EventoModel.fromJson(_asMap(raw));
  }

  @override
  Future<Evento> actualizarEvento(int id, Map<String, dynamic> body) async {
    final raw =
        await client.put('${AppConfig.apiEventos}/api/eventos/$id', body);
    return EventoModel.fromJson(_asMap(raw));
  }

  @override
  Future<void> eliminarEvento(int id) async {
    await client.delete('${AppConfig.apiEventos}/api/eventos/$id');
  }

  @override
  Future<List<TipoEntrada>> listarEntradas(int eventoId) async {
    final raw =
        await client.get('${AppConfig.apiEventos}/api/eventos/$eventoId/entradas');
    return _asMapList(raw).map(TipoEntradaModel.fromJson).toList();
  }

  @override
  Future<List<TipoEntrada>> listarTiposEntrada({int? eventoId}) async {
    final query = eventoId != null ? '?evento_id=$eventoId' : '';
    final raw =
        await client.get('${AppConfig.apiEventos}/api/tipos-entrada$query');
    return _asMapList(raw).map(TipoEntradaModel.fromJson).toList();
  }

  @override
  Future<TipoEntrada> crearTipoEntrada(Map<String, dynamic> body) async {
    final raw =
        await client.post('${AppConfig.apiEventos}/api/tipos-entrada', body);
    return TipoEntradaModel.fromJson(_asMap(raw));
  }

  @override
  Future<TipoEntrada> actualizarTipoEntrada(
    int id,
    Map<String, dynamic> body,
  ) async {
    final raw =
        await client.put('${AppConfig.apiEventos}/api/tipos-entrada/$id', body);
    return TipoEntradaModel.fromJson(_asMap(raw));
  }

  @override
  Future<void> eliminarTipoEntrada(int id) async {
    await client.delete('${AppConfig.apiEventos}/api/tipos-entrada/$id');
  }
}

class PromocionesRepository implements PromocionesRepositoryPort {
  final ApiClient client;
  const PromocionesRepository(this.client);

  @override
  Future<List<Promocion>> listarPromociones({bool soloActivas = false}) async {
    final query = soloActivas ? '?activas=true' : '';
    final raw =
        await client.get('${AppConfig.apiPromociones}/api/promociones$query');
    return _asMapList(raw).map(PromocionModel.fromJson).toList();
  }

  @override
  Future<Promocion> crearPromocion(Map<String, dynamic> body) async {
    final raw =
        await client.post('${AppConfig.apiPromociones}/api/promociones', body);
    return PromocionModel.fromJson(_asMap(raw));
  }

  @override
  Future<Promocion> actualizarPromocion(
    int id,
    Map<String, dynamic> body,
  ) async {
    final raw = await client.put(
      '${AppConfig.apiPromociones}/api/promociones/$id',
      body,
    );
    return PromocionModel.fromJson(_asMap(raw));
  }

  @override
  Future<void> eliminarPromocion(int id) async {
    await client.delete('${AppConfig.apiPromociones}/api/promociones/$id');
  }
}

class ComprasRepository implements ComprasRepositoryPort {
  final ApiClient client;
  const ComprasRepository(this.client);

  @override
  Future<ResumenCompra> previsualizar(List<Map<String, dynamic>> items) async {
    final raw = await client.post(
      '${AppConfig.apiCompras}/api/compras/previsualizar',
      {'items': items},
    );
    return ResumenCompraModel.fromJson(_asMap(raw));
  }

  @override
  Future<Compra> comprar(
    String solicitudId,
    List<Map<String, dynamic>> items,
  ) async {
    final raw = await client.post(
      '${AppConfig.apiCompras}/api/compras',
      {'solicitud_id': solicitudId, 'items': items},
    );
    return CompraModel.fromJson(_asMap(raw));
  }

  @override
  Future<List<Compra>> listarCompras() async {
    final raw = await client.get('${AppConfig.apiCompras}/api/compras');
    return _asMapList(raw).map(CompraModel.fromJson).toList();
  }

  @override
  Future<Estadisticas> estadisticas() async {
    final raw =
        await client.get('${AppConfig.apiCompras}/api/compras/estadisticas');
    return EstadisticasModel.fromJson(_asMap(raw));
  }

  @override
  Future<Compra> anularCompra(int id, {int? rowVersion}) async {
    final body = rowVersion != null ? {'row_version': rowVersion} : null;
    final raw = await client.patch(
      '${AppConfig.apiCompras}/api/compras/$id/anular',
      body,
    );
    return CompraModel.fromJson(_asMap(raw));
  }
}

class FacturacionRepository implements FacturacionRepositoryPort {
  final ApiClient client;
  const FacturacionRepository(this.client);

  @override
  Future<List<Factura>> listarFacturas({int? compraId}) async {
    final query = compraId != null ? '?compra_id=$compraId' : '';
    final raw =
        await client.get('${AppConfig.apiFacturacion}/api/factura$query');
    return _asMapList(raw).map(FacturaModel.fromJson).toList();
  }

  @override
  Future<String> obtenerXml(int facturaId) => client.getText(urlXml(facturaId));

  @override
  Future<Uint8List> obtenerPdfBytes(int facturaId) =>
      client.getBytes(urlPdf(facturaId));

  @override
  String urlXml(int facturaId) =>
      '${AppConfig.apiFacturacion}/api/factura/$facturaId/xml';

  @override
  String urlPdf(int facturaId) =>
      '${AppConfig.apiFacturacion}/api/factura/$facturaId/pdf';
}

class EntradasRepository implements EntradasRepositoryPort {
  final ApiClient client;
  const EntradasRepository(this.client);

  @override
  Future<List<Entrada>> listarEntradas({int? compraId, int? usuarioId}) async {
    final params = <String>[];
    if (compraId != null) params.add('compra_id=$compraId');
    if (usuarioId != null) params.add('usuario_id=$usuarioId');
    final query = params.isEmpty ? '' : '?${params.join('&')}';
    final raw = await client.get('${AppConfig.apiEntradas}/api/entradas$query');
    return _asMapList(raw).map(EntradaModel.fromJson).toList();
  }
}
