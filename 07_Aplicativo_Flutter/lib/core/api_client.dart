import 'dart:async';
import 'dart:convert';
import 'dart:io' show SocketException;
import 'dart:typed_data';

import 'package:http/http.dart' as http;

import 'session.dart';

class ApiException implements Exception {
  final int statusCode;
  final String message;

  const ApiException(this.statusCode, this.message);

  @override
  String toString() => message;
}

/// Maps HTTP status codes to friendly, actionable Spanish messages when the
/// backend omits a specific message or returns a generic status label.
String mapHttpErrorMessage(int statusCode, [String? serverMessage]) {
  final cleaned = serverMessage?.trim() ?? '';
  final isGeneric = cleaned.isEmpty ||
      cleaned.toLowerCase() == 'error $statusCode' ||
      cleaned.toLowerCase() == 'internal server error' ||
      cleaned.toLowerCase() == 'bad request' ||
      cleaned.toLowerCase() == 'unauthorized' ||
      cleaned.toLowerCase() == 'forbidden' ||
      cleaned.toLowerCase() == 'conflict' ||
      cleaned.toLowerCase() == 'service unavailable';

  if (!isGeneric) return cleaned;

  return switch (statusCode) {
    400 => 'Datos inválidos. Verifica los campos ingresados.',
    401 => 'Sesión expirada o credenciales inválidas. Inicia sesión nuevamente.',
    403 => 'No tienes permisos para realizar esta acción.',
    404 => 'El recurso solicitado no fue encontrado.',
    409 => 'Conflicto: stock insuficiente, registro duplicado o ya anulado.',
    503 =>
      'Servicio temporalmente no disponible. La operación fue revertida de forma segura.',
    >= 500 => 'Ocurrió un problema interno en el servidor. Inténtalo de nuevo.',
    _ => 'No se pudo completar la solicitud (código $statusCode).',
  };
}

class ApiClient {
  static const Duration defaultTimeout = Duration(seconds: 35);

  final Session session;
  final http.Client _http;
  final Duration timeout;

  ApiClient(
    this.session, {
    http.Client? httpClient,
    this.timeout = defaultTimeout,
  }) : _http = httpClient ?? http.Client();

  Map<String, String> _headers({bool jsonContent = true}) {
    final headers = <String, String>{};
    if (jsonContent) {
      headers['Content-Type'] = 'application/json';
    }
    final token = session.token;
    if (token != null && token.isNotEmpty) {
      headers['Authorization'] = 'Bearer $token';
    }
    return headers;
  }

  Future<dynamic> get(String url) => _executeJson(
        url,
        () => _http.get(Uri.parse(url), headers: _headers()),
      );

  Future<dynamic> post(String url, [Map<String, dynamic>? body]) =>
      _executeJson(
        url,
        () => _http.post(
          Uri.parse(url),
          headers: _headers(),
          body: body == null ? null : jsonEncode(body),
        ),
      );

  Future<dynamic> put(String url, [Map<String, dynamic>? body]) => _executeJson(
        url,
        () => _http.put(
          Uri.parse(url),
          headers: _headers(),
          body: body == null ? null : jsonEncode(body),
        ),
      );

  Future<dynamic> patch(String url, [Map<String, dynamic>? body]) =>
      _executeJson(
        url,
        () => _http.patch(
          Uri.parse(url),
          headers: _headers(),
          body: body == null ? null : jsonEncode(body),
        ),
      );

  Future<dynamic> delete(String url) => _executeJson(
        url,
        () => _http.delete(Uri.parse(url), headers: _headers()),
      );

  /// Authenticated GET returning UTF-8 text (e.g. XML invoices).
  Future<String> getText(String url) async {
    final response = await _send(
      () => _http.get(Uri.parse(url), headers: _headers(jsonContent: false)),
    );
    _throwIfError(url, response);
    return utf8.decode(response.bodyBytes);
  }

  /// Authenticated GET returning raw bytes (e.g. PDF invoices).
  Future<Uint8List> getBytes(String url) async {
    final response = await _send(
      () => _http.get(Uri.parse(url), headers: _headers(jsonContent: false)),
    );
    _throwIfError(url, response);
    return Uint8List.fromList(response.bodyBytes);
  }

  Future<dynamic> _executeJson(
    String url,
    Future<http.Response> Function() request,
  ) async {
    final response = await _send(request);
    final text = utf8.decode(response.bodyBytes);
    dynamic data;
    if (text.isNotEmpty) {
      try {
        data = jsonDecode(text);
      } catch (_) {
        data = text;
      }
    }
    if (response.statusCode >= 200 && response.statusCode < 300) {
      return data;
    }
    _handleUnauthorized(url, response.statusCode);
    final serverMsg =
        (data is Map && data['message'] != null) ? data['message'].toString() : null;
    throw ApiException(
      response.statusCode,
      mapHttpErrorMessage(response.statusCode, serverMsg),
    );
  }

  void _throwIfError(String url, http.Response response) {
    if (response.statusCode >= 200 && response.statusCode < 300) return;
    _handleUnauthorized(url, response.statusCode);
    String? serverMsg;
    try {
      final decoded = jsonDecode(utf8.decode(response.bodyBytes));
      if (decoded is Map && decoded['message'] != null) {
        serverMsg = decoded['message'].toString();
      }
    } catch (_) {
      // Non-JSON error body; fall back to status mapping.
    }
    throw ApiException(
      response.statusCode,
      mapHttpErrorMessage(response.statusCode, serverMsg),
    );
  }

  void _handleUnauthorized(String url, int statusCode) {
    if (statusCode == 401 &&
        session.isAuthenticated &&
        !url.endsWith('/api/login')) {
      session.clear();
    }
  }

  Future<http.Response> _send(Future<http.Response> Function() request) async {
    try {
      return await request().timeout(timeout);
    } on TimeoutException {
      throw const ApiException(
        408,
        'El servicio tardó demasiado en responder. Verifica que los microservicios estén activos e inténtalo nuevamente.',
      );
    } on SocketException {
      throw const ApiException(
        0,
        'No se pudo conectar con el servidor. Verifica tu conexión y que los servicios estén en ejecución.',
      );
    } on http.ClientException {
      throw const ApiException(
        0,
        'No se pudo establecer comunicación con el servicio. Verifica que los microservicios estén disponibles.',
      );
    }
  }
}
