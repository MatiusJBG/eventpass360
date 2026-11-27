import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import 'core/app_dependencies.dart';
import 'core/session.dart';
import 'core/theme.dart';
import 'domain/entities.dart';
import 'ui/admin/admin_home.dart';
import 'ui/auth/auth_screen.dart';
import 'ui/cliente/cart_controller.dart';
import 'ui/cliente/catalogo_screen.dart';
import 'ui/cliente/cliente_home.dart';

abstract final class AppRoutes {
  static const String root = '/';
  static const String login = '/login';
  static const String cliente = '/cliente';
  static const String admin = '/admin';
  static const String entradas = '/entradas';
}

class EventPassApp extends StatelessWidget {
  final Session? session;
  final AppDependencies? dependencies;
  final CartController? cartController;

  const EventPassApp({
    super.key,
    this.session,
    this.dependencies,
    this.cartController,
  });

  @override
  Widget build(BuildContext context) {
    return MultiProvider(
      providers: [
        ChangeNotifierProvider<Session>(
          create: (_) => session ?? Session(),
        ),
        ProxyProvider<Session, AppDependencies>(
          update: (_, currentSession, previous) {
            if (dependencies != null) return dependencies!;
            if (previous != null &&
                identical(previous.apiClient.session, currentSession)) {
              return previous;
            }
            return AppDependencies.fromSession(currentSession);
          },
        ),
        ChangeNotifierProvider<CartController>(
          create: (_) => cartController ?? CartController(),
        ),
      ],
      child: const _SessionCartSynchronizer(
        child: _EventPassMaterialApp(),
      ),
    );
  }
}

class _SessionCartSynchronizer extends StatefulWidget {
  final Widget child;
  const _SessionCartSynchronizer({required this.child});

  @override
  State<_SessionCartSynchronizer> createState() =>
      _SessionCartSynchronizerState();
}

class _SessionCartSynchronizerState extends State<_SessionCartSynchronizer> {
  Session? _session;
  bool _wasAuthenticated = false;

  @override
  void didChangeDependencies() {
    super.didChangeDependencies();
    final current = context.read<Session>();
    if (!identical(_session, current)) {
      _session?.removeListener(_onSessionChanged);
      _session = current;
      _wasAuthenticated = current.isAuthenticated;
      _session!.addListener(_onSessionChanged);
    }
  }

  void _onSessionChanged() {
    final isAuth = _session?.isAuthenticated ?? false;
    if (_wasAuthenticated && !isAuth) {
      context.read<CartController>().clear();
    }
    _wasAuthenticated = isAuth;
  }

  @override
  void dispose() {
    _session?.removeListener(_onSessionChanged);
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => widget.child;
}

class _EventPassMaterialApp extends StatelessWidget {
  const _EventPassMaterialApp();

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'EventPass 360',
      debugShowCheckedModeBanner: false,
      theme: buildTheme(),
      initialRoute: AppRoutes.root,
      onGenerateRoute: (settings) {
        final session = context.read<Session>();
        return MaterialPageRoute<void>(
          settings: settings,
          builder: (_) => _guardRoute(settings, session),
        );
      },
    );
  }

  Widget _guardRoute(RouteSettings settings, Session session) {
    switch (settings.name) {
      case AppRoutes.login:
        return session.isAuthenticated ? const RootGate() : const AuthScreen();
      case AppRoutes.admin:
        if (!session.isAuthenticated) return const AuthScreen();
        return session.isAdmin ? const AdminHome() : const ClienteHome();
      case AppRoutes.cliente:
        if (!session.isAuthenticated) return const AuthScreen();
        return session.isAdmin ? const AdminHome() : const ClienteHome();
      case AppRoutes.entradas:
        if (!session.isAuthenticated) return const AuthScreen();
        final arg = settings.arguments;
        if (arg is Evento) return EntradasScreen(evento: arg);
        return const RootGate();
      case AppRoutes.root:
      default:
        return const RootGate();
    }
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
