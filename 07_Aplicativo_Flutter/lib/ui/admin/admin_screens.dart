import 'package:flutter/material.dart';

import '../../core/api_client.dart';
import '../../core/format.dart';
import '../../core/theme.dart';
import '../../core/session.dart';
import '../../data/repositories.dart';
import '../../domain/entities.dart';
import '../widgets.dart';

// ---------------------------------------------------------------- Dashboard
class DashboardScreen extends StatefulWidget {
  final AdminRepos repos;
  const DashboardScreen({super.key, required this.repos});
  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  Map<String, dynamic>? _stats;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final s = await widget.repos.compras.estadisticas();
      if (mounted) setState(() => _stats = s as Map<String, dynamic>);
    } catch (e) {
      if (mounted) setState(() => _error = e.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Dashboard')),
      body: _error != null
          ? ErrorView(_error!, onRetry: _load)
          : _stats == null
              ? const LoadingView()
              : Padding(
                  padding: const EdgeInsets.all(16),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text('Estadísticas generales', style: Theme.of(context).textTheme.titleLarge),
                      const SizedBox(height: 16),
                      Wrap(
                        spacing: 16,
                        runSpacing: 16,
                        children: [
                          _StatCard(label: 'Compras', value: _stats!['total_compras']?.toString() ?? '0', icon: Icons.receipt_long),
                          _StatCard(label: 'Ingresos', value: money((_stats!['ingresos_totales'] as num?)?.toDouble()), icon: Icons.payments),
                          _StatCard(label: 'Entradas vendidas', value: _stats!['entradas_vendidas']?.toString() ?? '0', icon: Icons.confirmation_number),
                        ],
                      ),
                      const SizedBox(height: 24),
                      Text('Por estado', style: Theme.of(context).textTheme.titleMedium),
                      const SizedBox(height: 8),
                      if (_stats!['por_estado'] is Map)
                        ...(_stats!['por_estado'] as Map).entries.map((e) => ListTile(
                              dense: true,
                              title: Text(e.key.toString()),
                              trailing: Text(e.value.toString()),
                            )),
                    ],
                  ),
                ),
    );
  }
}

class _StatCard extends StatelessWidget {
  final String label;
  final String value;
  final IconData icon;
  const _StatCard({required this.label, required this.value, required this.icon});
  @override
  Widget build(BuildContext context) {
    return Card(
      child: SizedBox(
        width: 180,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            children: [
              Icon(icon, size: 32, color: accent),
              const SizedBox(height: 8),
              Text(value, style: Theme.of(context).textTheme.headlineSmall?.copyWith(fontWeight: FontWeight.bold)),
              Text(label, style: Theme.of(context).textTheme.bodyMedium),
            ],
          ),
        ),
      ),
    );
  }
}

// ---------------------------------------------------------------- Ventas
class VentasScreen extends StatefulWidget {
  final AdminRepos repos;
  const VentasScreen({super.key, required this.repos});
  @override
  State<VentasScreen> createState() => _VentasScreenState();
}

class _VentasScreenState extends State<VentasScreen> {
  List<Compra>? _compras;
  String? _error;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final c = await widget.repos.compras.listarCompras();
      if (mounted) setState(() => _compras = c);
    } catch (e) {
      if (mounted) setState(() => _error = e.toString());
    }
  }

  Future<void> _anular(Compra c) async {
    try {
      await widget.repos.compras.anularCompra(c.id);
      showSnack(context, 'Compra anulada y stock restaurado');
      _load();
    } catch (e) {
      showSnack(context, e.toString(), error: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: const Text('Ventas y Facturas')),
      body: _error != null
          ? ErrorView(_error!, onRetry: _load)
          : _compras == null
              ? const LoadingView()
              : _compras!.isEmpty
                  ? const EmptyView('No hay compras')
                  : ListView.builder(
                      padding: const EdgeInsets.all(12),
                      itemCount: _compras!.length,
                      itemBuilder: (context, i) {
                        final c = _compras![i];
                        return Card(
                          child: ListTile(
                            title: Text('Compra #' + c.id.toString() + ' · ' + money(c.total)),
                            subtitle: Text(c.usuarioId.toString() + ' · ' + fecha(c.fecha)),
                            trailing: Row(
                              mainAxisSize: MainAxisSize.min,
                              children: [
                                EstadoBadge(c.estado),
                                if (c.estado == 'CONFIRMADA')
                                  IconButton(
                                    icon: const Icon(Icons.block, color: Colors.red),
                                    onPressed: () => _anular(c),
                                    tooltip: 'Anular',
                                  ),
                              ],
                            ),
                          ),
                        );
                      },
                    ),
    );
  }
}

// ---------------------------------------------------------------- CRUD genérico
enum FieldType { text, number, dropdown }

