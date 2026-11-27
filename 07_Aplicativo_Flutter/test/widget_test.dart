import 'dart:typed_data';

import 'package:eventpass360/core/api_client.dart';
import 'package:eventpass360/core/app_dependencies.dart';
import 'package:eventpass360/core/session.dart';
import 'package:eventpass360/domain/entities.dart';
import 'package:eventpass360/domain/repositories.dart';
import 'package:eventpass360/ui/auth/auth_screen.dart';
import 'package:eventpass360/ui/cliente/carrito_screen.dart';
import 'package:eventpass360/ui/cliente/cart_controller.dart';
import 'package:eventpass360/ui/core/widgets/promo_tiers_table.dart';
import 'package:eventpass360/ui/core/widgets/status_badges.dart';
import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:provider/provider.dart';

class _FakePromocionesRepo implements PromocionesRepositoryPort {
  final List<Promocion> promos;
  const _FakePromocionesRepo(this.promos);

  @override
  Future<List<Promocion>> listarPromociones({bool soloActivas = false}) async =>
      promos;

  @override
  Future<Promocion> crearPromocion(Map<String, dynamic> body) =>
      throw UnimplementedError();

  @override
  Future<Promocion> actualizarPromocion(int id, Map<String, dynamic> body) =>
      throw UnimplementedError();

  @override
  Future<void> eliminarPromocion(int id) => throw UnimplementedError();
}

class _FakeComprasRepo implements ComprasRepositoryPort {
  @override
  Future<ResumenCompra> previsualizar(List<Map<String, dynamic>> items) async {
    final qty =
        items.fold<int>(0, (acc, e) => acc + (e['cantidad'] as int? ?? 0));
    final sub = qty * 25.0;
    return ResumenCompra(
      cantidadTotal: qty,
      subtotal: sub,
      porcentajeDescuento: qty >= 3 ? 5.0 : 0.0,
      descuento: qty >= 3 ? sub * 0.05 : 0.0,
      baseImponible: qty >= 3 ? sub * 0.95 : sub,
      iva: (qty >= 3 ? sub * 0.95 : sub) * 0.15,
      total: (qty >= 3 ? sub * 0.95 : sub) * 1.15,
    );
  }

  @override
  Future<Compra> comprar(String solicitudId, List<Map<String, dynamic>> items) =>
      throw UnimplementedError();

  @override
  Future<List<Compra>> listarCompras() async => const [];

  @override
  Future<Estadisticas> estadisticas() => throw UnimplementedError();

  @override
  Future<Compra> anularCompra(int id) => throw UnimplementedError();
}

class _FakeUsuariosRepo implements UsuariosRepositoryPort {
  @override
  Future<AuthResult> login(String correo, String password) =>
      throw UnimplementedError();
  @override
  Future<Usuario> registro(String nombre, String correo, String password) =>
      throw UnimplementedError();
  @override
  Future<Usuario> getPerfil() => throw UnimplementedError();
  @override
  Future<Usuario> actualizarPerfil({
    String? nombre,
    String? correo,
    String? password,
  }) =>
      throw UnimplementedError();
  @override
  Future<List<Usuario>> listarUsuarios([String? q]) async => const [];
  @override
  Future<Usuario> crearUsuario(Map<String, dynamic> body) =>
      throw UnimplementedError();
  @override
  Future<Usuario> actualizarUsuario(int id, Map<String, dynamic> body) =>
      throw UnimplementedError();
  @override
  Future<void> eliminarUsuario(int id) => throw UnimplementedError();
  @override
  Future<List<Rol>> listarRoles() async => const [];
  @override
  Future<Rol> crearRol(String nombre) => throw UnimplementedError();
  @override
  Future<Rol> actualizarRol(int id, Map<String, dynamic> body) =>
      throw UnimplementedError();
  @override
  Future<void> eliminarRol(int id) => throw UnimplementedError();
}

class _FakeEventosRepo implements EventosRepositoryPort {
  @override
  Future<List<Categoria>> listarCategorias() async => const [];
  @override
  Future<Categoria> crearCategoria(Map<String, dynamic> body) =>
      throw UnimplementedError();
  @override
  Future<Categoria> actualizarCategoria(int id, Map<String, dynamic> body) =>
      throw UnimplementedError();
  @override
  Future<void> eliminarCategoria(int id) => throw UnimplementedError();
  @override
  Future<List<Evento>> listarEventos({
    String? q,
    int? categoriaId,
    bool incluirInactivos = false,
  }) async =>
      const [];
  @override
  Future<Evento> crearEvento(Map<String, dynamic> body) =>
      throw UnimplementedError();
  @override
  Future<Evento> actualizarEvento(int id, Map<String, dynamic> body) =>
      throw UnimplementedError();
  @override
  Future<void> eliminarEvento(int id) => throw UnimplementedError();
  @override
  Future<List<TipoEntrada>> listarEntradas(int eventoId) async => const [];
  @override
  Future<List<TipoEntrada>> listarTiposEntrada({int? eventoId}) async =>
      const [];
  @override
  Future<TipoEntrada> crearTipoEntrada(Map<String, dynamic> body) =>
      throw UnimplementedError();
  @override
  Future<TipoEntrada> actualizarTipoEntrada(int id, Map<String, dynamic> body) =>
      throw UnimplementedError();
  @override
  Future<void> eliminarTipoEntrada(int id) => throw UnimplementedError();
}

