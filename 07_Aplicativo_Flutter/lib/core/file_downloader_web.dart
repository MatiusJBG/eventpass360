import 'dart:convert';
import 'dart:js_interop';
import 'dart:typed_data';

@JS('Blob')
extension type _JsBlob._(JSObject _) implements JSObject {
  external factory _JsBlob(JSArray<JSAny> parts, _BlobOptions options);
}

extension type _BlobOptions._(JSObject _) implements JSObject {
  external factory _BlobOptions({String type});
}

@JS('URL')
extension type _JsUrl._(JSObject _) implements JSObject {
  external static String createObjectURL(_JsBlob blob);
  external static void revokeObjectURL(String url);
}

@JS('document')
external _JsDocument get _document;

extension type _JsDocument._(JSObject _) implements JSObject {
  external _JsAnchorElement createElement(String tagName);
  external _JsElement? get body;
}

extension type _JsElement._(JSObject _) implements JSObject {
  external void appendChild(_JsElement node);
  external void removeChild(_JsElement node);
}

extension type _JsAnchorElement._(JSObject _) implements _JsElement {
  external set href(String value);
  external set download(String value);
  external void click();
}

/// Triggers a real authenticated browser download from in-memory bytes.
Future<bool> downloadFileBytes({
  required Uint8List bytes,
  required String filename,
  required String mimeType,
}) async {
  final blob = _JsBlob(
    <JSAny>[bytes.toJS].toJS,
    _BlobOptions(type: mimeType),
  );
  final objectUrl = _JsUrl.createObjectURL(blob);
  final anchor = _document.createElement('a')
    ..href = objectUrl
    ..download = filename;
  final body = _document.body;
  body?.appendChild(anchor);
  anchor.click();
  body?.removeChild(anchor);
  _JsUrl.revokeObjectURL(objectUrl);
  return true;
}

Future<bool> downloadTextFile({
  required String content,
  required String filename,
  required String mimeType,
}) {
  return downloadFileBytes(
    bytes: Uint8List.fromList(utf8.encode(content)),
    filename: filename,
    mimeType: mimeType,
  );
}
