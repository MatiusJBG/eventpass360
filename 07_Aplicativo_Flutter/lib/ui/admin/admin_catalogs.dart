import 'package:flutter/material.dart';
import 'package:provider/provider.dart';

import '../../core/app_dependencies.dart';
import '../../core/format.dart';
import '../core/widgets/status_badges.dart';
import 'admin_crud_panel.dart';

class AdminCatalogsHub extends StatefulWidget {
  const AdminCatalogsHub({super.key});

  @override
  State<AdminCatalogsHub> createState() => _AdminCatalogsHubState();
}

class _AdminCatalogsHubState extends State<AdminCatalogsHub> {
  static const _tabs = [
    ('Usuarios', Icons.people_outline),
    ('Roles', Icons.badge_outlined),
    ('Categorías', Icons.category_outlined),
    ('Eventos', Icons.event_outlined),
    ('Tipos de Entrada', Icons.confirmation_num_outlined),
    ('Promociones', Icons.percent_outlined),
  ];

  int _selected = 0;

  @override
  Widget build(BuildContext context) {
    final deps = context.read<AppDependencies>();

    return Column(
      children: [
        Material(
          color: Colors.white,
          elevation: 1,
          child: SizedBox(
            height: 56,
            child: ListView.separated(
              scrollDirection: Axis.horizontal,
              padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 8),
              itemCount: _tabs.length,
              separatorBuilder: (_, _) => const SizedBox(width: 8),
              itemBuilder: (context, index) {
                final (label, icon) = _tabs[index];
                return ChoiceChip(
                  avatar: Icon(icon, size: 18),
                  label: Text(label),
                  selected: _selected == index,
                  onSelected: (_) => setState(() => _selected = index),
                );
              },
            ),
          ),
        ),
        Expanded(
          child: switch (_selected) {
            0 => _UsuariosCatalog(deps: deps),
            1 => _RolesCatalog(deps: deps),
            2 => _CategoriasCatalog(deps: deps),
            3 => _EventosCatalog(deps: deps),
            4 => _TiposEntradaCatalog(deps: deps),
            _ => _PromocionesCatalog(deps: deps),
          },
        ),
      ],
    );
  }
}

class _UsuariosCatalog extends StatelessWidget {
  final AppDependencies deps;
  const _UsuariosCatalog({required this.deps});

  @override
  Widget build(BuildContext context) {
    return AdminCrudPanel(
      key: const ValueKey('crud_usuarios'),
      title: 'Usuarios',
      entityLabel: 'Usuario',
      serverSearch: true,
      fields: [
        const CrudField(
          'nombre',
          'Nombre completo',
          type: FieldType.personName,
        ),
        const CrudField('correo', 'Correo electrónico', type: FieldType.email),
        const CrudField(
          'password',
          'Contraseña',
          type: FieldType.password,
          requiredOnCreateOnly: true,
          helperText: 'Mínimo 6 caracteres (en edición déjalo vacío si no cambia)',
        ),
        CrudField(
          'rol_id',
          'Rol',
          type: FieldType.dropdown,
          loadOptions: () async {
            final roles = await deps.usuarios.listarRoles();
            return roles.map((r) => CrudOption(r.id, r.nombre)).toList();
          },
        ),
      ],
      load: (q) async {
        final users = await deps.usuarios.listarUsuarios(q);
        return users
            .map(
              (u) => CrudRecord(
                id: u.id,
                title: u.nombre,
                subtitle: '${u.correo} · Rol: ${u.rol}',
                estado: u.estado,
                values: {
                  'nombre': u.nombre,
                  'correo': u.correo,
                  'rol_id': u.rolId,
                  'row_version': u.rowVersion,
                },
              ),
            )
            .toList();
      },
      create: (body) => deps.usuarios.crearUsuario(body),
      update: (id, body) => deps.usuarios.actualizarUsuario(id, body),
      delete: (id) => deps.usuarios.eliminarUsuario(id),
    );
  }
}

class _RolesCatalog extends StatelessWidget {
  final AppDependencies deps;
  const _RolesCatalog({required this.deps});