class CrudField {
  final String name;
  final String label;
  final FieldType type;
  final List<MapEntry<dynamic, String>>? options;
  const CrudField(this.name, this.label, {this.type = FieldType.text, this.options});
}

class CrudScreen extends StatefulWidget {
  final String title;
  final List<CrudField> fields;
  final String idKey;
  final String titleKey;
  final String? subtitleKey;
  final Future<List<Map<String, dynamic>>> Function() load;
  final Future<void> Function(Map<String, dynamic> body) create;
  final Future<void> Function(int id, Map<String, dynamic> body) update;
  final Future<void> Function(int id) delete;
  const CrudScreen({super.key, required this.title, required this.fields, required this.idKey, required this.titleKey, this.subtitleKey, required this.load, required this.create, required this.update, required this.delete});

  @override
  State<CrudScreen> createState() => _CrudScreenState();
}

class _CrudScreenState extends State<CrudScreen> {
  List<Map<String, dynamic>>? _items;
  String? _error;
  String _q = '';

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    try {
      final items = await widget.load();
      if (mounted) setState(() { _items = items; _error = null; });
    } catch (e) {
      if (mounted) setState(() => _error = e.toString());
    }
  }

  Future<void> _openForm([Map<String, dynamic>? existing]) async {
    final result = await showDialog<Map<String, dynamic>>(
      context: context,
      builder: (_) => _CrudForm(fields: widget.fields, existing: existing),
    );
    if (result == null) return;
    try {
      if (existing == null) {
        await widget.create(result);
      } else {
        final id = (existing[widget.idKey] as num).toInt();
        await widget.update(id, result);
      }
      showSnack(context, 'Guardado');
      _load();
    } catch (e) {
      showSnack(context, e.toString(), error: true);
    }
  }

  Future<void> _delete(Map<String, dynamic> item) async {
    final ok = await showDialog<bool>(
      context: context,
      builder: (_) => AlertDialog(
        title: const Text('Confirmar eliminación'),
        content: const Text('¿Deseas eliminar este registro?'),
        actions: [
          TextButton(onPressed: () => Navigator.pop(context, false), child: const Text('Cancelar')),
          TextButton(onPressed: () => Navigator.pop(context, true), child: const Text('Eliminar', style: TextStyle(color: Colors.red))),
        ],
      ),
    );
    if (ok != true) return;
    try {
      final id = (item[widget.idKey] as num).toInt();
      await widget.delete(id);
      showSnack(context, 'Eliminado');
      _load();
    } catch (e) {
      showSnack(context, e.toString(), error: true);
    }
  }

  @override
  Widget build(BuildContext context) {
    return Scaffold(
      appBar: AppBar(title: Text(widget.title)),
      floatingActionButton: FloatingActionButton(onPressed: () => _openForm(), child: const Icon(Icons.add)),
      body: Column(
        children: [
          Padding(
            padding: const EdgeInsets.all(12),
            child: TextField(
              decoration: const InputDecoration(hintText: 'Buscar...', prefixIcon: Icon(Icons.search), isDense: true),
              onChanged: (v) => setState(() => _q = v),
            ),
          ),
          Expanded(child: _buildBody()),
        ],
      ),
    );
  }

  Widget _buildBody() {
    if (_error != null) return ErrorView(_error!, onRetry: _load);
    if (_items == null) return const LoadingView();
    final items = _items!.where((m) => (m[widget.titleKey]?.toString() ?? '').toLowerCase().contains(_q.toLowerCase())).toList();
    if (items.isEmpty) return const EmptyView('Sin registros');
    return ListView.builder(
      padding: const EdgeInsets.all(12),
      itemCount: items.length,
      itemBuilder: (context, i) {
        final m = items[i];
        return Card(
          child: ListTile(
            title: Text(m[widget.titleKey]?.toString() ?? ''),
            subtitle: widget.subtitleKey != null ? Text(m[widget.subtitleKey]?.toString() ?? '') : null,
            trailing: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                IconButton(icon: const Icon(Icons.edit), onPressed: () => _openForm(m)),
                IconButton(icon: const Icon(Icons.delete, color: Colors.red), onPressed: () => _delete(m)),
              ],
            ),
          ),
        );
      },
    );
  }
}

class _CrudForm extends StatefulWidget {
  final List<CrudField> fields;
  final Map<String, dynamic>? existing;
  const _CrudForm({required this.fields, this.existing});
  @override
  State<_CrudForm> createState() => _CrudFormState();
}

class _CrudFormState extends State<_CrudForm> {
  late final Map<String, TextEditingController> _controllers;
  late final Map<String, dynamic> _dropdowns;

  @override
  void initState() {
    super.initState();
    _controllers = {};
    _dropdowns = {};
    for (final f in widget.fields) {
      final v = widget.existing?[f.name];
      _controllers[f.name] = TextEditingController(text: v == null ? '' : v.toString());
      _dropdowns[f.name] = v;
    }
  }

