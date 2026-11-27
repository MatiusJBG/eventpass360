-- =============================================================
-- EventPass 360 (Fase 1 · SOA) — Esquema Canónico Unificado
-- 9 tablas + secuencia de facturación. 100% re-ejecutable.
-- =============================================================

DROP TABLE IF EXISTS entradas CASCADE;
DROP SEQUENCE IF EXISTS entrada_codigo_seq CASCADE;
DROP TABLE IF EXISTS facturas CASCADE;
DROP TABLE IF EXISTS detalle_compra CASCADE;
DROP TABLE IF EXISTS compras CASCADE;
DROP TABLE IF EXISTS promociones CASCADE;
DROP TABLE IF EXISTS tipos_entrada CASCADE;
DROP TABLE IF EXISTS eventos CASCADE;
DROP TABLE IF EXISTS categorias CASCADE;
DROP TABLE IF EXISTS usuarios CASCADE;
DROP TABLE IF EXISTS roles CASCADE;
DROP SEQUENCE IF EXISTS factura_numero_seq CASCADE;

-- 1. roles
CREATE TABLE roles (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(50) UNIQUE NOT NULL,
    estado      BOOLEAN NOT NULL DEFAULT TRUE,
    row_version INT NOT NULL DEFAULT 1 CHECK (row_version >= 1)
);

-- 2. usuarios
CREATE TABLE usuarios (
    id            SERIAL PRIMARY KEY,
    rol_id        INT NOT NULL REFERENCES roles(id) ON DELETE RESTRICT,
    nombre        VARCHAR(120) NOT NULL,
    correo        VARCHAR(150) UNIQUE NOT NULL,
    password_hash TEXT NOT NULL,
    estado        BOOLEAN NOT NULL DEFAULT TRUE,
    creado_en     TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    row_version   INT NOT NULL DEFAULT 1 CHECK (row_version >= 1)
);
CREATE INDEX idx_usuarios_rol_id ON usuarios(rol_id);

-- 3. categorias
CREATE TABLE categorias (
    id          SERIAL PRIMARY KEY,
    nombre      VARCHAR(100) UNIQUE NOT NULL,
    descripcion TEXT NOT NULL DEFAULT '',
    estado      BOOLEAN NOT NULL DEFAULT TRUE,
    row_version INT NOT NULL DEFAULT 1 CHECK (row_version >= 1)
);

-- 4. eventos
CREATE TABLE eventos (
    id           SERIAL PRIMARY KEY,
    categoria_id INT NOT NULL REFERENCES categorias(id) ON DELETE RESTRICT,
    nombre       VARCHAR(150) NOT NULL,
    descripcion  TEXT NOT NULL,
    lugar        VARCHAR(200) NOT NULL,
    fecha        TIMESTAMPTZ NOT NULL,
    imagen_url   TEXT NOT NULL,
    estado       BOOLEAN NOT NULL DEFAULT TRUE,
    row_version  INT NOT NULL DEFAULT 1 CHECK (row_version >= 1)
);
CREATE INDEX idx_eventos_categoria_id ON eventos(categoria_id);

-- 5. tipos_entrada
CREATE TABLE tipos_entrada (
    id          SERIAL PRIMARY KEY,
    evento_id   INT NOT NULL REFERENCES eventos(id) ON DELETE RESTRICT,
    tipo        VARCHAR(80) NOT NULL,
    precio      NUMERIC(10,2) NOT NULL CHECK (precio >= 0),
    stock       INT NOT NULL CHECK (stock >= 0),
    estado      BOOLEAN NOT NULL DEFAULT TRUE,
    row_version INT NOT NULL DEFAULT 1 CHECK (row_version >= 1),
    UNIQUE(evento_id, tipo)
);
CREATE INDEX idx_tipos_entrada_evento_id ON tipos_entrada(evento_id);

