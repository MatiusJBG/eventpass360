/// Strict field-by-field form validators and input formatters for EventPass 360.
/// Blocks all emojis across the entire application and enforces strict numeric/text rules.
library;

import 'package:flutter/services.dart';

class AppValidators {
  AppValidators._();

  static const String emojiErrorMessage = 'No se permiten emojis en este campo';

  static final RegExp emojiRegex = RegExp(
    r'[\u{1F000}-\u{1FAFF}\u{2600}-\u{27BF}\u{2300}-\u{23FF}\u{2B00}-\u{2BFF}\uFE00-\uFE0F\u200D\u20E3]',
    unicode: true,
  );

  static final RegExp _personNameRegex =
      RegExp(r"^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ\s.'-]+$");

  static final RegExp _emailRegex =
      RegExp(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$');

  static final RegExp _roleNameRegex =
      RegExp(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑüÜ0-9 _-]+$');

  static final RegExp _isoDateTimeRegex = RegExp(
    r'^\d{4}-\d{2}-\d{2}([T ]\d{2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?)?$',
  );

  static final RegExp _integerRegex = RegExp(r'^\d+$');

  static final RegExp _decimal2Regex = RegExp(r'^\d+(\.\d{1,2})?$');

  static bool containsEmoji(String value) => emojiRegex.hasMatch(value);

  static String? personName(String? value) {
    final raw = value ?? '';
    if (containsEmoji(raw)) return emojiErrorMessage;
    final v = raw.trim();
    if (v.isEmpty) return 'Ingresa un nombre válido';
    if (v.length < 2) return 'El nombre debe tener al menos 2 caracteres';
    if (v.length > 120) return 'El nombre no puede superar 120 caracteres';
    if (!_personNameRegex.hasMatch(v)) {
      return 'El nombre solo puede contener letras y espacios';
    }
    return null;
  }

  static String? email(String? value) {
    final raw = value ?? '';
    if (containsEmoji(raw)) return emojiErrorMessage;
    final v = raw.trim();
    if (v.isEmpty) return 'Ingresa tu correo electrónico';
    if (v.length > 150) return 'El correo no puede superar 150 caracteres';
    if (!_emailRegex.hasMatch(v)) return 'Ingresa un correo válido';
    return null;
  }

  static String? password(String? value, {bool required = true}) {
    final v = value ?? '';
    if (containsEmoji(v)) return emojiErrorMessage;
    if (v.isEmpty) {
      return required ? 'Ingresa tu contraseña' : null;
    }
    if (v != v.trim()) {
      return 'La contraseña no debe tener espacios al inicio o al final';
    }
    if (v.length < 6) {
      return 'La contraseña debe tener al menos 6 caracteres';
    }
    if (v.length > 72) {
      return 'La contraseña no puede superar 72 caracteres';
    }
    return null;
  }

  static String? roleName(String? value) {
    final raw = value ?? '';
    if (containsEmoji(raw)) return emojiErrorMessage;
    final v = raw.trim();
    if (v.isEmpty) return 'El nombre del rol es obligatorio';
    if (v.length < 2) return 'El rol debe tener al menos 2 caracteres';
    if (v.length > 50) return 'El rol no puede superar 50 caracteres';
    if (!_roleNameRegex.hasMatch(v)) {
      return 'El rol solo admite letras, números, espacios y guiones';
    }
    return null;
  }

  static String? plainText(
    String? value, {
    required String label,
    bool required = true,
    int minLength = 2,
    int maxLength = 200,
  }) {
    final raw = value ?? '';
    if (containsEmoji(raw)) return emojiErrorMessage;
    final v = raw.trim();
    if (v.isEmpty) {
      return required ? '$label es obligatorio' : null;
    }
    if (v.length < minLength) {
      return '$label debe tener al menos $minLength caracteres';
    }
    if (v.length > maxLength) {
      return '$label no puede superar $maxLength caracteres';
    }
    return null;
  }

  static String? isoDateTime(String? value) {
    final raw = value ?? '';
    if (containsEmoji(raw)) return emojiErrorMessage;
    final v = raw.trim();
    if (v.isEmpty) return 'La fecha y hora es obligatoria';
    if (!_isoDateTimeRegex.hasMatch(v) ||
        DateTime.tryParse(v.replaceFirst(' ', 'T')) == null) {
      return 'Usa formato ISO válido (ej. 2026-12-20T20:00:00)';
    }
    return null;
  }

  static String? httpUrl(String? value, {bool required = true}) {
    final raw = value ?? '';
    if (containsEmoji(raw)) return emojiErrorMessage;
    final v = raw.trim();
    if (v.isEmpty) {
      return required ? 'La URL es obligatoria' : null;
    }
    if (v.length > 500 || RegExp(r'\s').hasMatch(v)) {
      return 'Ingresa una URL válida (http:// o https://)';
    }
    final uri = Uri.tryParse(v);
    if (uri == null ||
        (uri.scheme != 'http' && uri.scheme != 'https') ||
        uri.host.isEmpty) {
      return 'Ingresa una URL válida (http:// o https://)';
    }
    return null;
  }

  static String? integer(
    String? value, {
    required String label,
    bool required = true,
    int min = 0,
    int max = 1000000,
  }) {
    final raw = value ?? '';
    if (containsEmoji(raw)) return emojiErrorMessage;
    final v = raw.trim();
    if (v.isEmpty) {
      return required ? '$label es obligatorio' : null;
    }
    if (!_integerRegex.hasMatch(v)) {
      return '$label solo permite números enteros';
    }
    final parsed = int.tryParse(v);
    if (parsed == null) {
      return 'Ingresa un número entero válido';
    }
    if (parsed < min) {
      return '$label debe ser mayor o igual a $min';
    }
    if (parsed > max) {
      return '$label debe ser menor o igual a $max';
    }
    return null;
  }

  static String? decimal(
    String? value, {
    required String label,
    bool required = true,
    double min = 0,
    double max = 999999.99,
  }) {
    final raw = value ?? '';
    if (containsEmoji(raw)) return emojiErrorMessage;
    final v = raw.trim();
    if (v.isEmpty) {
      return required ? '$label es obligatorio' : null;
    }
    if (!_decimal2Regex.hasMatch(v)) {
      return '$label debe ser un decimal válido (máx. 2 decimales)';
    }
    final parsed = double.tryParse(v);
    if (parsed == null) {
      return 'Ingresa un número decimal válido';
    }
    if (parsed < min) {
      return '$label debe ser mayor o igual a $min';
    }
    if (parsed > max) {
      return '$label debe ser menor o igual a $max';
    }
    return null;
  }
}

class AppInputFormatters {
  AppInputFormatters._();

