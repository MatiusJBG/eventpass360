/// Typed JSON serialization models mapped cleanly to pure domain entities.
library;

import '../domain/entities.dart';

int _asInt(dynamic v, [int fallback = 0]) {
  if (v is int) return v;
  if (v is num) return v.toInt();
  if (v is String) return int.tryParse(v) ?? fallback;
  return fallback;
}

int? _asNullableInt(dynamic v) {
  if (v == null) return null;
  if (v is int) return v;
  if (v is num) return v.toInt();
  if (v is String) return int.tryParse(v);
  return null;
}

double _asDouble(dynamic v, [double fallback = 0.0]) {
  if (v is double) return v;
  if (v is num) return v.toDouble();
  if (v is String) return double.tryParse(v) ?? fallback;
  return fallback;
}

bool _asBool(dynamic v, [bool fallback = false]) {
  if (v is bool) return v;
  if (v is num) return v != 0;
  if (v is String) return v.toLowerCase() == 'true' || v == '1';
  return fallback;
}

class UsuarioModel extends Usuario {
  const UsuarioModel({
    required super.id,
    required super.rolId,
    required super.rol,
    required super.nombre,
    required super.correo,
    required super.estado,
    super.rowVersion = 1,
  });

  factory UsuarioModel.fromJson(Map<String, dynamic> json) => UsuarioModel(
        id: _asInt(json['id']),
        rolId: _asInt(json['rol_id']),
        rol: json['rol']?.toString() ?? '',
        nombre: json['nombre']?.toString() ?? '',
        correo: json['correo']?.toString() ?? '',
        estado: _asBool(json['estado'], true),
        rowVersion: (json['row_version'] as num?)?.toInt() ?? 1,
      );

  factory UsuarioModel.fromEntity(Usuario e) => UsuarioModel(
        id: e.id,
        rolId: e.rolId,
        rol: e.rol,
        nombre: e.nombre,
        correo: e.correo,
        estado: e.estado,
        rowVersion: e.rowVersion,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'rol_id': rolId,
        'rol': rol,
        'nombre': nombre,
        'correo': correo,
        'estado': estado,
        'row_version': rowVersion,
      };
}

class RolModel extends Rol {
  const RolModel({
    required super.id,
    required super.nombre,
    required super.estado,
    super.rowVersion = 1,
  });

  factory RolModel.fromJson(Map<String, dynamic> json) => RolModel(
        id: _asInt(json['id']),
        nombre: json['nombre']?.toString() ?? '',
        estado: _asBool(json['estado'], true),
        rowVersion: (json['row_version'] as num?)?.toInt() ?? 1,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'nombre': nombre,
        'estado': estado,
        'row_version': rowVersion,
      };
}

class CategoriaModel extends Categoria {
  const CategoriaModel({
    required super.id,
    required super.nombre,
    required super.descripcion,
    required super.estado,
    super.rowVersion = 1,
  });

  factory CategoriaModel.fromJson(Map<String, dynamic> json) => CategoriaModel(
        id: _asInt(json['id']),
        nombre: json['nombre']?.toString() ?? '',
        descripcion: json['descripcion']?.toString() ?? '',
        estado: _asBool(json['estado'], true),
        rowVersion: (json['row_version'] as num?)?.toInt() ?? 1,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'nombre': nombre,
        'descripcion': descripcion,
        'estado': estado,
        'row_version': rowVersion,
      };
}

class EventoModel extends Evento {
  const EventoModel({
    required super.id,
    required super.categoriaId,
    required super.nombre,
    required super.descripcion,
    required super.lugar,
    required super.fecha,
    required super.imagenUrl,
    required super.estado,
    required super.categoria,
    super.rowVersion = 1,
  });

  factory EventoModel.fromJson(Map<String, dynamic> json) => EventoModel(
        id: _asInt(json['id']),
        categoriaId: _asInt(json['categoria_id']),
        nombre: json['nombre']?.toString() ?? '',
        descripcion: json['descripcion']?.toString() ?? '',
        lugar: json['lugar']?.toString() ?? '',
        fecha: json['fecha']?.toString() ?? '',
        imagenUrl: json['imagen_url']?.toString() ?? '',
        estado: _asBool(json['estado'], true),
        categoria: json['categoria']?.toString() ?? '',
        rowVersion: (json['row_version'] as num?)?.toInt() ?? 1,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'categoria_id': categoriaId,
        'nombre': nombre,
        'descripcion': descripcion,
        'lugar': lugar,
        'fecha': fecha,
        'imagen_url': imagenUrl,
        'estado': estado,
        'categoria': categoria,
        'row_version': rowVersion,
      };
}

