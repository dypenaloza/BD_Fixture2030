import re

from datetime import datetime, timezone, timedelta

import requests

from fastapi import APIRouter, Query
from fastapi.responses import JSONResponse

from app.services import estadisticas_service

from app.schemas.estadisticas_schema import (
    EstadisticasPartidoResponse,
    ErrorResponse
)


router = APIRouter(
    prefix="/partidos",
    tags=["InfluxDB"]
)


def error_http(estado, codigo, mensaje):

    return JSONResponse(
        status_code=estado,
        content={
            "code": codigo,
            "message": mensaje
        }
    )


def validar_fecha(valor):

    fecha = datetime.fromisoformat(
        valor.replace("Z", "+00:00")
    )

    if fecha.tzinfo is None:
        raise ValueError("Falta zona horaria")

    return fecha.astimezone(timezone.utc)


@router.get(
    "/{partido_id}/estadisticas",
    response_model=EstadisticasPartidoResponse,
    responses={
        400: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
        503: {"model": ErrorResponse}
    }
)
def consultar_estadisticas(

    partido_id: str,

    equipo_id: str | None = Query(None),

    desde: str | None = Query(None),

    hasta: str | None = Query(None),

    limit: str = Query("20")
):

    partido_id = partido_id.upper()

    if equipo_id is None:

        return error_http(
            400,
            "VALIDATION_ERROR",
            "Falta equipo_id"
        )

    equipo_id = equipo_id.upper()

    if (
        not re.fullmatch(r"[A-Z][0-9]{3}", partido_id)
        or not re.fullmatch(r"[A-Z]{3}", equipo_id)
    ):

        return error_http(
            400,
            "VALIDATION_ERROR",
            "Partido o equipo invalido"
        )

    try:

        limite = int(limit)

        if not 1 <= limite <= 100:
            raise ValueError()

        if desde is None or hasta is None:
            raise ValueError()

        fecha_desde = validar_fecha(desde)
        fecha_hasta = validar_fecha(hasta)

        if fecha_desde >= fecha_hasta:
            raise ValueError()

        if fecha_hasta - fecha_desde > timedelta(days=1):
            raise ValueError()

    except (ValueError, OverflowError):

        return error_http(
            400,
            "VALIDATION_ERROR",
            "Intervalo temporal o limite invalido"
        )

    # Normalizar las fechas a UTC
    desde_utc = fecha_desde.isoformat().replace(
        "+00:00", "Z"
    )

    hasta_utc = fecha_hasta.isoformat().replace(
        "+00:00", "Z"
    )

    try:

        estadisticas = (
            estadisticas_service.obtener_estadisticas(
                partido_id,
                equipo_id,
                desde_utc,
                hasta_utc,
                limite
            )
        )

    except (
        requests.RequestException,
        OSError,
        RuntimeError
    ):

        return error_http(
            503,
            "INFLUX_UNAVAILABLE",
            "InfluxDB no esta disponible o no se pudo consultar"
        )

    except ValueError:

        return error_http(
            502,
            "INVALID_DEPENDENCY_RESPONSE",
            "Respuesta invalida de InfluxDB"
        )

    return {
        "partidoId": partido_id,
        "equipoId": equipo_id,
        "cantidad": len(estadisticas),
        "estadisticas": estadisticas
    }