  @override
  void dispose() {
    for (final c in _controllers.values) {
      c.dispose();
    }
    super.dispose();
  }

  Map<String, dynamic> _buildBody() {
    final body = <String, dynamic>{};
    for (final f in widget.fields) {
      final raw = _controllers[f.name]!.text.trim();
      switch (f.type) {
        case FieldType.number:
          body[f.name] = int.tryParse(raw) ?? 0;
          break;
        case FieldType.dropdown:
          body[f.name] = _dropdowns[f.name];
          break;
        default:
          body[f.name] = raw;
      }
    }
    return body;
  }

  @override
  Widget build(BuildContext context) {
    return AlertDialog(
      title: Text(widget.existing == null ? 'Nuevo registro' : 'Editar registro'),
      content: SingleChildScrollView(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            for (final f in widget.fields)
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: _field(f),
              ),
          ],
        ),
      ),
      actions: [
        TextButton(onPressed: () => Navigator.pop(context), child: const Text('Cancelar')),
        ElevatedButton(onPressed: () => Navigator.pop(context, _buildBody()), child: const Text('Guardar')),
      ],
    );
  }

  Widget _field(CrudField f) {
    switch (f.type) {
      case FieldType.number:
        return TextField(controller: _controllers[f.name], decoration: InputDecoration(labelText: f.label), keyboardType: TextInputType.number);
      case FieldType.dropdown:
        return DropdownButtonFormField<dynamic>(
          initialValue: _dropdowns[f.name],
          decoration: InputDecoration(labelText: f.label),
          items: (f.options ?? []).map((e) => DropdownMenuItem(value: e.key, child: Text(e.value))).toList(),
          onChanged: (v) => setState(() => _dropdowns[f.name] = v),
        );
      default:
        return TextField(controller: _controllers[f.name], decoration: InputDecoration(labelText: f.label));
    }
  }
}

// ---------------------------------------------------------------- Repos agrupados
class AdminRepos {
  final UsuariosRepository usuarios;
  final EventosRepository eventos;
  final PromocionesRepository promociones;
  final ComprasRepository compras;
  final FacturacionRepository facturacion;
  AdminRepos(Session session)
      : usuarios = UsuariosRepository(ApiClient(session)),
        eventos = EventosRepository(ApiClient(session)),
        promociones = PromocionesRepository(ApiClient(session)),
        compras = ComprasRepository(ApiClient(session)),
        facturacion = FacturacionRepository(ApiClient(session));
}

// ---------------------------------------------------------------- Configs CRUD
class UsuariosCrud extends StatelessWidget {
  final AdminRepos repos;
  const UsuariosCrud({super.key, required this.repos});

  Future<List<Map<String, dynamic>>> _load() async {
    final roles = await repos.usuarios.listarRoles();
    final users = await repos.usuarios.listarUsuarios();
    return users.map((u) => {'id': u.id, 'nombre': u.nombre, 'correo': u.correo, 'rol_id': u.rol, 'rol': u.rol}).toList();
  }

  @override
  Widget build(BuildContext context) {
    return CrudScreen(
      title: 'Usuarios',
      idKey: 'id',
      titleKey: 'nombre',
      subtitleKey: 'correo',
      fields: const [
        CrudField('nombre', 'Nombre'),
        CrudField('correo', 'Correo'),
        CrudField('password', 'Contraseña'),
        CrudField('rol_id', 'Rol', type: FieldType.number),
      ],
      load: _load,
      create: (b) => repos.usuarios.crearUsuario(b),
      update: (id, b) => repos.usuarios.actualizarUsuario(id, b),
      delete: (id) => repos.usuarios.eliminarUsuario(id),
    );
  }
}

class RolesCrud extends StatelessWidget {
  final AdminRepos repos;
  const RolesCrud({super.key, required this.repos});
  @override
  Widget build(BuildContext context) {
    return CrudScreen(
      title: 'Roles',
      idKey: 'id',
      titleKey: 'nombre',
      fields: const [CrudField('nombre', 'Nombre')],
      load: () async => (await repos.usuarios.listarRoles()).map((r) => {'id': r.id, 'nombre': r.nombre}).toList(),
      create: (b) => repos.usuarios.crearRol(b['nombre'] as String),
      update: (id, b) => repos.usuarios.actualizarRol(id, b),
      delete: (id) => repos.usuarios.eliminarRol(id),
    );
  }
}

