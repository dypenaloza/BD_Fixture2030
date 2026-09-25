USE fixture2030;

-- PA1: últimos comentarios de un partido
SELECT creado_en, comentario_id, usuario_id, contenido, estado_moderacion, likes
FROM comentarios_por_partido
WHERE partido_id = 'M001'
  AND bucket_temporal = '20:00-20:05'
LIMIT 50;


-- PA2: comentarios de un partido dentro de una ventana temporal
SELECT creado_en, comentario_id, usuario_id, contenido, estado_moderacion, likes
FROM comentarios_por_partido
WHERE partido_id = 'M001'
  AND bucket_temporal = '20:00-20:05'
  AND creado_en >= '2030-06-13 20:00:00+0000'
  AND creado_en <  '2030-06-13 20:05:00+0000'
LIMIT 100;


-- PA3: historial de comentarios de un usuario
SELECT creado_en, comentario_id, partido_id, contenido, estado_moderacion, likes
FROM comentarios_por_usuario
WHERE usuario_id = 'U001'
  AND bucket_temporal = '2030-06'
LIMIT 50;