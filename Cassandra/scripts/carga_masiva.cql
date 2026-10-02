-- =============================================================================
-- Carga masiva reproducible (RF11, RNF3) — Comentarios Masivos del Fixture 2030
--
-- Este script registra el comando COPY exacto usado para medir el
-- rendimiento documentado en docs/rendimiento.md. Antes de ejecutarlo:
--
--   1. Generar los CSV reproducibles (semilla fija, ver scripts/generar_comentarios.py):
--        python3 scripts/generar_comentarios.py
--      Esto escribe data/comentarios_por_partido.csv y
--      data/comentarios_por_usuario.csv (montados en el contenedor en /data,
--      ver docker-compose.yml).
--
--   2. Ejecutar este archivo con cqlsh:
--        docker exec -i fixture2030-cassandra cqlsh -f /scripts/carga_masiva.cql
--
-- Nota de idempotencia: comentario_id es un UUID determinístico (generado a
-- partir del índice de la fila, ver generar_comentarios.py), por lo que
-- volver a correr este COPY sobre el mismo CSV sobrescribe cada fila con el
-- mismo valor en lugar de duplicarla. Para una carga "desde cero" totalmente
-- limpia, truncar antes:
--
--   TRUNCATE fixture2030.comentarios_por_partido;
--   TRUNCATE fixture2030.comentarios_por_usuario;
-- =============================================================================

USE fixture2030;

COPY comentarios_por_partido (partido_id, bucket_temporal, creado_en, comentario_id, usuario_id, contenido, estado_moderacion, likes)
FROM '/data/comentarios_por_partido.csv'
WITH HEADER = TRUE;

COPY comentarios_por_usuario (usuario_id, bucket_temporal, creado_en, comentario_id, partido_id, contenido, estado_moderacion, likes)
FROM '/data/comentarios_por_usuario.csv'
WITH HEADER = TRUE;
