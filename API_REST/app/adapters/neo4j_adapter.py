from functools import lru_cache

from neo4j import GraphDatabase

from app.config import settings


@lru_cache(maxsize=1)
def obtener_driver():

    if not settings.NEO4J_PASSWORD:
        raise RuntimeError(
            "Falta configurar NEO4J_PASSWORD"
        )

    driver = GraphDatabase.driver(
        settings.NEO4J_URI,
        auth=(
            settings.NEO4J_USER,
            settings.NEO4J_PASSWORD
        ),
        connection_timeout=3
    )

    return driver


def buscar_eventos(partido_id: str, limit: int = 20):

    cypher = """
    MATCH (p:Partido {partidoId: $partido_id})

    OPTIONAL MATCH
        (e:Evento)-[:OCURRE_EN]->(p)

    RETURN
        p.partidoId AS partido_id,
        e.eventoId AS evento_id,
        e.tipo AS tipo,
        e.minuto AS minuto,
        e.descripcion AS descripcion

    ORDER BY minuto ASC
    LIMIT $limit
    """

    driver = obtener_driver()

    with driver.session(
        database=settings.NEO4J_DATABASE
    ) as session:

        resultado = session.run(
            cypher,
            partido_id=partido_id,
            limit=limit
        )

        registros = list(resultado)

    # No existe el partido
    if not registros:
        return None

    eventos = []

    for registro in registros:

        # El partido existe, pero no tiene eventos
        if registro["evento_id"] is None:
            continue

        eventos.append({
            "eventoId": registro["evento_id"],
            "tipo": registro["tipo"],
            "minuto": registro["minuto"],
            "descripcion": registro["descripcion"]
        })

    return eventos


def cerrar_driver():

    if obtener_driver.cache_info().currsize:

        obtener_driver().close()
        obtener_driver.cache_clear()