  @override
  Widget build(BuildContext context) {
    return AdminCrudPanel(
      key: const ValueKey('crud_roles'),
      title: 'Roles',
      entityLabel: 'Rol',
      fields: const [
        CrudField(
          'nombre',
          'Nombre del rol',
          type: FieldType.roleName,
          minLength: 2,
          maxLength: 50,
        ),
      ],
      load: (_) async {
        final roles = await deps.usuarios.listarRoles();
        return roles
            .map(
              (r) => CrudRecord(
                id: r.id,
                title: r.nombre,
                subtitle: 'ID #${r.id}',
                estado: r.estado,
                values: {
                  'nombre': r.nombre,
                  'row_version': r.rowVersion,
                },
              ),
            )
            .toList();
      },
      create: (body) => deps.usuarios.crearRol(body['nombre'] as String),
      update: (id, body) => deps.usuarios.actualizarRol(id, body),
      delete: (id) => deps.usuarios.eliminarRol(id),
    );
  }
}

class _CategoriasCatalog extends StatelessWidget {
  final AppDependencies deps;
  const _CategoriasCatalog({required this.deps});

  @override
  Widget build(BuildContext context) {
    return AdminCrudPanel(
      key: const ValueKey('crud_categorias'),
      title: 'Categorías',
      entityLabel: 'Categoría',
      fields: const [
        CrudField(
          'nombre',
          'Nombre',
          type: FieldType.text,
          minLength: 2,
          maxLength: 100,
        ),
        CrudField(
          'descripcion',
          'Descripción',
          type: FieldType.multiline,
          required: false,
          minLength: 0,
          maxLength: 500,
        ),
      ],
      load: (_) async {
        final cats = await deps.eventos.listarCategorias();
        return cats
            .map(
              (c) => CrudRecord(
                id: c.id,
                title: c.nombre,
                subtitle: c.descripcion,
                estado: c.estado,
                values: {
                  'nombre': c.nombre,
                  'descripcion': c.descripcion,
                  'row_version': c.rowVersion,
                },
              ),
            )
            .toList();
      },
      create: (body) => deps.eventos.crearCategoria(body),
      update: (id, body) => deps.eventos.actualizarCategoria(id, body),
      delete: (id) => deps.eventos.eliminarCategoria(id),
    );
  }
}

class _EventosCatalog extends StatelessWidget {
  final AppDependencies deps;
  const _EventosCatalog({required this.deps});

  @override
  Widget build(BuildContext context) {
    return AdminCrudPanel(
      key: const ValueKey('crud_eventos'),
      title: 'Eventos',
      entityLabel: 'Evento',
      fields: [
        CrudField(
          'categoria_id',
          'Categoría',
          type: FieldType.dropdown,
          loadOptions: () async {
            final cats = await deps.eventos.listarCategorias();
            return cats.map((c) => CrudOption(c.id, c.nombre)).toList();
          },
        ),
        const CrudField(
          'nombre',
          'Nombre del evento',
          type: FieldType.text,
          minLength: 2,
          maxLength: 150,
        ),
        const CrudField(
          'descripcion',
          'Descripción',
          type: FieldType.multiline,
          minLength: 5,
          maxLength: 1000,
        ),
        const CrudField(
          'lugar',
          'Lugar',
          type: FieldType.text,
          minLength: 2,
          maxLength: 200,
        ),
        const CrudField(
          'fecha',
          'Fecha y hora (ISO 8601)',
          type: FieldType.dateTime,
          helperText: 'Ejemplo: 2026-12-20T20:00:00 (o usa el calendario)',
        ),
        const CrudField(
          'imagen_url',
          'URL de imagen',
          type: FieldType.url,
          helperText: 'Debe iniciar con http:// o https://',
        ),
      ],
      load: (_) async {
        final eventos =
            await deps.eventos.listarEventos(incluirInactivos: true);
        return eventos
            .map(
              (e) => CrudRecord(
                id: e.id,
                title: e.nombre,
                subtitle:
                    '${e.categoria.isNotEmpty ? '${e.categoria} · ' : ''}${e.lugar} · ${fecha(e.fecha)}',
                estado: e.estado,
                values: {
                  'categoria_id': e.categoriaId,
                  'nombre': e.nombre,
                  'descripcion': e.descripcion,
                  'lugar': e.lugar,
                  'fecha': e.fecha,
                  'imagen_url': e.imagenUrl,
                  'row_version': e.rowVersion,
                },
              ),
            )
            .toList();
      },
      create: (body) => deps.eventos.crearEvento(body),
      update: (id, body) => deps.eventos.actualizarEvento(id, body),
      delete: (id) => deps.eventos.eliminarEvento(id),
    );
  }
}