  static final RegExp _decimal2EditRegex = RegExp(r'^\d*\.?\d{0,2}$');

  static TextInputFormatter get noEmoji =>
      FilteringTextInputFormatter.deny(AppValidators.emojiRegex);

  static List<TextInputFormatter> get integerOnly => [
        noEmoji,
        FilteringTextInputFormatter.digitsOnly,
      ];

  static List<TextInputFormatter> get decimal2 => [
        noEmoji,
        TextInputFormatter.withFunction((oldValue, newValue) {
          final text = newValue.text;
          if (text.isEmpty || _decimal2EditRegex.hasMatch(text)) {
            return newValue;
          }
          // For single-character invalid typing, reject cleanly without losing cursor/text.
          if (oldValue.text.isNotEmpty &&
              text.length == oldValue.text.length + 1) {
            return oldValue;
          }
          // For paste / programmatic enterText, sanitize to digits + at most one dot + 2 decimals.
          final buf = StringBuffer();
          var seenDot = false;
          var decimals = 0;
          for (var i = 0; i < text.length; i++) {
            final ch = text[i];
            final code = ch.codeUnitAt(0);
            if (code >= 48 && code <= 57) {
              if (seenDot) {
                if (decimals >= 2) continue;
                decimals++;
              }
              buf.write(ch);
            } else if (ch == '.' && !seenDot) {
              seenDot = true;
              buf.write(ch);
            }
          }
          final sanitized = buf.toString();
          return TextEditingValue(
            text: sanitized,
            selection: TextSelection.collapsed(offset: sanitized.length),
          );
        }),
      ];

  static List<TextInputFormatter> get noSpacesNoEmoji => [
        noEmoji,
        FilteringTextInputFormatter.deny(RegExp(r'\s')),
      ];
}
