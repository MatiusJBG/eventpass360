import 'dart:convert';

import 'package:http/http.dart' as http;

import 'session.dart';

class ApiException implements Exception {
  final int statusCode;
  final String message;
  ApiException(this.statusCode, this.message);
  @override
  String toString() => message;
}

class ApiClient {
  final Session session;
  ApiClient(this.session);

  Map<String, String> get _headers {
    final h = <String, String>{'Content-Type': 'application/json'};
    final t = session.token;
    if (t != null && t.isNotEmpty) {
      h['Authorization'] = 'Bearer ' + t;
    }
    return h;
  }

  Future<dynamic> get(String url) async {
    final r = await http.get(Uri.parse(url), headers: _headers);
    return _handle(r);
  }

  Future<dynamic> post(String url, [Map<String, dynamic>? body]) async {
    final r = await http.post(Uri.parse(url), headers: _headers, body: body == null ? null : jsonEncode(body));
    return _handle(r);
  }

  Future<dynamic> put(String url, [Map<String, dynamic>? body]) async {
    final r = await http.put(Uri.parse(url), headers: _headers, body: body == null ? null : jsonEncode(body));
    return _handle(r);
  }

  Future<dynamic> patch(String url, [Map<String, dynamic>? body]) async {
    final r = await http.patch(Uri.parse(url), headers: _headers, body: body == null ? null : jsonEncode(body));
    return _handle(r);
  }

  Future<dynamic> delete(String url) async {
    final r = await http.delete(Uri.parse(url), headers: _headers);
    return _handle(r);
  }

  dynamic _handle(http.Response r) {
    final text = utf8.decode(r.bodyBytes);
    dynamic data;
    if (text.isNotEmpty) {
      try {
        data = jsonDecode(text);
      } catch (_) {
        data = text;
      }
    }
    if (r.statusCode >= 200 && r.statusCode < 300) return data;
    final msg = (data is Map && data['message'] != null)
        ? data['message'].toString()
        : 'Error ' + r.statusCode.toString();
    throw ApiException(r.statusCode, msg);
  }
}