class TipoEntradaModel extends TipoEntrada {
  const TipoEntradaModel({
    required super.id,
    required super.eventoId,
    required super.tipo,
    required super.precio,
    required super.stock,
    required super.estado,
    required super.evento,
    super.rowVersion = 1,
  });

  factory TipoEntradaModel.fromJson(Map<String, dynamic> json) =>
      TipoEntradaModel(
        id: _asInt(json['id']),
        eventoId: _asInt(json['evento_id']),
        tipo: json['tipo']?.toString() ?? '',
        precio: _asDouble(json['precio']),
        stock: _asInt(json['stock']),
        estado: _asBool(json['estado'], true),
        evento: json['evento']?.toString() ?? '',
        rowVersion: (json['row_version'] as num?)?.toInt() ?? 1,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'evento_id': eventoId,
        'tipo': tipo,
        'precio': precio,
        'stock': stock,
        'estado': estado,
        'evento': evento,
        'row_version': rowVersion,
      };
}

class PromocionModel extends Promocion {
  const PromocionModel({
    required super.id,
    required super.cantidadMin,
    super.cantidadMax,
    required super.porcentaje,
    required super.estado,
    super.rowVersion = 1,
  });

  factory PromocionModel.fromJson(Map<String, dynamic> json) => PromocionModel(
        id: _asInt(json['id']),
        cantidadMin: _asInt(json['cantidad_min'], 1),
        cantidadMax: _asNullableInt(json['cantidad_max']),
        porcentaje: _asDouble(json['porcentaje']),
        estado: _asBool(json['estado'], true),
        rowVersion: (json['row_version'] as num?)?.toInt() ?? 1,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'cantidad_min': cantidadMin,
        'cantidad_max': cantidadMax,
        'porcentaje': porcentaje,
        'estado': estado,
        'row_version': rowVersion,
      };
}

class DetalleCompraModel extends DetalleCompra {
  const DetalleCompraModel({
    required super.tipoEntradaId,
    required super.tipo,
    required super.evento,
    required super.cantidad,
    required super.precioUnitario,
    required super.subtotal,
  });

  factory DetalleCompraModel.fromJson(Map<String, dynamic> json) =>
      DetalleCompraModel(
        tipoEntradaId: _asInt(json['tipo_entrada_id']),
        tipo: json['tipo']?.toString() ?? '',
        evento: json['evento']?.toString() ?? '',
        cantidad: _asInt(json['cantidad']),
        precioUnitario: _asDouble(json['precio_unitario']),
        subtotal: _asDouble(json['subtotal']),
      );

  factory DetalleCompraModel.fromEntity(DetalleCompra e) => DetalleCompraModel(
        tipoEntradaId: e.tipoEntradaId,
        tipo: e.tipo,
        evento: e.evento,
        cantidad: e.cantidad,
        precioUnitario: e.precioUnitario,
        subtotal: e.subtotal,
      );

  Map<String, dynamic> toJson() => {
        'tipo_entrada_id': tipoEntradaId,
        'tipo': tipo,
        'evento': evento,
        'cantidad': cantidad,
        'precio_unitario': precioUnitario,
        'subtotal': subtotal,
      };
}

class FacturaModel extends Factura {
  const FacturaModel({
    required super.id,
    required super.compraId,
    required super.numero,
    required super.fecha,
    required super.estado,
    super.rowVersion = 1,
  });

  factory FacturaModel.fromJson(Map<String, dynamic> json) => FacturaModel(
        id: _asInt(json['id']),
        compraId: _asInt(json['compra_id']),
        numero: json['numero']?.toString() ?? '',
        fecha: json['fecha']?.toString() ?? '',
        estado: json['estado']?.toString() ?? '',
        rowVersion: (json['row_version'] as num?)?.toInt() ?? 1,
      );

  Map<String, dynamic> toJson() => {
        'id': id,
        'compra_id': compraId,
        'numero': numero,
        'fecha': fecha,
        'estado': estado,
        'row_version': rowVersion,
      };
}

class CompraModel extends Compra {
  const CompraModel({
    required super.id,
    required super.usuarioId,
    required super.usuarioNombre,
    required super.usuarioCorreo,
    required super.solicitudId,
    required super.fecha,
    required super.subtotal,
    required super.descuento,
    required super.baseImponible,
    required super.iva,
    required super.total,
    required super.estado,
    super.facturaId,
    super.facturaNumero,
    super.facturaEstado,
    required super.detalles,
    super.rowVersion = 1,
  });

