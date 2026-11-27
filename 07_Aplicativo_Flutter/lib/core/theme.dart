import 'package:flutter/material.dart';

const brand = Color(0xFF1E1B4B);
const accent = Color(0xFF7C3AED);

ThemeData buildTheme() {
  return ThemeData(
    useMaterial3: true,
    colorScheme: ColorScheme.fromSeed(seedColor: brand, primary: brand, secondary: accent),
    appBarTheme: const AppBarTheme(centerTitle: true, backgroundColor: brand, foregroundColor: Colors.white),
    elevatedButtonTheme: ElevatedButtonThemeData(
      style: ElevatedButton.styleFrom(backgroundColor: accent, foregroundColor: Colors.white),
    ),
    inputDecorationTheme: const InputDecorationTheme(border: OutlineInputBorder()),
  );
}
