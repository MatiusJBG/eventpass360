# EventPass 360 — Fase 1 · Arquitectura Orientada a Servicios (SOA)

Sistema distribuido para administrar y comercializar entradas a conciertos, encuentros deportivos y conferencias, con facturación electrónica académica en XML y PDF por cada compra confirmada.

Entregable: **Morales_Matias_EventPass360**

---

## 1. Arquitectura

SOA: una bóveda central (Supabase PostgreSQL, 9 tablas) y 5 ventanillas independientes (APIs Flask) que se comunican solo por HTTP/JSON, más un mostrador digital (Flutter) que jamás toca la base de datos directamente.

| Componente | Puerto | Responsabilidad |
| :--- | :---: | :--- |
| 02_API_Compras | 5000 | Orquestador SAGA (cotiza → descuenta stock → emite factura → compensa si falla) |
| 03_API_Usuarios | 5001 | Auth JWT (bcrypt), usuarios y roles |
| 04_API_Eventos | 5002 | Categorías, eventos, tipos de entrada y stock atómico |
| 05_API_Promociones | 5003 | Promociones por tramos y cálculo dinámico (descuento + IVA 15%) |
| 06_API_Facturacion | 5004 | Emisión idempotente de factura XML + PDF (ReportLab) |
| 07_Aplicativo_Flutter | 8080 | Cliente y administrador (Web/Windows/Android) |

Cada API implementa Clean Architecture + SOLID (domain / application / infrastructure / presentation) y es 100% independiente: ninguna API importa código de otra (interoperabilidad solo HTTP REST). Flutter consume las 5 APIs vía http, sin conexión directa a Supabase.

---

## 2. Estructura

    Morales_Matias_EventPass360/
    ├── 01_BaseDatos/          esquema.sql + datos.sql + migrar.py
    ├── 02_API_Compras/        :5000 (SAGA)
    ├── 03_API_Usuarios/       :5001 (JWT + usuarios + roles)
    ├── 04_API_Eventos/        :5002 (categorías + eventos + entradas + stock)
    ├── 05_API_Promociones/    :5003 (promociones + cálculo)
    ├── 06_API_Facturacion/    :5004 (XML + PDF)
    ├── 07_Aplicativo_Flutter/ cliente + admin
    ├── 08_Facturas/           factura.xml + factura.pdf de muestra
    └── 09_Evidencias/         capturas de pantalla

---

## 3. Requisitos

- Python 3.13+ y paquetes: flask, flask-cors, psycopg[binary], PyJWT, python-dotenv, bcrypt, requests, reportlab.
- Supabase PostgreSQL (Transaction Pooler en puerto 6543).
- Flutter 3.47+ (para la app).

Instalar dependencias Python:

    python -m pip install flask flask-cors "psycopg[binary]" PyJWT python-dotenv bcrypt requests reportlab

---

## 4. Configuración de base de datos

1. Crear el proyecto en Supabase y copiar la DATABASE_URL del pooler IPv4 (puerto 6543).
2. Ejecutar la migración (crea las 9 tablas y datos semilla):

    $env:DATABASE_URL = "postgresql://USUARIO:CONTRASENA@HOST:6543/postgres"
    python 01_BaseDatos/migrar.py

Nota: psycopg abre conexiones con prepare_threshold=None (Supavisor en modo transacción).

---

## 5. Configuración de las APIs

En cada carpeta 02_API_Compras … 06_API_Facturacion, copiar .env.example a .env y completar:

    DATABASE_URL=postgresql://USUARIO:CONTRASENA@HOST:6543/postgres
    JWT_SECRET_KEY=un-secreto-largo-de-32-o-mas-caracteres

Para 02_API_Compras añadir además:

    URL_EVENTOS=http://localhost:5002
    URL_PROMOCIONES=http://localhost:5003
    URL_FACTURACION=http://localhost:5004

IMPORTANTE: el JWT_SECRET_KEY debe ser el mismo en las 5 APIs: Usuarios, Eventos, Promociones, Compras y Facturación.

---

## 6. Ejecución

Arrancar cada API en una consola independiente (desde su carpeta):

    cd 02_API_Compras ; python app.py
    cd 03_API_Usuarios ; python app.py
    cd 04_API_Eventos ; python app.py
    cd 05_API_Promociones ; python app.py
    cd 06_API_Facturacion ; python app.py

Compilar y servir la app Flutter:

    cd 07_Aplicativo_Flutter
    flutter pub get
    flutter build web
    python -m http.server 8080 -d build/web

Abrir http://localhost:8080

---

## 7. Credenciales de prueba

| Rol | Correo | Contraseña |
| :--- | :--- | :--- |
| Administrador | admin@eventpass360.com | Admin123* |
| Cliente | cliente@eventpass360.com | Cliente123* |

---

## 8. Caso de referencia oficial (verificado)

3 entradas "General" de Rock Fest (USD 25.00 c/u):

| Concepto | Valor |
| :--- | :--- |
| Subtotal | 75.00 |
| Descuento (5%, tramo 3–4) | -3.75 |
| Base imponible | 71.25 |
| IVA (15%) | 10.69 |
| Total | 81.94 |
| Stock | 100 → 97 |
| Factura | FAC-000001 |

Cálculo con Decimal y redondeo ROUND_HALF_UP.

---

## 9. Endpoints principales

- Compras: POST /api/compras/previsualizar · POST /api/compras · GET /api/compras · GET /api/compras/estadisticas · PATCH /api/compras/<id>/anular
- Usuarios: POST /api/login · POST /api/registro · GET|PUT /api/perfil · /api/usuarios · /api/roles
- Eventos: /api/categorias · /api/eventos · /api/tipos-entrada · POST /api/stock/cotizar|descontar|restaurar
- Promociones: /api/promociones · POST /api/promociones/calcular
- Facturación: POST /api/factura · GET /api/factura · GET /api/factura/<id>/xml|pdf · PATCH /api/factura/<id>/anular

---

## 10. Seguridad e integridad

- Hash de contraseñas bcrypt; JWT HS256; 401/403 estrictos.
- Registro público siempre como CLIENTE (no permite escalar a ADMIN).
- Precios consultados siempre del servidor (nunca se confía en precios del cliente).
- Stock atómico con CHECK (stock >= 0) y 409 Conflict.
- Idempotencia por solicitud_id (UNIQUE) y por compra_id en facturación.
- Compensación SAGA: si facturación falla, se restaura el stock y la compra queda FALLIDA (503).
- Promociones con validación anti-solapamiento de rangos activos.