  factory CompraModel.fromJson(Map<String, dynamic> json) {
    final facturaRaw = json['factura'];
    final facturaMap =
        facturaRaw is Map<String, dynamic> ? facturaRaw : null;
    final detallesRaw = json['detalles'];
    final detallesList = detallesRaw is List
        ? detallesRaw
            .whereType<Map<String, dynamic>>()
            .map(DetalleCompraModel.fromJson)
            .toList()
        : <DetalleCompra>[];

    return CompraModel(
      id: _asInt(json['id']),
      usuarioId: _asInt(json['usuario_id']),
      usuarioNombre: json['usuario_nombre']?.toString() ?? '',
      usuarioCorreo: json['usuario_correo']?.toString() ?? '',
      solicitudId: json['solicitud_id']?.toString() ?? '',
      fecha: json['fecha']?.toString() ?? '',
      subtotal: _asDouble(json['subtotal']),
      descuento: _asDouble(json['descuento']),
      baseImponible: _asDouble(json['base_imponible']),
      iva: _asDouble(json['iva']),
      total: _asDouble(json['total']),
      estado: json['estado']?.toString() ?? '',
      facturaId: _asNullableInt(facturaMap?['id'] ?? json['factura_id']),
      facturaNumero:
          (facturaMap?['numero'] ?? json['factura_numero'])?.toString(),
      facturaEstado:
          (facturaMap?['estado'] ?? json['factura_estado'])?.toString(),
      detalles: detallesList,
      rowVersion: (json['row_version'] as num?)?.toInt() ?? 1,
    );
  }

  Map<String, dynamic> toJson() => {
        'id': id,
        'usuario_id': usuarioId,
        'usuario_nombre': usuarioNombre,
        'usuario_correo': usuarioCorreo,
        'solicitud_id': solicitudId,
        'fecha': fecha,
        'subtotal': subtotal,
        'descuento': descuento,
        'base_imponible': baseImponible,
        'iva': iva,
        'total': total,
        'estado': estado,
        'factura_id': facturaId,
        'factura_numero': facturaNumero,
        'factura_estado': facturaEstado,
        'detalles': detalles
            .map((d) => DetalleCompraModel.fromEntity(d).toJson())
            .toList(),
        'row_version': rowVersion,
      };
}

class ResumenCompraModel extends ResumenCompra {
  const ResumenCompraModel({
    required super.cantidadTotal,
    required super.subtotal,
    required super.porcentajeDescuento,
    required super.descuento,
    required super.baseImponible,
    required super.iva,
    required super.total,
  });

  factory ResumenCompraModel.fromJson(Map<String, dynamic> json) =>
      ResumenCompraModel(
        cantidadTotal: _asInt(json['cantidad_total']),
        subtotal: _asDouble(json['subtotal']),
        porcentajeDescuento: _asDouble(json['porcentaje_descuento']),
        descuento: _asDouble(json['descuento']),
        baseImponible: _asDouble(json['base_imponible']),
        iva: _asDouble(json['iva']),
        total: _asDouble(json['total']),
      );

  Map<String, dynamic> toJson() => {
        'cantidad_total': cantidadTotal,
        'subtotal': subtotal,
        'porcentaje_descuento': porcentajeDescuento,
        'descuento': descuento,
        'base_imponible': baseImponible,
        'iva': iva,
        'total': total,
      };
}

class EstadisticasModel extends Estadisticas {
  const EstadisticasModel({
    required super.totalCompras,
    required super.ingresosTotales,
    required super.entradasVendidas,
    required super.porEstado,
  });

  factory EstadisticasModel.fromJson(Map<String, dynamic> json) {
    final rawEstados = json['por_estado'];
    final estados = <String, int>{};
    if (rawEstados is Map) {
      for (final entry in rawEstados.entries) {
        estados[entry.key.toString()] = _asInt(entry.value);
      }
    }
    return EstadisticasModel(
      totalCompras: _asInt(json['total_compras']),
      ingresosTotales: _asDouble(json['ingresos_totales']),
      entradasVendidas: _asInt(json['entradas_vendidas']),
      porEstado: estados,
    );
  }

  Map<String, dynamic> toJson() => {
        'total_compras': totalCompras,
        'ingresos_totales': ingresosTotales,
        'entradas_vendidas': entradasVendidas,
        'por_estado': porEstado,
      };
}