class CategoriasCrud extends StatelessWidget {
  final AdminRepos repos;
  const CategoriasCrud({super.key, required this.repos});
  @override
  Widget build(BuildContext context) {
    return CrudScreen(
      title: 'Categorías',
      idKey: 'id',
      titleKey: 'nombre',
      subtitleKey: 'descripcion',
      fields: const [CrudField('nombre', 'Nombre'), CrudField('descripcion', 'Descripción')],
      load: () async => (await repos.eventos.listarCategorias()).map((c) => {'id': c.id, 'nombre': c.nombre, 'descripcion': c.descripcion}).toList(),
      create: (b) => repos.eventos.crearCategoria(b),
      update: (id, b) => repos.eventos.actualizarCategoria(id, b),
      delete: (id) => repos.eventos.eliminarCategoria(id),
    );
  }
}

class EventosCrud extends StatelessWidget {
  final AdminRepos repos;
  const EventosCrud({super.key, required this.repos});

  Future<List<MapEntry<dynamic, String>>> _categorias() async {
    final cats = await repos.eventos.listarCategorias();
    return cats.map((c) => MapEntry<dynamic, String>(c.id, c.nombre)).toList();
  }

  @override
  Widget build(BuildContext context) {
    return CrudScreen(
      title: 'Eventos',
      idKey: 'id',
      titleKey: 'nombre',
      subtitleKey: 'lugar',
      fields: const [
        CrudField('categoria_id', 'Categoría', type: FieldType.number),
        CrudField('nombre', 'Nombre'),
        CrudField('descripcion', 'Descripción'),
        CrudField('lugar', 'Lugar'),
        CrudField('fecha', 'Fecha (ISO)'),
        CrudField('imagen_url', 'Imagen URL'),
      ],
      load: () async => (await repos.eventos.listarEventos()).map((e) => {'id': e.id, 'nombre': e.nombre, 'lugar': e.lugar, 'categoria_id': e.categoriaId, 'descripcion': e.descripcion, 'fecha': e.fecha, 'imagen_url': e.imagenUrl}).toList(),
      create: (b) => repos.eventos.crearEvento(b),
      update: (id, b) => repos.eventos.actualizarEvento(id, b),
      delete: (id) => repos.eventos.eliminarEvento(id),
    );
  }
}

class TiposEntradaCrud extends StatelessWidget {
  final AdminRepos repos;
  const TiposEntradaCrud({super.key, required this.repos});
  @override
  Widget build(BuildContext context) {
    return CrudScreen(
      title: 'Tipos de Entrada',
      idKey: 'id',
      titleKey: 'tipo',
      subtitleKey: 'precio',
      fields: const [
        CrudField('evento_id', 'Evento ID', type: FieldType.number),
        CrudField('tipo', 'Tipo'),
        CrudField('precio', 'Precio', type: FieldType.number),
        CrudField('stock', 'Stock', type: FieldType.number),
      ],
      load: () async {
        final eventos = await repos.eventos.listarEventos();
        final result = <Map<String, dynamic>>[];
        for (final e in eventos) {
          for (final t in await repos.eventos.listarEntradas(e.id)) {
            result.add({'id': t.id, 'tipo': t.tipo, 'precio': t.precio.toString(), 'evento_id': t.eventoId, 'stock': t.stock});
          }
        }
        return result;
      },
      create: (b) => repos.eventos.crearTipoEntrada(b),
      update: (id, b) => repos.eventos.actualizarTipoEntrada(id, b),
      delete: (id) => repos.eventos.eliminarTipoEntrada(id),
    );
  }
}

class PromocionesCrud extends StatelessWidget {
  final AdminRepos repos;
  const PromocionesCrud({super.key, required this.repos});
  @override
  Widget build(BuildContext context) {
    return CrudScreen(
      title: 'Promociones',
      idKey: 'id',
      titleKey: 'nombre',
      subtitleKey: 'descripcion',
      fields: const [
        CrudField('cantidad_min', 'Cantidad mínima', type: FieldType.number),
        CrudField('cantidad_max', 'Cantidad máxima (vacío = sin límite)'),
        CrudField('porcentaje', 'Porcentaje', type: FieldType.number),
      ],
      load: () async => (await repos.promociones.listarPromociones()).map((p) => {'id': p.id, 'nombre': p.cantidadMin.toString() + ' - ' + (p.cantidadMax?.toString() ?? '∞'), 'descripcion': p.porcentaje.toString() + '%', 'cantidad_min': p.cantidadMin, 'cantidad_max': p.cantidadMax, 'porcentaje': p.porcentaje}).toList(),
      create: (b) => repos.promociones.crearPromocion(_fixPromo(b)),
      update: (id, b) => repos.promociones.actualizarPromocion(id, _fixPromo(b)),
      delete: (id) => repos.promociones.eliminarPromocion(id),
    );
  }

  Map<String, dynamic> _fixPromo(Map<String, dynamic> b) {
    if (b['cantidad_max'] == null || (b['cantidad_max'] as String).isEmpty) {
      b['cantidad_max'] = null;
    }
    return b;
  }
}
