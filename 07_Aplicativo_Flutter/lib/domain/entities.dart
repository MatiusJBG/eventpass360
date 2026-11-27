/// Pure immutable domain entities for EventPass 360.
/// Contains zero JSON serialization or transport logic.
library;

class Usuario {
  final int id;
  final int rolId;
  final String rol;
  final String nombre;
  final String correo;
  final bool estado;

  const Usuario({
    required this.id,
    required this.rolId,
    required this.rol,
    required this.nombre,
    required this.correo,
    required this.estado,
  });
}

class Rol {
  final int id;
  final String nombre;
  final bool estado;

  const Rol({
    required this.id,
    required this.nombre,
    required this.estado,
  });
}

class Categoria {
  final int id;
  final String nombre;
  final String descripcion;
  final bool estado;

  const Categoria({
    required this.id,
    required this.nombre,
    required this.descripcion,
    required this.estado,
  });
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

  const Evento({
    required this.id,
    required this.categoriaId,
    required this.nombre,
    required this.descripcion,
    required this.lugar,
    required this.fecha,
    required this.imagenUrl,
    required this.estado,
    required this.categoria,
  });
}

class TipoEntrada {
  final int id;
  final int eventoId;
  final String tipo;
  final double precio;
  final int stock;
  final bool estado;
  final String evento;

  const TipoEntrada({
    required this.id,
    required this.eventoId,
    required this.tipo,
    required this.precio,
    required this.stock,
    required this.estado,
    required this.evento,
  });
}

class Promocion {
  final int id;
  final int cantidadMin;
  final int? cantidadMax;
  final double porcentaje;
  final bool estado;

  const Promocion({
    required this.id,
    required this.cantidadMin,
    this.cantidadMax,
    required this.porcentaje,
    required this.estado,
  });

  bool aplicaPara(int cantidad) {
    if (!estado) return false;
    if (cantidad < cantidadMin) return false;
    if (cantidadMax != null && cantidad > cantidadMax!) return false;
    return true;
  }
}

class DetalleCompra {
  final int tipoEntradaId;
  final String tipo;
  final String evento;
  final int cantidad;
  final double precioUnitario;
  final double subtotal;

  const DetalleCompra({
    required this.tipoEntradaId,
    required this.tipo,
    required this.evento,
    required this.cantidad,
    required this.precioUnitario,
    required this.subtotal,
  });
}

class Factura {
  final int id;
  final int compraId;
  final String numero;
  final String fecha;
  final String estado;

  const Factura({
    required this.id,
    required this.compraId,
    required this.numero,
    required this.fecha,
    required this.estado,
  });
}

class Compra {
  final int id;
  final int usuarioId;
  final String usuarioNombre;
  final String usuarioCorreo;
  final String solicitudId;
  final String fecha;
  final double subtotal;
  final double descuento;
  final double baseImponible;
  final double iva;
  final double total;
  final String estado;
  final int? facturaId;
  final String? facturaNumero;
  final String? facturaEstado;
  final List<DetalleCompra> detalles;

  const Compra({
    required this.id,
    required this.usuarioId,
    required this.usuarioNombre,
    required this.usuarioCorreo,
    required this.solicitudId,
    required this.fecha,
    required this.subtotal,
    required this.descuento,
    required this.baseImponible,
    required this.iva,
    required this.total,
    required this.estado,
    this.facturaId,
    this.facturaNumero,
    this.facturaEstado,
    required this.detalles,
  });
}

class ResumenCompra {
  final int cantidadTotal;
  final double subtotal;
  final double porcentajeDescuento;
  final double descuento;
  final double baseImponible;
  final double iva;
  final double total;

  const ResumenCompra({
    required this.cantidadTotal,
    required this.subtotal,
    required this.porcentajeDescuento,
    required this.descuento,
    required this.baseImponible,
    required this.iva,
    required this.total,
  });
}

class Estadisticas {
  final int totalCompras;
  final double ingresosTotales;
  final int entradasVendidas;
  final Map<String, int> porEstado;

  const Estadisticas({
    required this.totalCompras,
    required this.ingresosTotales,
    required this.entradasVendidas,
    required this.porEstado,
  });
}
