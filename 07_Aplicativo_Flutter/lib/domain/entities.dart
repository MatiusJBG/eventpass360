class Usuario {
  final int id;
  final String rol;
  final String nombre;
  final String correo;
  final bool estado;
  Usuario({required this.id, required this.rol, required this.nombre, required this.correo, required this.estado});
  factory Usuario.fromJson(Map<String, dynamic> j) => Usuario(
        id: (j['id'] as num?)?.toInt() ?? 0,
        rol: j['rol']?.toString() ?? '',
        nombre: j['nombre']?.toString() ?? '',
        correo: j['correo']?.toString() ?? '',
        estado: j['estado'] == true,
      );
}

class Rol {
  final int id;
  final String nombre;
  final bool estado;
  Rol({required this.id, required this.nombre, required this.estado});
  factory Rol.fromJson(Map<String, dynamic> j) => Rol(
        id: (j['id'] as num?)?.toInt() ?? 0,
        nombre: j['nombre']?.toString() ?? '',
        estado: j['estado'] == true,
      );
}

class Categoria {
  final int id;
  final String nombre;
  final String descripcion;
  final bool estado;
  Categoria({required this.id, required this.nombre, required this.descripcion, required this.estado});
  factory Categoria.fromJson(Map<String, dynamic> j) => Categoria(
        id: (j['id'] as num?)?.toInt() ?? 0,
        nombre: j['nombre']?.toString() ?? '',
        descripcion: j['descripcion']?.toString() ?? '',
        estado: j['estado'] == true,
      );
}

class Evento {
  final int id;
  final int categoriaId;
  final String nombre;
  final String descripcion;
  final String lugar;
  final String fecha;
  final String imagenUrl;
  final bool estado;
  final String categoria;
  Evento({required this.id, required this.categoriaId, required this.nombre, required this.descripcion, required this.lugar, required this.fecha, required this.imagenUrl, required this.estado, required this.categoria});
  factory Evento.fromJson(Map<String, dynamic> j) => Evento(
        id: (j['id'] as num?)?.toInt() ?? 0,
        categoriaId: (j['categoria_id'] as num?)?.toInt() ?? 0,
        nombre: j['nombre']?.toString() ?? '',
        descripcion: j['descripcion']?.toString() ?? '',
        lugar: j['lugar']?.toString() ?? '',
        fecha: j['fecha']?.toString() ?? '',
        imagenUrl: j['imagen_url']?.toString() ?? '',
        estado: j['estado'] == true,
        categoria: j['categoria']?.toString() ?? '',
      );
}

class TipoEntrada {
  final int id;
  final int eventoId;
  final String tipo;
  final double precio;
  final int stock;
  final bool estado;
  final String evento;
  TipoEntrada({required this.id, required this.eventoId, required this.tipo, required this.precio, required this.stock, required this.estado, required this.evento});
  factory TipoEntrada.fromJson(Map<String, dynamic> j) => TipoEntrada(
        id: (j['id'] as num?)?.toInt() ?? 0,
        eventoId: (j['evento_id'] as num?)?.toInt() ?? 0,
        tipo: j['tipo']?.toString() ?? '',
        precio: (j['precio'] as num?)?.toDouble() ?? 0,
        stock: (j['stock'] as num?)?.toInt() ?? 0,
        estado: j['estado'] == true,
        evento: j['evento']?.toString() ?? '',
      );
}

class Promocion {
  final int id;
  final int cantidadMin;
  final int? cantidadMax;
  final double porcentaje;
  final bool estado;
  Promocion({required this.id, required this.cantidadMin, this.cantidadMax, required this.porcentaje, required this.estado});
  factory Promocion.fromJson(Map<String, dynamic> j) => Promocion(
        id: (j['id'] as num?)?.toInt() ?? 0,
        cantidadMin: (j['cantidad_min'] as num?)?.toInt() ?? 1,
        cantidadMax: (j['cantidad_max'] as num?)?.toInt(),
        porcentaje: (j['porcentaje'] as num?)?.toDouble() ?? 0,
        estado: j['estado'] == true,
      );
}

class DetalleCompra {
  final int tipoEntradaId;
  final String tipo;
  final String evento;
  final int cantidad;
  final double precioUnitario;
  final double subtotal;
  DetalleCompra({required this.tipoEntradaId, required this.tipo, required this.evento, required this.cantidad, required this.precioUnitario, required this.subtotal});
  factory DetalleCompra.fromJson(Map<String, dynamic> j) => DetalleCompra(
        tipoEntradaId: (j['tipo_entrada_id'] as num?)?.toInt() ?? 0,
        tipo: j['tipo']?.toString() ?? '',
        evento: j['evento']?.toString() ?? '',
        cantidad: (j['cantidad'] as num?)?.toInt() ?? 0,
        precioUnitario: (j['precio_unitario'] as num?)?.toDouble() ?? 0,
        subtotal: (j['subtotal'] as num?)?.toDouble() ?? 0,
      );
}

class Factura {
  final int id;
  final int compraId;
  final String numero;
  final String fecha;
  final String estado;
  Factura({required this.id, required this.compraId, required this.numero, required this.fecha, required this.estado});
  factory Factura.fromJson(Map<String, dynamic> j) => Factura(
        id: (j['id'] as num?)?.toInt() ?? 0,
        compraId: (j['compra_id'] as num?)?.toInt() ?? 0,
        numero: j['numero']?.toString() ?? '',
        fecha: j['fecha']?.toString() ?? '',
        estado: j['estado']?.toString() ?? '',
      );
}

class Compra {
  final int id;
  final int usuarioId;
  final String solicitudId;
  final String fecha;
  final double subtotal;
  final double descuento;
  final double baseImponible;
  final double iva;
  final double total;
  final String estado;
  final List<DetalleCompra> detalles;
  final Factura? factura;
  Compra({required this.id, required this.usuarioId, required this.solicitudId, required this.fecha, required this.subtotal, required this.descuento, required this.baseImponible, required this.iva, required this.total, required this.estado, required this.detalles, this.factura});
  factory Compra.fromJson(Map<String, dynamic> j) => Compra(
        id: (j['id'] as num?)?.toInt() ?? 0,
        usuarioId: (j['usuario_id'] as num?)?.toInt() ?? 0,
        solicitudId: j['solicitud_id']?.toString() ?? '',
        fecha: j['fecha']?.toString() ?? '',
        subtotal: (j['subtotal'] as num?)?.toDouble() ?? 0,
        descuento: (j['descuento'] as num?)?.toDouble() ?? 0,
        baseImponible: (j['base_imponible'] as num?)?.toDouble() ?? 0,
        iva: (j['iva'] as num?)?.toDouble() ?? 0,
        total: (j['total'] as num?)?.toDouble() ?? 0,
        estado: j['estado']?.toString() ?? '',
        detalles: ((j['detalles'] as List?) ?? []).map((e) => DetalleCompra.fromJson(e as Map<String, dynamic>)).toList(),
        factura: j['factura'] != null ? Factura.fromJson(j['factura'] as Map<String, dynamic>) : null,
      );
}
