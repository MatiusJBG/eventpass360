import 'dart:convert';

import 'package:eventpass360/core/api_client.dart';
import 'package:eventpass360/core/session.dart';
import 'package:eventpass360/data/models.dart';
import 'package:eventpass360/domain/entities.dart';
import 'package:eventpass360/domain/ui_state.dart';
import 'package:eventpass360/ui/cliente/cart_controller.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';

void main() {
  group('CartController — stock bounds & idempotency key', () {
    test('respeta el límite de stock en add e increment y decrementa hasta eliminar', () {
      final cart = CartController();

      expect(
        cart.add(
          CartItem(
            tipoEntradaId: 1,
            tipo: 'VIP',
            evento: 'Rock Fest',
            precio: 50.0,
            stock: 0,
          ),
        ),
        isFalse,
      );
      expect(cart.items, isEmpty);

      expect(
        cart.add(
          CartItem(
            tipoEntradaId: 1,
            tipo: 'VIP',
            evento: 'Rock Fest',
            precio: 50.0,
            stock: 3,
            cantidad: 2,
          ),
        ),
        isTrue,
      );
      expect(cart.totalCantidad, 2);
      expect(cart.subtotal, 100.0);
      expect(cart.canAddMore(1, 3), isTrue);

      expect(cart.increment(1), isTrue);
      expect(cart.totalCantidad, 3);
      expect(cart.canAddMore(1, 3), isFalse);

      // Cannot exceed stock
      expect(cart.increment(1), isFalse);
      expect(
        cart.add(
          CartItem(
            tipoEntradaId: 1,
            tipo: 'VIP',
            evento: 'Rock Fest',
            precio: 50.0,
            stock: 3,
          ),
        ),
        isFalse,
      );
      expect(cart.totalCantidad, 3);

      cart.decrement(1);
      cart.decrement(1);
      cart.decrement(1);
      expect(cart.items, isEmpty);
    });

    test('mantiene estable solicitudId durante reintentos y la regenera solo al mutar el carrito', () {
      final cart = CartController();
      cart.add(
        CartItem(
          tipoEntradaId: 10,
          tipo: 'General',
          evento: 'Jazz Night',
          precio: 20.0,
          stock: 10,
        ),
      );

      final firstKey = cart.getOrCreateSolicitudId();
      final retryKey = cart.getOrCreateSolicitudId();
      expect(firstKey, equals(retryKey));
      expect(firstKey, startsWith('ep360-'));

      // Mutating cart resets idempotency key
      cart.increment(10);
      expect(cart.currentSolicitudId, isNull);
      final nextKey = cart.getOrCreateSolicitudId();
      expect(nextKey, isNot(equals(firstKey)));

      cart.clear();
      expect(cart.currentSolicitudId, isNull);
      expect(cart.items, isEmpty);
    });
  });

  group('Typed models fromJson / toJson', () {
    test('serializa y deserializa UsuarioModel con rolId', () {
      final json = {
        'id': 7,
        'rol_id': 2,
        'rol': 'CLIENTE',
        'nombre': 'Ana Pérez',
        'correo': 'ana@eventpass.ec',
        'estado': true,
      };
      final model = UsuarioModel.fromJson(json);
      expect(model.id, 7);
      expect(model.rolId, 2);
      expect(model.rol, 'CLIENTE');
      expect(model.estado, isTrue);
      expect(model.toJson(), equals(json));
    });

    test('serializa y deserializa TipoEntradaModel con precio decimal y PromocionModel con cantidad_max null', () {
      final tipo = TipoEntradaModel.fromJson({
        'id': 3,
        'evento_id': 9,
        'evento': 'Concierto Sinfónico',
        'tipo': 'Platea',
        'precio': 45.75,
        'stock': 25,
        'estado': true,
      });
      expect(tipo.precio, 45.75);
      expect(tipo.toJson()['precio'], 45.75);

      final promo = PromocionModel.fromJson({
        'id': 4,
        'cantidad_min': 10,
        'cantidad_max': null,
        'porcentaje': 15.5,
        'estado': true,
      });
      expect(promo.cantidadMax, isNull);
      expect(promo.porcentaje, 15.5);
      expect(promo.aplicaPara(10), isTrue);
      expect(promo.aplicaPara(9), isFalse);
      expect(promo.toJson()['cantidad_max'], isNull);
    });

    test('serializa y deserializa CompraModel, ResumenCompraModel y EstadisticasModel', () {
      final compra = CompraModel.fromJson({
        'id': 42,
        'usuario_id': 3,
        'usuario_nombre': 'Carlos',
        'usuario_correo': 'carlos@mail.com',
        'solicitud_id': 'req-1',
        'fecha': '2026-11-27T10:00:00Z',
        'subtotal': 100.0,
        'descuento': 10.0,
        'base_imponible': 90.0,
        'iva': 13.5,
        'total': 103.5,
        'estado': 'CONFIRMADA',
        'factura': {
          'id': 88,
          'compra_id': 42,
          'numero': 'FAC-000088',
          'estado': 'EMITIDA',
        },
        'detalles': [
          {
            'tipo_entrada_id': 5,
            'tipo': 'VIP',
            'evento': 'Expo Tech',
            'cantidad': 2,
            'precio_unitario': 50.0,
            'subtotal': 100.0,
          },
        ],
      });

      expect(compra.usuarioNombre, 'Carlos');
      expect(compra.facturaId, 88);
      expect(compra.facturaNumero, 'FAC-000088');
      expect(compra.facturaEstado, 'EMITIDA');
      expect(compra.detalles.length, 1);
      expect(compra.toJson()['factura_numero'], 'FAC-000088');

      final resumen = ResumenCompraModel.fromJson({
        'cantidad_total': 5,
        'subtotal': 200.0,
        'porcentaje_descuento': 10.0,
        'descuento': 20.0,
        'base_imponible': 180.0,
        'iva': 27.0,
        'total': 207.0,
      });
      expect(resumen.toJson()['total'], 207.0);

      final stats = EstadisticasModel.fromJson({
        'total_compras': 12,
        'ingresos_totales': 1450.25,
        'entradas_vendidas': 38,
        'por_estado': {'CONFIRMADA': 10, 'ANULADA': 2},
      });
      expect(stats.porEstado['CONFIRMADA'], 10);
      expect(stats.toJson()['entradas_vendidas'], 38);
    });
  });

  group('UiState Dart 3 exhaustive switch', () {
    test('evalúa todos los estados de UiState<T>', () {
      String describe(UiState<int> state) => switch (state) {
            UiLoading() => 'loading',
            UiSuccess(:final data) => 'ok:$data',
            UiError(:final message) => 'err:$message',
          };

      expect(describe(const UiLoading<int>()), 'loading');
      expect(describe(const UiSuccess<int>(42)), 'ok:42');
      expect(describe(const UiError<int>('fallo')), 'err:fallo');
    });
  });

  group('HTTP error mapping & ApiClient 401 handling', () {
    test('traduce códigos HTTP sin mensaje específico a mensajes amigables en español', () {
      expect(mapHttpErrorMessage(400), contains('Datos inválidos'));
      expect(mapHttpErrorMessage(401, 'Error 401'), contains('Sesión expirada'));
      expect(mapHttpErrorMessage(403), contains('permisos'));
      expect(mapHttpErrorMessage(409), contains('Conflicto'));
      expect(mapHttpErrorMessage(503), contains('temporalmente no disponible'));
      expect(
        mapHttpErrorMessage(409, 'Stock insuficiente para VIP'),
        equals('Stock insuficiente para VIP'),
      );
    });

    test('limpia la sesión automáticamente ante 401 en rutas protegidas y adjunta Bearer en getText/getBytes', () async {
      final session = Session()
        ..setAuth(
          'jwt-secret-token',
          const Usuario(
            id: 1,
            rolId: 2,
            rol: 'CLIENTE',
            nombre: 'Test',
            correo: 'test@mail.com',
            estado: true,
          ),
        );

      String? capturedAuthHeader;
      final mockHttp = MockClient((request) async {
        capturedAuthHeader = request.headers['Authorization'];
        if (request.url.path.endsWith('/xml')) {
          return http.Response('<factura><numero>FAC-000001</numero></factura>', 200);
        }
        return http.Response(jsonEncode({'message': 'Token expirado'}), 401);
      });

      final client = ApiClient(session, httpClient: mockHttp);

      final xml = await client.getText('http://localhost:5004/api/factura/1/xml');
      expect(xml, contains('FAC-000001'));
      expect(capturedAuthHeader, equals('Bearer jwt-secret-token'));
      expect(session.isAuthenticated, isTrue);

      await expectLater(
        () => client.get('http://localhost:5000/api/compras'),
        throwsA(isA<ApiException>()),
      );
      expect(session.isAuthenticated, isFalse);
    });
  });
}
