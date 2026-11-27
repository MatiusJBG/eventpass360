import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/api_client.dart';
import '../../core/session.dart';
import '../../core/theme.dart';
import '../../data/repositories.dart';
import '../widgets.dart';

class AuthScreen extends StatefulWidget {
  const AuthScreen({super.key});
  @override
  State<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> {
  bool _login = true;
  bool _loading = false;
  final _nombre = TextEditingController();
  final _correo = TextEditingController();
  final _password = TextEditingController();

  @override
  void dispose() {
    _nombre.dispose();
    _correo.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _submit() async {
    setState(() => _loading = true);
    final session = context.read<Session>();
    final repo = UsuariosRepository(ApiClient(session));
    try {
      if (_login) {
        final r = await repo.login(_correo.text.trim(), _password.text);
        session.setAuth(r['token'] as String, r['usuario'] as Map<String, dynamic>);
      } else {
        await repo.registro(_nombre.text.trim(), _correo.text.trim(), _password.text);
        final r = await repo.login(_correo.text.trim(), _password.text);
        session.setAuth(r['token'] as String, r['usuario'] as Map<String, dynamic>);
      }
    } catch (e) {
      if (mounted) showSnack(context, e.toString(), error: true);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      body: Center(
        child: SingleChildScrollView(
          padding: const EdgeInsets.all(24),
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 420),
            child: Card(
              child: Padding(
                padding: const EdgeInsets.all(24),
                child: Column(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.confirmation_number, size: 56, color: accent),
                    const SizedBox(height: 8),
                    Text('EventPass 360', style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold, color: brand)),
                    const SizedBox(height: 4),
                    Text(_login ? 'Iniciar sesión' : 'Crear cuenta', style: Theme.of(context).textTheme.bodyLarge),
                    const SizedBox(height: 20),
                    if (!_login) ...[
                      TextField(controller: _nombre, decoration: const InputDecoration(labelText: 'Nombre')),
                      const SizedBox(height: 12),
                    ],
                    TextField(controller: _correo, decoration: const InputDecoration(labelText: 'Correo'), keyboardType: TextInputType.emailAddress),
                    const SizedBox(height: 12),
                    TextField(controller: _password, decoration: const InputDecoration(labelText: 'Contraseña'), obscureText: true),
                    const SizedBox(height: 20),
                    SizedBox(
                      width: double.infinity,
                      child: ElevatedButton(
                        onPressed: _loading ? null : _submit,
                        child: _loading ? const SizedBox(height: 20, width: 20, child: CircularProgressIndicator(strokeWidth: 2, color: Colors.white)) : Text(_login ? 'Ingresar' : 'Registrarse'),
                      ),
                    ),
                    TextButton(
                      onPressed: () => setState(() => _login = !_login),
                      child: Text(_login ? '¿No tienes cuenta? Regístrate' : '¿Ya tienes cuenta? Inicia sesión'),
                    ),
                  ],
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
