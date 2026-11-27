import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'core/session.dart';
import 'core/theme.dart';
import 'ui/auth/auth_screen.dart';
import 'ui/cliente/cliente_home.dart';
import 'ui/admin/admin_home.dart';

class EventPassApp extends StatelessWidget {
  const EventPassApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'EventPass 360',
      debugShowCheckedModeBanner: false,
      theme: buildTheme(),
      home: const RootGate(),
    );
  }
}

class RootGate extends StatelessWidget {
  const RootGate({super.key});

  @override
  Widget build(BuildContext context) {
    final session = context.watch<Session>();
    if (!session.isAuthenticated) return const AuthScreen();
    if (session.isAdmin) return const AdminHome();
    return const ClienteHome();
  }
}
