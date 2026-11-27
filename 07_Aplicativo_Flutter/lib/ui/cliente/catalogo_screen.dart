import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/api_client.dart';
import '../../core/format.dart';
import '../../core/session.dart';
import '../../core/theme.dart';
import '../../data/repositories.dart';
import '../../domain/entities.dart';
import '../widgets.dart';
import 'cart_controller.dart';

class CatalogoScreen extends StatefulWidget {
  const CatalogoScreen({super.key});
  @override
  State<CatalogoScreen> createState() => _CatalogoScreenState();
}

class _CatalogoScreenState extends State<CatalogoScreen> {
  List<Evento>? _eventos;
  List<Categoria>? _categorias;
  String? _error;
  String _q = '';
  int? _categoriaId;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() { _error = null; _eventos = null; });
    try {
      final session = context.read<Session>();
      final repo = EventosRepository(ApiClient(session));
      final cats = await repo.listarCategorias();
      final evs = await repo.listarEventos(q: _q.isEmpty ? null : _q, categoriaId: _categoriaId);
      if (mounted) setState(() { _categorias = cats; _eventos = evs; });
    } catch (e) {
      if (mounted) setState(() => _error = e.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Catálogo de Eventos')),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: Row(
              children: [
                Expanded(
                  child: TextField(
                    decoration: const InputDecoration(hintText: 'Buscar evento...', prefixIcon: Icon(Icons.search), isDense: true),
                    onChanged: (v) => _q = v,
                    onSubmitted: (_) => _load(),
                  ),
                ),
                const SizedBox(width: 8),
                DropdownButton<int?>(
                  value: _categoriaId,
                  hint: const Text('Categoría'),
                  items: [
                    const DropdownMenuItem<int?>(value: null, child: Text('Todas')),
                    ...?_categorias?.map((c) => DropdownMenuItem<int?>(value: c.id, child: Text(c.nombre))),
                  ],
                  onChanged: (v) { setState(() => _categoriaId = v); _load(); },
                ),
              ],
            ),
          ),
          Expanded(child: _buildBody()),
        ],
      ),
    );
  }

  Widget _buildBody() {
    if (_error != null) return ErrorView(_error!, onRetry: _load);
    if (_eventos == null) return const LoadingView();
    if (_eventos!.isEmpty) return const EmptyView('No hay eventos disponibles');
    return ListView.builder(
      padding: const EdgeInsets.all(12),
      itemCount: _eventos!.length,
      itemBuilder: (context, i) {
        final e = _eventos![i];
        return Card(
          child: ListTile(
            leading: CircleAvatar(child: Icon(Icons.event, color: accent)),
            title: Text(e.nombre),
            subtitle: Text(e.categoria + ' · ' + e.lugar + ' · ' + fecha(e.fecha)),
            isThreeLine: true,
            trailing: const Icon(Icons.chevron_right),
            onTap: () => _openEntradas(e),
          ),
        );
      },
    );
  }

  void _openEntradas(Evento e) {
    Navigator.of(context).push(MaterialPageRoute(builder: (_) => EntradasScreen(evento: e)));
  }
}

class EntradasScreen extends StatefulWidget {
  final Evento evento;
  const EntradasScreen({super.key, required this.evento});
  @override
  State<EntradasScreen> createState() => _EntradasScreenState();
}

class _EntradasScreenState extends State<EntradasScreen> {
  List<TipoEntrada>? _entradas;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final session = context.read<Session>();
      final repo = EventosRepository(ApiClient(session));
      final entradas = await repo.listarEntradas(widget.evento.id);
      if (mounted) setState(() => _entradas = entradas);
    } catch (e) {
      if (mounted) setState(() => _error = e.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.evento.nombre)),
      body: _buildBody(),
    );
  }

  Widget _buildBody() {
    if (_error != null) return ErrorView(_error!, onRetry: _load);
    if (_entradas == null) return const LoadingView();
    if (_entradas!.isEmpty) return const EmptyView('Sin tipos de entrada');
    return ListView.builder(
      padding: const EdgeInsets.all(12),
      itemCount: _entradas!.length,
      itemBuilder: (context, i) {
        final t = _entradas![i];
        final agotado = t.stock <= 0;
        return Card(
          child: ListTile(
            title: Text(t.tipo),
            subtitle: Text(agotado ? 'Agotado' : t.stock.toString() + ' disponibles'),
            trailing: Column(
              mainAxisAlignment: MainAxisAlignment.center,
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(money(t.precio), style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                const SizedBox(height: 4),
                FilledButton.tonal(
                  onPressed: agotado ? null : () {
                    context.read<CartController>().add(CartItem(tipoEntradaId: t.id, tipo: t.tipo, evento: widget.evento.nombre, precio: t.precio));
                    showSnack(context, 'Agregado al carrito');
                  },
                  child: const Text('Agregar'),
                ),
              ],
            ),
          ),
        );
      },
    );
  }
}
