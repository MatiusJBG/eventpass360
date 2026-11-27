# EventPass 360 — Aplicativo Flutter (Fase 1 · SOA)

Aplicación cliente y panel administrativo de **EventPass 360** construida en Flutter con arquitectura limpia por capas (`domain/`, `data/`, `core/`, `ui/`) y consumo exclusivo por HTTP REST hacia los cinco microservicios del ecosistema.

## Microservicios consumidos

| Servicio | Puerto local | Propósito |
| --- | --- | --- |
| `02_API_Compras` | `http://localhost:5000` | Orquestador SAGA de compras, previsualización, historial, estadísticas y anulación |
| `03_API_Usuarios` | `http://localhost:5001` | Autenticación JWT, perfil propio, CRUD de usuarios y roles |
| `04_API_Eventos` | `http://localhost:5002` | Catálogo de categorías, eventos y tipos de entrada con stock |
| `05_API_Promociones` | `http://localhost:5003` | Reglas de descuento por volumen y cálculo de IVA (15%) |
| `06_API_Facturacion` | `http://localhost:5004` | Consulta y descarga autenticada (Bearer JWT) de facturas XML y PDF |

## Estructura del proyecto

- `lib/domain/`: Entidades inmutables puras (`entities.dart`), puertos de repositorio (`repositories.dart`) y estado algebraico Dart 3 (`ui_state.dart`).
- `lib/data/`: Modelos tipados con `fromJson`/`toJson` (`models.dart`) e implementaciones HTTP (`repositories.dart`).
- `lib/core/`: Cliente HTTP con timeout y traducción de errores (`api_client.dart`), inyección de dependencias (`app_dependencies.dart`), sesión (`session.dart`), tema (`theme.dart`), formateo (`format.dart`) y descargador multiplataforma Web/VM (`file_downloader.dart`).
- `lib/ui/`: Pantallas de autenticación, flujo Cliente (`Catálogo`, `Carrito`, `Historial y Facturas`, `Perfil`), panel Administrador (`Dashboard`, `Catálogos CRUD`, `Ventas y Facturas`) y componentes reutilizables en `lib/ui/core/widgets/`.

## Comandos de verificación

```bash
flutter pub get
flutter analyze
flutter test
flutter build web
```