class _FakeFacturacionRepo implements FacturacionRepositoryPort {
  @override
  Future<List<Factura>> listarFacturas({int? compraId}) async => const [];
  @override
  Future<String> obtenerXml(int facturaId) async => '<factura />';
  @override
  Future<Uint8List> obtenerPdfBytes(int facturaId) async => Uint8List(0);
  @override
  String urlXml(int facturaId) => '';
  @override
  String urlPdf(int facturaId) => '';
}

AppDependencies _buildFakeDeps(Session session) {
  return AppDependencies.custom(
    apiClient: ApiClient(session),
    usuarios: _FakeUsuariosRepo(),
    eventos: _FakeEventosRepo(),
    promociones: const _FakePromocionesRepo([
      Promocion(id: 1, cantidadMin: 1, cantidadMax: 2, porcentaje: 0, estado: true),
      Promocion(id: 2, cantidadMin: 3, cantidadMax: 4, porcentaje: 5, estado: true),
      Promocion(id: 3, cantidadMin: 5, cantidadMax: 9, porcentaje: 10, estado: true),
      Promocion(id: 4, cantidadMin: 10, cantidadMax: null, porcentaje: 15, estado: true),
    ]),
    facturacion: _FakeFacturacionRepo(),
    compras: _FakeComprasRepo(),
  );
}

void main() {
  testWidgets('AuthScreen valida correo y contraseña antes de enviar', (tester) async {
    final session = Session();
    final deps = _buildFakeDeps(session);

    await tester.pumpWidget(
      MultiProvider(
        providers: [
          ChangeNotifierProvider<Session>.value(value: session),
          Provider<AppDependencies>.value(value: deps),
        ],
        child: const MaterialApp(home: AuthScreen()),
      ),
    );

    await tester.tap(find.text('Ingresar'));
    await tester.pump();

    expect(find.text('Ingresa tu correo electrónico'), findsOneWidget);
    expect(find.text('Ingresa tu contraseña'), findsOneWidget);

    await tester.enterText(find.byType(TextFormField).first, 'correo-invalido');
    await tester.enterText(find.byType(TextFormField).last, '123');
    await tester.tap(find.text('Ingresar'));
    await tester.pump();

    expect(find.text('Ingresa un correo válido'), findsOneWidget);
    expect(
      find.text('La contraseña debe tener al menos 6 caracteres'),
      findsOneWidget,
    );
  });

  testWidgets('StockBadge y StatusBadge renderizan etiquetas correctas', (tester) async {
    await tester.pumpWidget(
      MaterialApp(
        home: Scaffold(
          body: Column(
            children: [
              const StockBadge(stock: 97),
              const StockBadge(stock: 0),
              const StatusBadge('CONFIRMADA'),
              const StatusBadge('ANULADA'),
              StatusBadge.fromBool(true),
              StatusBadge.fromBool(false),
            ],
          ),
        ),
      ),
    );

    expect(find.text('97 disponibles'), findsOneWidget);
    expect(find.text('Agotado'), findsOneWidget);
    expect(find.text('CONFIRMADA'), findsOneWidget);
    expect(find.text('ANULADA'), findsOneWidget);
    expect(find.text('Activo'), findsOneWidget);
    expect(find.text('Inactivo'), findsOneWidget);
  });

  testWidgets('PromoTiersTable muestra rangos activos correctamente', (tester) async {
    await tester.pumpWidget(
      const MaterialApp(
        home: Scaffold(
          body: PromoTiersTable(
            currentQuantity: 5,
            promociones: [
              Promocion(id: 1, cantidadMin: 1, cantidadMax: 2, porcentaje: 0, estado: true),
              Promocion(id: 2, cantidadMin: 3, cantidadMax: 4, porcentaje: 5, estado: true),
              Promocion(id: 3, cantidadMin: 5, cantidadMax: 9, porcentaje: 10, estado: true),
              Promocion(id: 4, cantidadMin: 10, cantidadMax: null, porcentaje: 15, estado: true),
            ],
          ),
        ),
      ),
    );

    expect(find.text('Descuentos por volumen'), findsOneWidget);
    expect(find.text('1–2 entradas: 0%'), findsOneWidget);
    expect(find.text('3–4 entradas: 5%'), findsOneWidget);
    expect(find.text('5–9 entradas: 10%'), findsOneWidget);
    expect(find.text('10+ entradas: 15%'), findsOneWidget);
  });

  testWidgets('CarritoScreen muestra estado vacío y deshabilita [+] al alcanzar stock máximo', (tester) async {
    final session = Session();
    final deps = _buildFakeDeps(session);
    final cart = CartController();

    await tester.pumpWidget(
      MultiProvider(
        providers: [
          ChangeNotifierProvider<Session>.value(value: session),
          Provider<AppDependencies>.value(value: deps),
          ChangeNotifierProvider<CartController>.value(value: cart),
        ],
        child: const MaterialApp(home: CarritoScreen()),
      ),
    );
    await tester.pumpAndSettle();

    expect(find.textContaining('Tu carrito está vacío'), findsOneWidget);

    // Add item at max stock (2 of 2)
    cart.add(
      CartItem(
        tipoEntradaId: 1,
        tipo: 'VIP',
        evento: 'Rock Fest',
        precio: 25.0,
        stock: 2,
        cantidad: 2,
      ),
    );
    await tester.pump(const Duration(milliseconds: 300));
    await tester.pumpAndSettle();

    expect(find.text('Rock Fest · VIP'), findsOneWidget);
    final addButton = tester.widget<IconButton>(
      find.widgetWithIcon(IconButton, Icons.add_circle_outline),
    );
    expect(addButton.onPressed, isNull);
    expect(find.text('Confirmar compra'), findsOneWidget);
  });
}
