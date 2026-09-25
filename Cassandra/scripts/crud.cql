USE fixture2030;

-- CREATE
INSERT INTO comentarios_por_partido
(partido_id, bucket_temporal, creado_en, comentario_id, usuario_id, contenido, estado_moderacion, likes)
VALUES
('M001', '20:00-20:05', '2030-06-13 20:04:00+0000',
44444444-4444-4444-4444-444444444444,
'U003', 'Comentario de prueba CRUD', 'visible', 0);

INSERT INTO comentarios_por_usuario
(usuario_id, bucket_temporal, creado_en, comentario_id, partido_id, contenido, estado_moderacion, likes)
VALUES
('U003', '2030-06', '2030-06-13 20:04:00+0000',
44444444-4444-4444-4444-444444444444,
'M001', 'Comentario de prueba CRUD', 'visible', 0);


-- READ
SELECT *
FROM comentarios_por_partido
WHERE partido_id = 'M001'
  AND bucket_temporal = '20:00-20:05';


-- UPDATE
UPDATE comentarios_por_partido
SET likes = 10
WHERE partido_id = 'M001'
  AND bucket_temporal = '20:00-20:05'
  AND creado_en = '2030-06-13 20:04:00+0000'
  AND comentario_id = 44444444-4444-4444-4444-444444444444;

UPDATE comentarios_por_usuario
SET likes = 10
WHERE usuario_id = 'U003'
  AND bucket_temporal = '2030-06'
  AND creado_en = '2030-06-13 20:04:00+0000'
  AND comentario_id = 44444444-4444-4444-4444-444444444444;


-- DELETE
DELETE FROM comentarios_por_partido
WHERE partido_id = 'M001'
  AND bucket_temporal = '20:00-20:05'
  AND creado_en = '2030-06-13 20:04:00+0000'
  AND comentario_id = 44444444-4444-4444-4444-444444444444;

DELETE FROM comentarios_por_usuario
WHERE usuario_id = 'U003'
  AND bucket_temporal = '2030-06'
  AND creado_en = '2030-06-13 20:04:00+0000'
  AND comentario_id = 44444444-4444-4444-4444-444444444444;