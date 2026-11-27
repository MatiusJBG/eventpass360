-- =============================================================
-- EventPass 360 — Datos semilla (Sección 4 y 7 del PDF oficial)
-- =============================================================

-- Roles
INSERT INTO roles (nombre) VALUES ('ADMIN'), ('CLIENTE');

-- Usuarios (hash bcrypt real)
INSERT INTO usuarios (rol_id, nombre, correo, password_hash) VALUES
((SELECT id FROM roles WHERE nombre='ADMIN'), 'Administrador', 'admin@eventpass360.com',
 '$2b$12$dN9u1CEa4ABKtyos8OSMJ.No/xw//S4GfdW3dQViw25qgFl90DDxK'),
((SELECT id FROM roles WHERE nombre='CLIENTE'), 'Cliente de prueba', 'cliente@eventpass360.com',
 '$2b$12$dtC3KrFHtPAV1h36pLpw2eC9FBnZbfHyk.ZsAVWY54dhaIRPwGgIq'),
((SELECT id FROM roles WHERE nombre='CLIENTE'), 'María López', 'maria@eventpass360.com',
 '$2b$12$dtC3KrFHtPAV1h36pLpw2eC9FBnZbfHyk.ZsAVWY54dhaIRPwGgIq'),
((SELECT id FROM roles WHERE nombre='CLIENTE'), 'Juan Pérez', 'juan@eventpass360.com',
 '$2b$12$dtC3KrFHtPAV1h36pLpw2eC9FBnZbfHyk.ZsAVWY54dhaIRPwGgIq');

-- Categorías
INSERT INTO categorias (nombre, descripcion) VALUES
('Conciertos', 'Eventos musicales en vivo'),
('Conferencias', 'Charlas y congresos académicos'),
('Deportes', 'Encuentros deportivos');

-- Eventos
INSERT INTO eventos (categoria_id, nombre, descripcion, lugar, fecha, imagen_url) VALUES
((SELECT id FROM categorias WHERE nombre='Conciertos'), 'Rock Fest',
 'Festival de rock con las mejores bandas en vivo', 'Estadio Olímpico Atahualpa',
 '2026-12-20 19:00:00-05', 'https://placehold.co/600x400/1e1b4b/ffffff?text=Rock+Fest'),
((SELECT id FROM categorias WHERE nombre='Conferencias'), 'Congreso Tecnológico',
 'Congreso de tecnología, innovación y transformación digital', 'Centro de Convenciones Quito',
 '2026-12-15 09:00:00-05', 'https://placehold.co/600x400/065f46/ffffff?text=Congreso+Tecnologico'),
((SELECT id FROM categorias WHERE nombre='Deportes'), 'Campeonato Deportivo',
 'Campeonato de fútbol interuniversitario', 'Coliseo Rumiñahui',
 '2026-12-28 15:00:00-05', 'https://placehold.co/600x400/b91c1c/ffffff?text=Campeonato+Deportivo');

-- Tipos de entrada (Sección 4 del PDF)
INSERT INTO tipos_entrada (evento_id, tipo, precio, stock) VALUES
((SELECT id FROM eventos WHERE nombre='Rock Fest'), 'General', 25.00, 100),
((SELECT id FROM eventos WHERE nombre='Rock Fest'), 'VIP', 60.00, 30),
((SELECT id FROM eventos WHERE nombre='Congreso Tecnológico'), 'General', 15.00, 80),
((SELECT id FROM eventos WHERE nombre='Congreso Tecnológico'), 'VIP', 35.00, 20),
((SELECT id FROM eventos WHERE nombre='Campeonato Deportivo'), 'General', 10.00, 150),
((SELECT id FROM eventos WHERE nombre='Campeonato Deportivo'), 'VIP', 40.00, 50);

-- Promociones por tramos de cantidad (Sección 7 del PDF)
INSERT INTO promociones (cantidad_min, cantidad_max, porcentaje, estado) VALUES
(1, 2, 0.00, TRUE),
(3, 4, 5.00, TRUE),
(5, 9, 10.00, TRUE),
(10, NULL, 15.00, TRUE);