-- 6. promociones
CREATE TABLE promociones (
    id           SERIAL PRIMARY KEY,
    cantidad_min INT NOT NULL CHECK (cantidad_min >= 1),
    cantidad_max INT NULL CHECK (cantidad_max IS NULL OR cantidad_max >= cantidad_min),
    porcentaje   NUMERIC(5,2) NOT NULL CHECK (porcentaje >= 0 AND porcentaje <= 100),
    estado       BOOLEAN NOT NULL DEFAULT TRUE,
    row_version  INT NOT NULL DEFAULT 1 CHECK (row_version >= 1)
);

-- 7. compras
CREATE TABLE compras (
    id             SERIAL PRIMARY KEY,
    usuario_id     INT NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    solicitud_id   VARCHAR(100) UNIQUE NOT NULL,
    fecha          TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    subtotal       NUMERIC(10,2) NOT NULL,
    descuento      NUMERIC(10,2) NOT NULL,
    base_imponible NUMERIC(10,2) NOT NULL,
    iva            NUMERIC(10,2) NOT NULL,
    total          NUMERIC(10,2) NOT NULL,
    estado         VARCHAR(20) NOT NULL DEFAULT 'CONFIRMADA'
                   CHECK (estado IN ('PENDIENTE','CONFIRMADA','ANULADA','FALLIDA')),
    row_version    INT NOT NULL DEFAULT 1 CHECK (row_version >= 1)
);
CREATE INDEX idx_compras_usuario_id ON compras(usuario_id);

-- 8. detalle_compra
CREATE TABLE detalle_compra (
    id              SERIAL PRIMARY KEY,
    compra_id       INT NOT NULL REFERENCES compras(id) ON DELETE RESTRICT,
    tipo_entrada_id INT NOT NULL REFERENCES tipos_entrada(id) ON DELETE RESTRICT,
    cantidad        INT NOT NULL CHECK (cantidad > 0),
    precio_unitario NUMERIC(10,2) NOT NULL CHECK (precio_unitario >= 0),
    subtotal        NUMERIC(10,2) NOT NULL CHECK (subtotal >= 0)
);
CREATE INDEX idx_detalle_compra_compra_id ON detalle_compra(compra_id);
CREATE INDEX idx_detalle_compra_tipo_entrada_id ON detalle_compra(tipo_entrada_id);

-- 9. facturas
CREATE TABLE facturas (
    id          SERIAL PRIMARY KEY,
    compra_id   INT UNIQUE NOT NULL REFERENCES compras(id) ON DELETE RESTRICT,
    numero      VARCHAR(25) UNIQUE NOT NULL,
    fecha       TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    xml         TEXT NOT NULL,
    pdf_base64  TEXT NOT NULL,
    estado      VARCHAR(20) NOT NULL DEFAULT 'EMITIDA'
                CHECK (estado IN ('EMITIDA','ANULADA')),
    row_version INT NOT NULL DEFAULT 1 CHECK (row_version >= 1)
);

-- Secuencia para numeración inmutable FAC-000001
CREATE SEQUENCE factura_numero_seq START 1;

-- 10. entradas (Fase 2 · entradas electrónicas individuales)
CREATE TABLE entradas (
    id                SERIAL PRIMARY KEY,
    compra_id         INT NOT NULL REFERENCES compras(id) ON DELETE RESTRICT,
    detalle_compra_id INT NOT NULL REFERENCES detalle_compra(id) ON DELETE RESTRICT,
    evento_id         INT NOT NULL REFERENCES eventos(id) ON DELETE RESTRICT,
    codigo            VARCHAR(50) UNIQUE NOT NULL,
    estado            VARCHAR(20) NOT NULL DEFAULT 'DISPONIBLE'
                      CHECK (estado IN ('DISPONIBLE','UTILIZADA','ANULADA')),
    fecha_validacion  TIMESTAMPTZ NULL,
    row_version       INT NOT NULL DEFAULT 1 CHECK (row_version >= 1)
);
CREATE INDEX idx_entradas_compra_id ON entradas(compra_id);
CREATE INDEX idx_entradas_detalle_compra_id ON entradas(detalle_compra_id);
CREATE INDEX idx_entradas_evento_id ON entradas(evento_id);

-- Secuencia para códigos únicos EVT-000001
CREATE SEQUENCE entrada_codigo_seq START 1;
