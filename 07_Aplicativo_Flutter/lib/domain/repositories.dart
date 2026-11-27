/// Domain repository ports (Dependency Inversion Principle).
library;

import 'dart:typed_data';

import 'entities.dart';

class AuthResult {
  final String token;
  final Usuario usuario;

  const AuthResult({required this.token, required this.usuario});
}

abstract interface class UsuariosRepositoryPort {
  Future<AuthResult> login(String correo, String password);
  Future<Usuario> registro(String nombre, String correo, String password);
  Future<Usuario> getPerfil();
  Future<Usuario> actualizarPerfil({
    String? nombre,
    String? correo,
    String? password,
  });

  Future<List<Usuario>> listarUsuarios([String? q]);
  Future<Usuario> crearUsuario(Map<String, dynamic> body);
  Future<Usuario> actualizarUsuario(int id, Map<String, dynamic> body);
  Future<void> eliminarUsuario(int id);

  Future<List<Rol>> listarRoles();
  Future<Rol> crearRol(String nombre);
  Future<Rol> actualizarRol(int id, Map<String, dynamic> body);
  Future<void> eliminarRol(int id);
}

abstract interface class EventosRepositoryPort {
  Future<List<Categoria>> listarCategorias();
  Future<Categoria> crearCategoria(Map<String, dynamic> body);
  Future<Categoria> actualizarCategoria(int id, Map<String, dynamic> body);
  Future<void> eliminarCategoria(int id);

  Future<List<Evento>> listarEventos({
    String? q,
    int? categoriaId,
    bool incluirInactivos = false,
  });
  Future<Evento> crearEvento(Map<String, dynamic> body);
  Future<Evento> actualizarEvento(int id, Map<String, dynamic> body);
  Future<void> eliminarEvento(int id);

  Future<List<TipoEntrada>> listarEntradas(int eventoId);
  Future<List<TipoEntrada>> listarTiposEntrada({int? eventoId});
  Future<TipoEntrada> crearTipoEntrada(Map<String, dynamic> body);
  Future<TipoEntrada> actualizarTipoEntrada(int id, Map<String, dynamic> body);
  Future<void> eliminarTipoEntrada(int id);
}

abstract interface class PromocionesRepositoryPort {
  Future<List<Promocion>> listarPromociones({bool soloActivas = false});
  Future<Promocion> crearPromocion(Map<String, dynamic> body);
  Future<Promocion> actualizarPromocion(int id, Map<String, dynamic> body);
  Future<void> eliminarPromocion(int id);
}

abstract interface class FacturacionRepositoryPort {
  Future<List<Factura>> listarFacturas({int? compraId});
  Future<String> obtenerXml(int facturaId);
  Future<Uint8List> obtenerPdfBytes(int facturaId);
  String urlXml(int facturaId);
  String urlPdf(int facturaId);
}

abstract interface class ComprasRepositoryPort {
  Future<ResumenCompra> previsualizar(List<Map<String, dynamic>> items);
  Future<Compra> comprar(String solicitudId, List<Map<String, dynamic>> items);
  Future<List<Compra>> listarCompras();
  Future<Estadisticas> estadisticas();
  Future<Compra> anularCompra(int id);
}
