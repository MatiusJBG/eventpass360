import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/app_dependencies.dart';
import '../../core/session.dart';
import '../../core/theme.dart';
import '../../domain/entities.dart';
import '../../domain/ui_state.dart';
import '../core/widgets/feedback_views.dart';
import '../core/widgets/status_badges.dart';
import 'cart_controller.dart';

class PerfilScreen extends StatefulWidget {
  const PerfilScreen({super.key});

  @override
  State<PerfilScreen> createState() => _PerfilScreenState();
}

class _PerfilScreenState extends State<PerfilScreen> {
  final _formKey = GlobalKey<FormState>();
  final _nombre = TextEditingController();
  final _correo = TextEditingController();
  final _password = TextEditingController();

  UiState<Usuario> _state = const UiLoading();
  bool _saving = false;
  bool _obscurePassword = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  @override
  void dispose() {
    _nombre.dispose();
    _correo.dispose();
    _password.dispose();
    super.dispose();
  }

  Future<void> _load() async {
    setState(() => _state = const UiLoading());
    final repo = context.read<AppDependencies>().usuarios;
    try {
      final usuario = await repo.getPerfil();
      if (!mounted) return;
      _nombre.text = usuario.nombre;
      _correo.text = usuario.correo;
      _password.clear();
      setState(() => _state = UiSuccess(usuario));
    } catch (e) {
      if (mounted) setState(() => _state = UiError(e.toString()));
    }
  }

  Future<void> _guardar() async {
    if (!(_formKey.currentState?.validate() ?? false)) return;
    setState(() => _saving = true);
    final deps = context.read<AppDependencies>();
    final session = context.read<Session>();
    try {
      final updated = await deps.usuarios.actualizarPerfil(
        nombre: _nombre.text.trim(),
        correo: _correo.text.trim(),
        password: _password.text.isEmpty ? null : _password.text,
      );
      session.updateUser(updated);
      if (!mounted) return;
      _password.clear();
      setState(() => _state = UiSuccess(updated));
      showAppSnack(context, 'Perfil actualizado correctamente');
    } catch (e) {
      if (mounted) showAppSnack(context, e.toString(), error: true);
    } finally {
      if (mounted) setState(() => _saving = false);
    }
  }

  void _logout() {
    context.read<CartController>().clear();
    context.read<Session>().clear();
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Mi Perfil'),
        actions: [
          IconButton(
            tooltip: 'Recargar perfil',
            icon: const Icon(Icons.refresh),
            onPressed: _load,
          ),
        ],
      ),
      body: switch (_state) {
        UiLoading() => const LoadingView(label: 'Cargando perfil...'),
        UiError(:final message) => ErrorStateView(
            message: message,
            onRetry: _load,
          ),
        UiSuccess(:final data) => SingleChildScrollView(
            padding: const EdgeInsets.all(20),
            child: Center(
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 480),
                child: Card(
                  child: Padding(
                    padding: const EdgeInsets.all(24),
                    child: Form(
                      key: _formKey,
                      autovalidateMode: AutovalidateMode.onUserInteraction,
                      child: Column(
                        children: [
                          const CircleAvatar(
                            radius: 38,
                            backgroundColor: surfaceTint,
                            child: Icon(Icons.person, size: 40, color: accent),
                          ),
                          const SizedBox(height: 12),
                          Text(
                            data.nombre,
                            style: Theme.of(context)
                                .textTheme
                                .titleLarge
                                ?.copyWith(
                                  fontWeight: FontWeight.bold,
                                  color: brand,
                                ),
                          ),
                          const SizedBox(height: 6),
                          Wrap(
                            spacing: 8,
                            runSpacing: 6,
                            alignment: WrapAlignment.center,
                            children: [
                              Chip(
                                label: Text(
                                  data.rol.isNotEmpty ? data.rol : 'CLIENTE',
                                ),
                              ),
                              StatusBadge.fromBool(data.estado),
                            ],
                          ),
                          const SizedBox(height: 22),
                          TextFormField(
                            controller: _nombre,
                            decoration: const InputDecoration(
                              labelText: 'Nombre',
                              prefixIcon: Icon(Icons.person_outline),
                            ),
                            validator: (v) {
                              if (v == null || v.trim().isEmpty) {
                                return 'El nombre es obligatorio';
                              }
                              return null;
                            },
                          ),
                          const SizedBox(height: 14),
                          TextFormField(
                            controller: _correo,
                            decoration: const InputDecoration(
                              labelText: 'Correo electrónico',
                              prefixIcon: Icon(Icons.email_outlined),
                            ),
                            keyboardType: TextInputType.emailAddress,
                            validator: (v) {
                              final text = v?.trim() ?? '';
                              if (text.isEmpty) {
                                return 'El correo es obligatorio';
                              }
                              if (!RegExp(r'^[^@\s]+@[^@\s]+\.[^@\s]+$')
                                  .hasMatch(text)) {
                                return 'Ingresa un correo válido';
                              }
                              return null;
                            },
                          ),
                          const SizedBox(height: 14),
                          TextFormField(
                            controller: _password,
                            decoration: InputDecoration(
                              labelText: 'Nueva contraseña (opcional)',
                              helperText:
                                  'Déjalo vacío para mantener tu contraseña actual',
                              prefixIcon: const Icon(Icons.lock_outline),
                              suffixIcon: IconButton(
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
                            validator: (v) {
                              if (v == null || v.isEmpty) return null;
                              if (v.length < 6) {
                                return 'Mínimo 6 caracteres';
                              }
                              return null;
                            },
                          ),
                          const SizedBox(height: 22),
                          LoadingButton(
                            loading: _saving,
                            onPressed: _guardar,
                            label: 'Guardar cambios',
                            loadingLabel: 'Guardando...',
                            icon: Icons.save_outlined,
                            expand: true,
                          ),
                          const SizedBox(height: 12),
                          SizedBox(
                            width: double.infinity,
                            child: OutlinedButton.icon(
                              icon: const Icon(Icons.logout),
                              label: const Text('Cerrar sesión'),
                              onPressed: _saving ? null : _logout,
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
      },
    );
  }
}
