import re

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from neo4j.exceptions import (
    ServiceUnavailable,
    SessionExpired,
    AuthError
)

from cassandra import (
    OperationTimedOut,
    ReadTimeout,
    Unavailable
)

from cassandra.cluster import NoHostAvailable

from app.services import partidos_service

from app.schemas.partidos_schema import (
    EventosPartidoResponse,
    ComentariosPartidoResponse,
    ErrorResponse
)


router = APIRouter(
    prefix="/partidos"
)


def error_http(estado, codigo, mensaje):

    return JSONResponse(
        status_code=estado,
        content={
            "code": codigo,
            "message": mensaje
        }
    )


def validar_partido(partido_id):

    return bool(
        re.fullmatch(r"[A-Za-z][0-9]{3}", partido_id)
    )


def validar_limite(limit):

    try:

        numero = int(limit)

        if 1 <= numero <= 50:
            return numero

    except ValueError:
        pass

    return None


# ---------------------------------
# NEO4J
# ---------------------------------

@router.get(
    "/{partido_id}/eventos",
    tags=["Neo4j"],
    response_model=EventosPartidoResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        503: {"model": ErrorResponse}
    }
)
def consultar_eventos(
    partido_id: str,
    limit: str = Query(
        "20",
        description="Cantidad máxima: entero entre 1 y 50"
    )
):

    limite = validar_limite(limit)

    if not validar_partido(partido_id) or limite is None:

        return error_http(
            400,
            "VALIDATION_ERROR",
            "Identificador o limite invalido"
        )

    try:

        eventos = partidos_service.obtener_eventos(
            partido_id,
            limite
        )

    except (
        ServiceUnavailable,
        SessionExpired,
        AuthError,
        OSError,
        RuntimeError
    ):

        return error_http(
            503,
            "NEO4J_UNAVAILABLE",
            "Neo4j no esta disponible"
        )

    if eventos is None:

        return error_http(
            404,
            "PARTIDO_NOT_FOUND",
            "El partido no existe"
        )

    return {
        "partidoId": partido_id.upper(),
        "cantidad": len(eventos),
        "eventos": eventos
    }


# ---------------------------------
# CASSANDRA
# ---------------------------------

@router.get(
    "/{partido_id}/comentarios",
    tags=["Cassandra"],
    response_model=ComentariosPartidoResponse,
    responses={
        400: {"model": ErrorResponse},
        503: {"model": ErrorResponse}
    }
)
def consultar_comentarios(
    partido_id: str,
    bucket_temporal: str | None = Query(
        None,
        description="Bucket de la particion, por ejemplo 20:00-20:05"
    ),
    limit: str = Query(
        "20",
        description="Cantidad máxima: entero entre 1 y 50"
    )
):

    limite = validar_limite(limit)

    if (
        not validar_partido(partido_id)
        or not bucket_temporal
        or len(bucket_temporal) > 40
        or limite is None
    ):

        return error_http(
            400,
            "VALIDATION_ERROR",
            "Partido, bucket o limite invalido"
        )

    try:

        comentarios = partidos_service.obtener_comentarios(
            partido_id,
            bucket_temporal,
            limite
        )

    except (
        NoHostAvailable,
        OperationTimedOut,
        ReadTimeout,
        Unavailable
    ):

        return error_http(
            503,
            "CASSANDRA_UNAVAILABLE",
            "Cassandra no esta disponible"
        )

    return {
        "partidoId": partido_id.upper(),
        "bucketTemporal": bucket_temporal,
        "cantidad": len(comentarios),
        "comentarios": comentarios
    }