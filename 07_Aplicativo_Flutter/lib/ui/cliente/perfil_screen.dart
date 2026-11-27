import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/session.dart';

class PerfilScreen extends StatelessWidget {
  const PerfilScreen({super.key});
  @override
  Widget build(BuildContext context) {
    final session = context.watch<Session>();
    return Scaffold(
      appBar: AppBar(title: const Text('Mi Perfil')),
      body: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          children: [
            const CircleAvatar(radius: 40, child: Icon(Icons.person, size: 40)),
            const SizedBox(height: 16),
            Text(session.nombre, style: Theme.of(context).textTheme.titleLarge),
            Text(session.correo, style: Theme.of(context).textTheme.bodyMedium),
            const SizedBox(height: 8),
            Chip(label: Text(session.isAdmin ? 'ADMIN' : 'CLIENTE')),
            const SizedBox(height: 24),
            SizedBox(
              width: double.infinity,
              child: OutlinedButton.icon(
                icon: const Icon(Icons.logout),
                label: const Text('Cerrar sesión'),
                onPressed: () => session.clear(),
              ),
            ),
          ],
        ),
      ),
    );
  }
}
