from functools import lru_cache

from cassandra.cluster import Cluster

from app.config import settings


@lru_cache(maxsize=1)
def obtener_conexion():

    cluster = Cluster(
        [settings.CASSANDRA_HOST],
        port=settings.CASSANDRA_PORT,
        connect_timeout=5
    )

    try:

        session = cluster.connect(
            settings.CASSANDRA_KEYSPACE
        )

        consulta = session.prepare("""
            SELECT
                comentario_id,
                usuario_id,
                contenido,
                creado_en,
                likes,
                estado_moderacion

            FROM comentarios_por_partido

            WHERE partido_id = ?
              AND bucket_temporal = ?

            LIMIT ?
        """)

        return cluster, session, consulta

    except Exception:

        cluster.shutdown()
        raise


def buscar_comentarios(
    partido_id: str,
    bucket_temporal: str,
    limit: int = 20
):

    cluster, session, consulta = obtener_conexion()

    resultado = session.execute(
        consulta,
        (partido_id, bucket_temporal, limit),
        timeout=5
    )

    comentarios = []

    for fila in resultado:

        comentarios.append({
            "comentarioId": str(fila.comentario_id),
            "usuarioId": fila.usuario_id,
            "contenido": fila.contenido,
            "creadoEn": fila.creado_en.isoformat(),
            "likes": fila.likes,
            "estadoModeracion": fila.estado_moderacion
        })

    return comentarios


def cerrar_conexion():

    if obtener_conexion.cache_info().currsize:

        cluster, session, consulta = obtener_conexion()

        session.shutdown()
        cluster.shutdown()

        obtener_conexion.cache_clear()