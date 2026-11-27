import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/app_dependencies.dart';
import '../../core/session.dart';
import '../../core/theme.dart';
import '../../core/validators.dart';
import '../core/widgets/feedback_views.dart';

class AuthScreen extends StatefulWidget {
  const AuthScreen({super.key});

  @override
  State<AuthScreen> createState() => _AuthScreenState();
}

class _AuthScreenState extends State<AuthScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nombre = TextEditingController();
  final _correo = TextEditingController();
  final _password = TextEditingController();

  bool _isLogin = true;
  bool _loading = false;
  bool _obscurePassword = true;

  @override
  void dispose() {
    _nombre.dispose();
    _correo.dispose();
    _password.dispose();
    super.dispose();
  }

  String? _validateNombre(String? value) {
    if (_isLogin) return null;
    return AppValidators.personName(value);
  }

  String? _validateCorreo(String? value) => AppValidators.email(value);

  String? _validatePassword(String? value) => AppValidators.password(value);

  Future<void> _submit() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    setState(() => _loading = true);
    final session = context.read<Session>();
    final repo = context.read<AppDependencies>().usuarios;
    try {
      final correo = _correo.text.trim();
      final password = _password.text;
      if (!_isLogin) {
        await repo.registro(_nombre.text.trim(), correo, password);
      }
      final auth = await repo.login(correo, password);
      session.setAuth(auth.token, auth.usuario);
    } catch (e) {
      if (mounted) showAppSnack(context, e.toString(), error: true);
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  void _toggleMode() {
    setState(() {
      _isLogin = !_isLogin;
      _formKey.currentState?.reset();
    });
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
              elevation: 2,
              child: Padding(
                padding: const EdgeInsets.all(28),
                child: Form(
                  key: _formKey,
                  autovalidateMode: AutovalidateMode.onUserInteraction,
                  child: Column(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(
                        Icons.confirmation_number,
                        size: 56,
                        color: accent,
                      ),
                      const SizedBox(height: 8),
                      Text(
                        'EventPass 360',
                        style:
                            Theme.of(context).textTheme.headlineSmall?.copyWith(
                                  fontWeight: FontWeight.bold,
                                  color: brand,
                                ),
                      ),
                      const SizedBox(height: 4),
                      Text(
                        _isLogin ? 'Iniciar sesión' : 'Crear cuenta de cliente',
                        style: Theme.of(context).textTheme.bodyLarge,
                      ),
                      const SizedBox(height: 24),
                      if (!_isLogin) ...[
                        TextFormField(
                          controller: _nombre,
                          inputFormatters: [AppInputFormatters.noEmoji],
                          decoration: const InputDecoration(
                            labelText: 'Nombre completo',
                            prefixIcon: Icon(Icons.person_outline),
                          ),
                          textInputAction: TextInputAction.next,
                          validator: _validateNombre,
                        ),
                        const SizedBox(height: 14),
                      ],
                      TextFormField(
                        controller: _correo,
                        inputFormatters: AppInputFormatters.noSpacesNoEmoji,
                        decoration: const InputDecoration(
                          labelText: 'Correo electrónico',
                          prefixIcon: Icon(Icons.email_outlined),
                        ),
                        keyboardType: TextInputType.emailAddress,
                        textInputAction: TextInputAction.next,
                        validator: _validateCorreo,
                      ),
                      const SizedBox(height: 14),
                      TextFormField(
                        controller: _password,
                        inputFormatters: [AppInputFormatters.noEmoji],
                        decoration: InputDecoration(
                          labelText: 'Contraseña',
                          prefixIcon: const Icon(Icons.lock_outline),
                          suffixIcon: IconButton(
                            tooltip: _obscurePassword
                                ? 'Mostrar contraseña'
                                : 'Ocultar contraseña',
                            icon: Icon(
                              _obscurePassword
                                  ? Icons.visibility_outlined
                                  : Icons.visibility_off_outlined,
                            ),
                            onPressed: () => setState(
                              () => _obscurePassword = !_obscurePassword,
                            ),
                          ),
                        ),
                        obscureText: _obscurePassword,
                        textInputAction: TextInputAction.done,
                        onFieldSubmitted: (_) => _loading ? null : _submit(),
                        validator: _validatePassword,
                      ),
                      const SizedBox(height: 22),
                      LoadingButton(
                        loading: _loading,
                        onPressed: _submit,
                        label: _isLogin ? 'Ingresar' : 'Registrarse',
                        loadingLabel: _isLogin
                            ? 'Iniciando sesión...'
                            : 'Creando cuenta...',
                        expand: true,
                      ),
                      const SizedBox(height: 12),
                      TextButton(
                        onPressed: _loading ? null : _toggleMode,
                        child: Text(
                          _isLogin
                              ? '¿No tienes cuenta? Regístrate'
                              : '¿Ya tienes cuenta? Inicia sesión',
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