class _TiposEntradaCatalog extends StatelessWidget {
  final AppDependencies deps;
  const _TiposEntradaCatalog({required this.deps});

  @override
  Widget build(BuildContext context) {
    return AdminCrudPanel(
      key: const ValueKey('crud_tipos_entrada'),
      title: 'Tipos de Entrada',
      entityLabel: 'Tipo de entrada',
      fields: [
        CrudField(
          'evento_id',
          'Evento',
          type: FieldType.dropdown,
          loadOptions: () async {
            final eventos =
                await deps.eventos.listarEventos(incluirInactivos: true);
            return eventos.map((e) => CrudOption(e.id, e.nombre)).toList();
          },
        ),
        const CrudField(
          'tipo',
          'Nombre del tipo (ej. VIP, General)',
          type: FieldType.text,
          minLength: 2,
          maxLength: 100,
        ),
        const CrudField(
          'precio',
          'Precio (USD)',
          type: FieldType.decimal,
          min: 0,
          max: 999999.99,
          helperText: 'Acepta decimales (máx. 2), ej. 45.50',
        ),
        const CrudField(
          'stock',
          'Stock disponible',
          type: FieldType.integer,
          min: 0,
          max: 1000000,
        ),
      ],
      load: (_) async {
        final tipos = await deps.eventos.listarTiposEntrada();
        return tipos
            .map(
              (t) => CrudRecord(
                id: t.id,
                title: '${t.evento.isNotEmpty ? '${t.evento} · ' : ''}${t.tipo}',
                subtitle: 'Precio: ${money(t.precio)}',
                estado: t.estado,
                extraBadge: StockBadge(stock: t.stock),
                values: {
                  'evento_id': t.eventoId,
                  'tipo': t.tipo,
                  'precio': t.precio,
                  'stock': t.stock,
                  'row_version': t.rowVersion,
                },
              ),
            )
            .toList();
      },
      create: (body) => deps.eventos.crearTipoEntrada(body),
      update: (id, body) => deps.eventos.actualizarTipoEntrada(id, body),
      delete: (id) => deps.eventos.eliminarTipoEntrada(id),
    );
  }
}

class _PromocionesCatalog extends StatelessWidget {
  final AppDependencies deps;
  const _PromocionesCatalog({required this.deps});

  @override
  Widget build(BuildContext context) {
    return AdminCrudPanel(
      key: const ValueKey('crud_promociones'),
      title: 'Promociones',
      entityLabel: 'Promoción',
      fields: const [
        CrudField(
          'cantidad_min',
          'Cantidad mínima',
          type: FieldType.integer,
          min: 1,
          max: 1000000,
        ),
        CrudField(
          'cantidad_max',
          'Cantidad máxima',
          type: FieldType.optionalInteger,
          required: false,
          min: 1,
          max: 1000000,
          helperText: 'Déjalo vacío para "Sin límite"',
        ),
        CrudField(
          'porcentaje',
          'Porcentaje de descuento (%)',
          type: FieldType.decimal,
          min: 0,
          max: 100,
          helperText: 'Valor entre 0 y 100 (máx. 2 decimales)',
        ),
      ],
      crossFieldValidator: (payload) {
        final min = payload['cantidad_min'] as int?;
        final max = payload['cantidad_max'] as int?;
        if (min != null && max != null && max < min) {
          return 'La cantidad máxima debe ser mayor o igual a la cantidad mínima ($min).';
        }
        return null;
      },
      load: (_) async {
        final promos = await deps.promociones.listarPromociones();
        return promos
            .map(
              (p) => CrudRecord(
                id: p.id,
                title: p.cantidadMax == null
                    ? '${p.cantidadMin}+ entradas (Sin límite)'
                    : '${p.cantidadMin}–${p.cantidadMax} entradas',
                subtitle: 'Descuento: ${porcentaje(p.porcentaje)}',
                estado: p.estado,
                values: {
                  'cantidad_min': p.cantidadMin,
                  'cantidad_max': p.cantidadMax,
                  'porcentaje': p.porcentaje,
                  'row_version': p.rowVersion,
                },
              ),
            )
            .toList();
      },
      create: (body) => deps.promociones.crearPromocion(body),
      update: (id, body) => deps.promociones.actualizarPromocion(id, body),
      delete: (id) => deps.promociones.eliminarPromocion(id),
    );
  }
}
