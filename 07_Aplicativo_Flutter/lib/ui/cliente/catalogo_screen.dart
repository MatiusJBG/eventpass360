import 'dart:async';

import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../app.dart';
import '../../core/app_dependencies.dart';
import '../../core/format.dart';
import '../../core/theme.dart';
import '../../core/validators.dart';
import '../../domain/entities.dart';
import '../../domain/ui_state.dart';
import '../core/widgets/feedback_views.dart';
import '../core/widgets/status_badges.dart';
import 'cart_controller.dart';

class CatalogoScreen extends StatefulWidget {
  const CatalogoScreen({super.key});

  @override
  State<CatalogoScreen> createState() => _CatalogoScreenState();
}

class _CatalogoScreenState extends State<CatalogoScreen> {
  final _searchController = TextEditingController();
  Timer? _debounce;

  UiState<List<Evento>> _state = const UiLoading();
  List<Categoria> _categorias = const [];
  String _query = '';
  int? _categoriaId;

  @override
  void initState() {
    super.initState();
    _loadInitial();
  }

  @override
  void dispose() {
    _debounce?.cancel();
    _searchController.dispose();
    super.dispose();
  }

  Future<void> _loadInitial() async {
    setState(() => _state = const UiLoading());
    final repo = context.read<AppDependencies>().eventos;
    try {
      final results = await Future.wait<dynamic>([
        repo.listarCategorias(),
        repo.listarEventos(
          q: _query.isEmpty ? null : _query,
          categoriaId: _categoriaId,
        ),
      ]);
      if (!mounted) return;
      setState(() {
        _categorias = (results[0] as List<Categoria>)
            .where((c) => c.estado)
            .toList();
        _state = UiSuccess(results[1] as List<Evento>);
      });
    } catch (e) {
      if (mounted) setState(() => _state = UiError(e.toString()));
    }
  }

  Future<void> _loadEventos() async {
    setState(() => _state = const UiLoading());
    final repo = context.read<AppDependencies>().eventos;
    try {
      final eventos = await repo.listarEventos(
        q: _query.isEmpty ? null : _query,
        categoriaId: _categoriaId,
      );
      if (mounted) setState(() => _state = UiSuccess(eventos));
    } catch (e) {
      if (mounted) setState(() => _state = UiError(e.toString()));
    }
  }

  void _onSearchChanged(String value) {
    _query = value.trim();
    _debounce?.cancel();
    _debounce = Timer(const Duration(milliseconds: 350), _loadEventos);
  }

  void _openEntradas(Evento evento) {
    Navigator.of(context).pushNamed(AppRoutes.entradas, arguments: evento);
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(
        title: const Text('Catálogo de Eventos'),
        actions: [
          IconButton(
            tooltip: 'Actualizar catálogo',
            icon: const Icon(Icons.refresh),
            onPressed: _loadInitial,
          ),
        ],
      ),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.fromLTRB(12, 12, 12, 6),
            child: TextField(
              controller: _searchController,
              inputFormatters: [AppInputFormatters.noEmoji],
              decoration: InputDecoration(
                hintText: 'Buscar evento por nombre o lugar...',
                prefixIcon: const Icon(Icons.search),
                isDense: true,
                suffixIcon: _searchController.text.isEmpty
                    ? null
                    : IconButton(
                        tooltip: 'Limpiar búsqueda',
                        icon: const Icon(Icons.clear),
                        onPressed: () {
                          _searchController.clear();
                          setState(() => _query = '');
                          _loadEventos();
                        },
                      ),
              ),
              onChanged: (v) {
                setState(() {});
                _onSearchChanged(v);
              },
              onSubmitted: (_) {
                _debounce?.cancel();
                _loadEventos();
              },
            ),
          ),
          if (_categorias.isNotEmpty)
            SizedBox(
              height: 46,
              child: ListView(
                scrollDirection: Axis.horizontal,
                padding: const EdgeInsets.symmetric(horizontal: 12),
                children: [
                  Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: ChoiceChip(
                      label: const Text('Todas'),
                      selected: _categoriaId == null,
                      onSelected: (_) {
                        setState(() => _categoriaId = null);
                        _loadEventos();
                      },
                    ),
                  ),
                  for (final c in _categorias)
                    Padding(
                      padding: const EdgeInsets.only(right: 8),
                      child: ChoiceChip(
                        label: Text(c.nombre),
                        selected: _categoriaId == c.id,
                        onSelected: (_) {
                          setState(() => _categoriaId = c.id);
                          _loadEventos();
                        },
                      ),
                    ),
                ],
              ),
            ),
          const SizedBox(height: 4),
          Expanded(
            child: switch (_state) {
              UiLoading() => const LoadingView(label: 'Cargando eventos...'),
              UiError(:final message) => ErrorStateView(
                  message: message,
                  onRetry: _loadInitial,
                ),
              UiSuccess(:final data) when data.isEmpty => const EmptyStateView(
                  message: 'No se encontraron eventos con esos filtros.',
                  icon: Icons.event_busy_outlined,
                ),
              UiSuccess(:final data) => RefreshIndicator(
                  onRefresh: _loadInitial,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(12),
                    itemCount: data.length,
                    itemBuilder: (context, index) => _EventoCard(
                      evento: data[index],
                      onOpenEntradas: () => _openEntradas(data[index]),
                    ),
                  ),
                ),
            },
          ),
        ],
      ),
    );
  }
}

