import '../data/repositories.dart';
import '../domain/repositories.dart';
import 'api_client.dart';
import 'session.dart';

/// Explicit DI container wiring ApiClient and all 5 domain repository ports.
class AppDependencies {
  final ApiClient apiClient;
  final UsuariosRepositoryPort usuarios;
  final EventosRepositoryPort eventos;
  final PromocionesRepositoryPort promociones;
  final FacturacionRepositoryPort facturacion;
  final ComprasRepositoryPort compras;

  AppDependencies._({
    required this.apiClient,
    required this.usuarios,
    required this.eventos,
    required this.promociones,
    required this.facturacion,
    required this.compras,
  });

  factory AppDependencies.fromSession(Session session) {
    final client = ApiClient(session);
    return AppDependencies._(
      apiClient: client,
      usuarios: UsuariosRepository(client),
      eventos: EventosRepository(client),
      promociones: PromocionesRepository(client),
      facturacion: FacturacionRepository(client),
      compras: ComprasRepository(client),
    );
  }

  factory AppDependencies.custom({
    required ApiClient apiClient,
    required UsuariosRepositoryPort usuarios,
    required EventosRepositoryPort eventos,
    required PromocionesRepositoryPort promociones,
    required FacturacionRepositoryPort facturacion,
    required ComprasRepositoryPort compras,
  }) {
    return AppDependencies._(
      apiClient: apiClient,
      usuarios: usuarios,
      eventos: eventos,
      promociones: promociones,
      facturacion: facturacion,
      compras: compras,
    );
  }
}
