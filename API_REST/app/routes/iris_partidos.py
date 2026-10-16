import re
import logging

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from app.services import iris_service

from app.adapters.iris_adapter import (
    IrisNoDisponible
)

from app.schemas.iris_schema import (
    PartidoIRISResponse,
    ErrorResponse
)


logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/partidos",
    tags=["IRIS"]
)


def error_http(estado, codigo, mensaje):

    return JSONResponse(
        status_code=estado,
        content={
            "code": codigo,
            "message": mensaje
        }
    )


@router.get(
    "/{codigo}/detalle",
    response_model=PartidoIRISResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
        503: {"model": ErrorResponse}
    }
)
def consultar_detalle_partido(codigo: str):

    codigo = codigo.upper()

    # Validar identificador
    if not re.fullmatch(r"[A-Z][0-9]{3}", codigo):

        return error_http(
            400,
            "VALIDATION_ERROR",
            "Codigo de partido invalido"
        )

    try:

        partido = iris_service.obtener_detalle_partido(
            codigo
        )

    except IrisNoDisponible:

        return error_http(
            503,
            "IRIS_UNAVAILABLE",
            "IRIS no esta disponible"
        )

    except Exception:

        logger.exception(
            "Error interno al consultar un partido en IRIS"
        )

        return error_http(
            500,
            "INTERNAL_ERROR",
            "No se pudo completar la consulta"
        )

    if partido is None:

        return error_http(
            404,
            "PARTIDO_NOT_FOUND",
            "El partido no existe en IRIS"
        )

    return partido