class _EventoCard extends StatelessWidget {
  final Evento evento;
  final VoidCallback onOpenEntradas;

  const _EventoCard({
    required this.evento,
    required this.onOpenEntradas,
  });

  @override
  Widget build(BuildContext context) {
    return Card(
      margin: const EdgeInsets.only(bottom: 12),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                CircleAvatar(
                  backgroundColor: surfaceTint,
                  child: const Icon(Icons.event, color: accent),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        evento.nombre,
                        style: Theme.of(context)
                            .textTheme
                            .titleMedium
                            ?.copyWith(fontWeight: FontWeight.bold, color: brand),
                      ),
                      const SizedBox(height: 4),
                      Wrap(
                        spacing: 10,
                        runSpacing: 4,
                        children: [
                          if (evento.categoria.isNotEmpty)
                            Chip(
                              label: Text(evento.categoria),
                              visualDensity: VisualDensity.compact,
                              padding: EdgeInsets.zero,
                            ),
                          Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Icon(Icons.location_on_outlined, size: 15),
                              const SizedBox(width: 4),
                              Text(evento.lugar),
                            ],
                          ),
                          Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Icon(Icons.calendar_today_outlined, size: 15),
                              const SizedBox(width: 4),
                              Text(fecha(evento.fecha)),
                            ],
                          ),
                        ],
                      ),
                    ],
                  ),
                ),
              ],
            ),
            if (evento.descripcion.isNotEmpty) ...[
              const SizedBox(height: 10),
              Text(
                evento.descripcion,
                style: Theme.of(context).textTheme.bodyMedium?.copyWith(
                      color: Colors.grey.shade700,
                    ),
                maxLines: 2,
                overflow: TextOverflow.ellipsis,
              ),
            ],
            const SizedBox(height: 12),
            Align(
              alignment: Alignment.centerRight,
              child: FilledButton.icon(
                onPressed: onOpenEntradas,
                icon: const Icon(Icons.confirmation_num_outlined, size: 18),
                label: const Text('Ver entradas'),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class EntradasScreen extends StatefulWidget {
  final Evento evento;

  const EntradasScreen({super.key, required this.evento});

  @override
  State<EntradasScreen> createState() => _EntradasScreenState();
}

class _EntradasScreenState extends State<EntradasScreen> {
  UiState<List<TipoEntrada>> _state = const UiLoading();

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() => _state = const UiLoading());
    final repo = context.read<AppDependencies>().eventos;
    try {
      final entradas = await repo.listarEntradas(widget.evento.id);
      if (mounted) setState(() => _state = UiSuccess(entradas));
    } catch (e) {
      if (mounted) setState(() => _state = UiError(e.toString()));
    }
  }

  @override
  Widget build(BuildContext context) {
    final cart = context.watch<CartController>();

    return Scaffold(
      appBar: AppBar(
        title: Text(widget.evento.nombre),
        actions: [
          IconButton(
            tooltip: 'Actualizar disponibilidad',
            icon: const Icon(Icons.refresh),
            onPressed: _load,
          ),
        ],
      ),
      body: Column(
        children: [
          Container(
            width: double.infinity,
            color: surfaceTint,
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            child: Wrap(
              spacing: 16,
              runSpacing: 6,
              children: [
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.location_on_outlined,
                        size: 16, color: brand),
                    const SizedBox(width: 4),
                    Text(widget.evento.lugar),
                  ],
                ),
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Icons.calendar_today_outlined,
                        size: 16, color: brand),
                    const SizedBox(width: 4),
                    Text(fecha(widget.evento.fecha)),
                  ],
                ),
              ],
            ),
          ),
          Expanded(
            child: switch (_state) {
              UiLoading() => const LoadingView(label: 'Cargando entradas...'),
              UiError(:final message) => ErrorStateView(
                  message: message,
                  onRetry: _load,
                ),
              UiSuccess(:final data) when data.isEmpty => const EmptyStateView(
                  message: 'Este evento aún no tiene tipos de entrada activos.',
                  icon: Icons.confirmation_number_outlined,
                ),
              UiSuccess(:final data) => RefreshIndicator(
                  onRefresh: _load,
                  child: ListView.builder(
                    padding: const EdgeInsets.all(12),
                    itemCount: data.length,
                    itemBuilder: (context, index) {
                      final entrada = data[index];
                      final enCarrito = cart.quantityOf(entrada.id);
                      final puedeAgregar =
                          cart.canAddMore(entrada.id, entrada.stock);
                      final agotado = entrada.stock <= 0;

                      return Card(
                        margin: const EdgeInsets.only(bottom: 10),
                        child: Padding(
                          padding: const EdgeInsets.all(16),
                          child: Row(
                            crossAxisAlignment: CrossAxisAlignment.center,
                            children: [
                              Expanded(
                                child: Column(
                                  crossAxisAlignment: CrossAxisAlignment.start,
                                  children: [
                                    Text(
                                      entrada.tipo,
                                      style: Theme.of(context)
                                          .textTheme
                                          .titleMedium
                                          ?.copyWith(
                                            fontWeight: FontWeight.bold,
                                            color: brand,
                                          ),
                                    ),
                                    const SizedBox(height: 8),
                                    Wrap(
                                      spacing: 8,
                                      runSpacing: 6,
                                      crossAxisAlignment:
                                          WrapCrossAlignment.center,
                                      children: [
                                        StockBadge(stock: entrada.stock),
                                        if (enCarrito > 0)
                                          Chip(
                                            label: Text('En carrito: $enCarrito'),
                                            visualDensity: VisualDensity.compact,
                                          ),
                                      ],
                                    ),
                                  ],
                                ),
                              ),
                              const SizedBox(width: 12),
                              Column(
                                crossAxisAlignment: CrossAxisAlignment.end,
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Text(
                                    money(entrada.precio),
                                    style: Theme.of(context)
                                        .textTheme
                                        .titleLarge
                                        ?.copyWith(
                                          fontWeight: FontWeight.bold,
                                          color: brand,
                                        ),
                                  ),
                                  const SizedBox(height: 8),
                                  FilledButton.tonalIcon(
                                    onPressed: puedeAgregar
                                        ? () {
                                            final added = context
                                                .read<CartController>()
                                                .add(
                                                  CartItem(
                                                    tipoEntradaId: entrada.id,
                                                    tipo: entrada.tipo,
                                                    evento: widget.evento.nombre,
                                                    precio: entrada.precio,
                                                    stock: entrada.stock,
                                                  ),
                                                );
                                            if (added) {
                                              showAppSnack(
                                                context,
                                                '${entrada.tipo} agregado al carrito',
                                              );
                                            }
                                          }
                                        : null,
                                    icon: const Icon(Icons.add_shopping_cart,
                                        size: 18),
                                    label: Text(
                                      agotado
                                          ? 'Agotado'
                                          : puedeAgregar
                                              ? 'Agregar'
                                              : 'Stock máx.',
                                    ),
                                  ),
                                ],
                              ),
                            ],
                          ),
                        ),
                      );
                    },
                  ),
                ),
            },
          ),
        ],
      ),
    );
  }
}
