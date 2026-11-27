import 'dart:convert';
import 'dart:typed_data';

/// Non-web stub (VM/tests/desktop) that completes gracefully without crashing.
Future<bool> downloadFileBytes({
  required Uint8List bytes,
  required String filename,
  required String mimeType,
}) async {
  return bytes.isNotEmpty && filename.isNotEmpty && mimeType.isNotEmpty;
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
