USE fixture2030;

-- Comentario 1
INSERT INTO comentarios_por_partido
(partido_id, bucket_temporal, creado_en, comentario_id, usuario_id, contenido, estado_moderacion, likes)
VALUES
('M001', '20:00-20:05', '2030-06-13 20:01:00+0000',
11111111-1111-1111-1111-111111111111,
'U001', 'Gran inicio de partido', 'visible', 4);

INSERT INTO comentarios_por_usuario
(usuario_id, bucket_temporal, creado_en, comentario_id, partido_id, contenido, estado_moderacion, likes)
VALUES
('U001', '2030-06', '2030-06-13 20:01:00+0000',
11111111-1111-1111-1111-111111111111,
'M001', 'Gran inicio de partido', 'visible', 4);

-- Comentario 2
INSERT INTO comentarios_por_partido
(partido_id, bucket_temporal, creado_en, comentario_id, usuario_id, contenido, estado_moderacion, likes)
VALUES
('M001', '20:00-20:05', '2030-06-13 20:03:00+0000',
22222222-2222-2222-2222-222222222222,
'U002', 'Que jugada increible', 'visible', 7);

INSERT INTO comentarios_por_usuario
(usuario_id, bucket_temporal, creado_en, comentario_id, partido_id, contenido, estado_moderacion, likes)
VALUES
('U002', '2030-06', '2030-06-13 20:03:00+0000',
22222222-2222-2222-2222-222222222222,
'M001', 'Que jugada increible', 'visible', 7);

-- Comentario 3
INSERT INTO comentarios_por_partido
(partido_id, bucket_temporal, creado_en, comentario_id, usuario_id, contenido, estado_moderacion, likes)
VALUES
('M002', '18:00-18:05', '2030-06-14 18:02:00+0000',
33333333-3333-3333-3333-333333333333,
'U001', 'Buen partido hasta ahora', 'pendiente', 2);

INSERT INTO comentarios_por_usuario
(usuario_id, bucket_temporal, creado_en, comentario_id, partido_id, contenido, estado_moderacion, likes)
VALUES
('U001', '2030-06', '2030-06-14 18:02:00+0000',
33333333-3333-3333-3333-333333333333,
'M002', 'Buen partido hasta ahora', 'pendiente', 2);