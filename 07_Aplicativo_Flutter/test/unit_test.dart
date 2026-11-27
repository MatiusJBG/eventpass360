import 'dart:convert';

import 'package:eventpass360/core/api_client.dart';
import 'package:eventpass360/core/session.dart';
import 'package:eventpass360/core/validators.dart';
import 'package:eventpass360/data/models.dart';
import 'package:eventpass360/data/repositories.dart';
import 'package:eventpass360/domain/entities.dart';
import 'package:eventpass360/domain/ui_state.dart';
import 'package:eventpass360/ui/cliente/cart_controller.dart';
import 'package:flutter/services.dart';
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

  group('Typed models fromJson / toJson & row_version OCC', () {
    test('serializa y deserializa UsuarioModel con rolId y row_version', () {
      final json = {
        'id': 7,
        'rol_id': 2,
        'rol': 'CLIENTE',
        'nombre': 'Ana Pérez',
        'correo': 'ana@eventpass.ec',
        'estado': true,
        'row_version': 4,
      };
      final model = UsuarioModel.fromJson(json);
      expect(model.id, 7);
      expect(model.rolId, 2);
      expect(model.rol, 'CLIENTE');
      expect(model.estado, isTrue);
      expect(model.rowVersion, 4);
      expect(model.toJson(), equals(json));

      // Default row_version = 1 when omitted
      final withoutVersion = UsuarioModel.fromJson({
        'id': 8,
        'rol_id': 2,
        'rol': 'CLIENTE',
        'nombre': 'Luis',
        'correo': 'luis@eventpass.ec',
        'estado': true,
      });
      expect(withoutVersion.rowVersion, 1);
      expect(withoutVersion.toJson()['row_version'], 1);
    });

    test('serializa y deserializa row_version en Rol, Categoria, Evento, TipoEntrada, Promocion, Factura y Compra', () {
      final rol = RolModel.fromJson({
        'id': 1,
        'nombre': 'ADMIN',
        'estado': true,
        'row_version': 3,
      });
      expect(rol.rowVersion, 3);
      expect(rol.toJson()['row_version'], 3);

      final cat = CategoriaModel.fromJson({
        'id': 2,
        'nombre': 'Conciertos',
        'descripcion': 'Música en vivo',
        'estado': true,
        'row_version': 5,
      });
      expect(cat.rowVersion, 5);
      expect(cat.toJson()['row_version'], 5);

      final evento = EventoModel.fromJson({
        'id': 10,
        'categoria_id': 2,
        'nombre': 'Rock Fest',
        'descripcion': 'Festival anual',
        'lugar': 'Quito',
        'fecha': '2026-12-20T20:00:00',
        'imagen_url': 'https://cdn.example.com/rock.jpg',
        'estado': true,
        'categoria': 'Conciertos',
        'row_version': 6,
      });
      expect(evento.rowVersion, 6);
      expect(evento.toJson()['row_version'], 6);

      final tipo = TipoEntradaModel.fromJson({
        'id': 3,
        'evento_id': 9,
        'evento': 'Concierto Sinfónico',
        'tipo': 'Platea',
        'precio': 45.75,
        'stock': 25,
        'estado': true,
        'row_version': 7,
      });
      expect(tipo.precio, 45.75);
      expect(tipo.rowVersion, 7);
      expect(tipo.toJson()['precio'], 45.75);
      expect(tipo.toJson()['row_version'], 7);

      final promo = PromocionModel.fromJson({
        'id': 4,
        'cantidad_min': 10,
        'cantidad_max': null,
        'porcentaje': 15.5,
        'estado': true,
        'row_version': 2,
      });
      expect(promo.cantidadMax, isNull);
      expect(promo.porcentaje, 15.5);
      expect(promo.rowVersion, 2);
      expect(promo.aplicaPara(10), isTrue);
      expect(promo.aplicaPara(9), isFalse);
      expect(promo.toJson()['cantidad_max'], isNull);
      expect(promo.toJson()['row_version'], 2);

      final factura = FacturaModel.fromJson({
        'id': 88,
        'compra_id': 42,
        'numero': 'FAC-000088',
        'fecha': '2026-11-27T10:00:00Z',
        'estado': 'EMITIDA',
        'row_version': 9,
      });
      expect(factura.rowVersion, 9);
      expect(factura.toJson()['row_version'], 9);
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
        'row_version': 3,
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
      expect(compra.rowVersion, 3);
      expect(compra.toJson()['factura_numero'], 'FAC-000088');
      expect(compra.toJson()['row_version'], 3);

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

  group('AppValidators & AppInputFormatters — ZERO emojis & strict field rules', () {
    test('detecta todo tipo de emojis (caras, banderas, corazón, ZWJ, keycaps) y permite español acentuado', () {
      expect(AppValidators.containsEmoji('Hola 😀'), isTrue);
      expect(AppValidators.containsEmoji('Ecuador 🇪🇨'), isTrue);
      expect(AppValidators.containsEmoji('Te amo ❤️'), isTrue);
      expect(AppValidators.containsEmoji('Familia 👨‍👩‍👧‍👦'), isTrue);
      expect(AppValidators.containsEmoji('Top 1️⃣'), isTrue);
      expect(AppValidators.containsEmoji('Estrella ⭐'), isTrue);

      expect(AppValidators.containsEmoji('María José Ñandú-Pérez'), isFalse);
      expect(AppValidators.containsEmoji('precio: 45.50 USD (2026)'), isFalse);
    });

    test('personName rechaza emojis, dígitos, símbolos y longitudes inválidas', () {
      expect(AppValidators.personName('Ana Pérez'), isNull);
      expect(AppValidators.personName("O'Connor-García Jr."), isNull);
      expect(AppValidators.personName('Ana 😀'), AppValidators.emojiErrorMessage);
      expect(AppValidators.personName('Ana123'), isNotNull);
      expect(AppValidators.personName('Ana@#'), isNotNull);
      expect(AppValidators.personName('A'), isNotNull);
      expect(AppValidators.personName(''), isNotNull);
    });

    test('email rechaza emojis y formatos inválidos', () {
      expect(AppValidators.email('usuario.test+1@eventpass.ec'), isNull);
      expect(AppValidators.email('user😀@mail.com'), AppValidators.emojiErrorMessage);
      expect(AppValidators.email('invalido'), isNotNull);
      expect(AppValidators.email('user@dominio'), isNotNull);
      expect(AppValidators.email('user @mail.com'), isNotNull);
      expect(AppValidators.email(''), isNotNull);
    });

    test('password rechaza emojis, espacios en extremos y longitudes fuera de rango', () {
      expect(AppValidators.password('Secreto123'), isNull);
      expect(AppValidators.password('', required: false), isNull);
      expect(AppValidators.password('pass😀123'), AppValidators.emojiErrorMessage);
      expect(AppValidators.password(' 123456'), isNotNull);
      expect(AppValidators.password('12345'), isNotNull);
      expect(AppValidators.password('a' * 73), isNotNull);
    });

    test('httpUrl y isoDateTime validan estrictamente formato y bloquean emojis', () {
      expect(AppValidators.httpUrl('https://cdn.eventpass.ec/img.png'), isNull);
      expect(AppValidators.httpUrl('http://localhost:8080/poster.jpg'), isNull);
      expect(AppValidators.httpUrl('https://cdn.ec/😀.png'), AppValidators.emojiErrorMessage);
      expect(AppValidators.httpUrl('ftp://files.ec/img.png'), isNotNull);
      expect(AppValidators.httpUrl('no-es-url'), isNotNull);
      expect(AppValidators.httpUrl('https://'), isNotNull);

      expect(AppValidators.isoDateTime('2026-12-20T20:00:00'), isNull);
      expect(AppValidators.isoDateTime('2026-12-20 20:00:00'), isNull);
      expect(AppValidators.isoDateTime('2026-12-20T20:00:00😀'), AppValidators.emojiErrorMessage);
      expect(AppValidators.isoDateTime('20/12/2026'), isNotNull);
      expect(AppValidators.isoDateTime('mañana'), isNotNull);
    });

    test('integer y decimal rechazan emojis, letras, negativos, >2 decimales y desbordes', () {
      expect(AppValidators.integer('0', label: 'Stock', min: 0, max: 1000), isNull);
      expect(AppValidators.integer('500', label: 'Stock', min: 0, max: 1000), isNull);
      expect(AppValidators.integer('10😀', label: 'Stock'), AppValidators.emojiErrorMessage);
      expect(AppValidators.integer('12abc', label: 'Stock'), isNotNull);
      expect(AppValidators.integer('-5', label: 'Stock'), isNotNull);
      expect(AppValidators.integer('10.5', label: 'Stock'), isNotNull);
      expect(AppValidators.integer('1001', label: 'Stock', max: 1000), isNotNull);

      expect(AppValidators.decimal('0', label: 'Precio', min: 0, max: 999999.99), isNull);
      expect(AppValidators.decimal('45.50', label: 'Precio', min: 0, max: 999999.99), isNull);
      expect(AppValidators.decimal('45.5😀', label: 'Precio'), AppValidators.emojiErrorMessage);
      expect(AppValidators.decimal('45.555', label: 'Precio'), isNotNull);
      expect(AppValidators.decimal('-10.00', label: 'Precio'), isNotNull);
      expect(AppValidators.decimal('1e5', label: 'Precio'), isNotNull);
      expect(AppValidators.decimal('1000000', label: 'Precio', max: 999999.99), isNotNull);
    });

    test('AppInputFormatters bloquean emojis, letras y exceso de decimales', () {
      String applyFormatters(List<TextInputFormatter> formatters, String oldText, String newText) {
        var value = TextEditingValue(text: newText);
        final oldVal = TextEditingValue(text: oldText);
        for (final f in formatters) {
          value = f.formatEditUpdate(oldVal, value);
        }
        return value.text;
      }

      expect(applyFormatters([AppInputFormatters.noEmoji], '', 'Rock 🎸 Fest 🇪🇨'), 'Rock  Fest ');
      expect(applyFormatters(AppInputFormatters.integerOnly, '', '-12a.5😀9'), '1259');
      expect(applyFormatters(AppInputFormatters.decimal2, '', '45.678abc😀'), '45.67');
      expect(applyFormatters(AppInputFormatters.decimal2, '45.67', '45.678'), '45.67');
      expect(applyFormatters(AppInputFormatters.noSpacesNoEmoji, '', ' a b@c.ec 😀'), 'ab@c.ec');
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

  group('HTTP error mapping, OCC payloads & ApiClient 401 handling', () {
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

    test('envía row_version en actualizarPerfil y anularCompra', () async {
      final session = Session()
        ..setAuth(
          'jwt-token',
          const Usuario(
            id: 1,
            rolId: 2,
            rol: 'CLIENTE',
            nombre: 'Ana',
            correo: 'ana@mail.com',
            estado: true,
            rowVersion: 3,
          ),
        );

      Map<String, dynamic>? perfilBody;
      Map<String, dynamic>? anularBody;

      final mockHttp = MockClient((request) async {
        if (request.url.path.endsWith('/api/perfil') && request.method == 'PUT') {
          perfilBody = jsonDecode(request.body) as Map<String, dynamic>;
          return http.Response(
            jsonEncode({
              'id': 1,
              'rol_id': 2,
              'rol': 'CLIENTE',
              'nombre': 'Ana María',
              'correo': 'ana@mail.com',
              'estado': true,
              'row_version': 4,
            }),
            200,
            headers: {'content-type': 'application/json; charset=utf-8'},
          );
        }
        if (request.url.path.endsWith('/api/compras/42/anular') &&
            request.method == 'PATCH') {
          anularBody = jsonDecode(request.body) as Map<String, dynamic>;
          return http.Response(
            jsonEncode({
              'id': 42,
              'usuario_id': 1,
              'solicitud_id': 's1',
              'fecha': '2026-11-27T10:00:00Z',
              'subtotal': 50.0,
              'descuento': 0.0,
              'base_imponible': 50.0,
              'iva': 7.5,
              'total': 57.5,
              'estado': 'ANULADA',
              'row_version': 2,
              'detalles': const [],
            }),
            200,
          );
        }
        return http.Response('{}', 404);
      });

      final client = ApiClient(session, httpClient: mockHttp);
      final usuariosRepo = UsuariosRepository(client);
      final comprasRepo = ComprasRepository(client);

      final updated = await usuariosRepo.actualizarPerfil(
        nombre: 'Ana María',
        correo: 'ana@mail.com',
        rowVersion: 3,
      );
      expect(perfilBody?['row_version'], 3);
      expect(updated.rowVersion, 4);

      final anulada = await comprasRepo.anularCompra(42, rowVersion: 1);
      expect(anularBody?['row_version'], 1);
      expect(anulada.rowVersion, 2);
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
