-- Crear keyspace del módulo
CREATE KEYSPACE IF NOT EXISTS fixture2030
WITH replication = {
    'class': 'SimpleStrategy',
    'replication_factor': 1
};

--Usamos "SimpleStrategy" con factor de replicación 1 porque el --laboratorio tiene un solo nodo

USE fixture2030;

-- Tabla principal: PA1 y PA2
CREATE TABLE IF NOT EXISTS comentarios_por_partido (
    partido_id text,
    bucket_temporal text,
    creado_en timestamp,
    comentario_id uuid,
    usuario_id text,
    contenido text,
    estado_moderacion text,
    likes int,
    PRIMARY KEY ((partido_id, bucket_temporal), creado_en, comentario_id)
) WITH CLUSTERING ORDER BY (creado_en DESC, comentario_id ASC);

-- Tabla secundaria: PA3
CREATE TABLE IF NOT EXISTS comentarios_por_usuario (
    usuario_id text,
    bucket_temporal text,
    creado_en timestamp,
    comentario_id uuid,
    partido_id text,
    contenido text,
    estado_moderacion text,
    likes int,
    PRIMARY KEY ((usuario_id, bucket_temporal), creado_en, comentario_id)
) WITH CLUSTERING ORDER BY (creado_en DESC, comentario_id ASC);