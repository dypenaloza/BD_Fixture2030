from app.adapters import (
    neo4j_adapter,
    cassandra_adapter
)


def obtener_eventos(partido_id: str, limit: int):

    return neo4j_adapter.buscar_eventos(
        partido_id.upper(),
        limit
    )


def obtener_comentarios(
    partido_id: str,
    bucket_temporal: str,
    limit: int
):

    return cassandra_adapter.buscar_comentarios(
        partido_id.upper(),
        bucket_temporal,
        limit
    )