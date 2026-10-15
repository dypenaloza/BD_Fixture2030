import re

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from redis.exceptions import RedisError

from app.services import sesiones_service

from app.schemas.sesiones_schema import (
    SesionResponse,
    ErrorResponse
)


router = APIRouter(
    prefix="/sesiones",
    tags=["Redis"]
)


@router.get(
    "/{usuario_id}",
    response_model=SesionResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        503: {"model": ErrorResponse}
    }
)
def consultar_sesion(usuario_id: str):

    usuario_id = usuario_id.upper()

    # Validar identificador
    if not re.fullmatch(r"U[0-9]{5}", usuario_id):

        return JSONResponse(
            status_code=400,
            content={
                "code": "VALIDATION_ERROR",
                "message": "Identificador de usuario invalido"
            }
        )

    try:

        sesion = sesiones_service.obtener_sesion(
            usuario_id
        )

    except RedisError:

        return JSONResponse(
            status_code=503,
            content={
                "code": "REDIS_UNAVAILABLE",
                "message": "Redis no esta disponible"
            }
        )

    if sesion is None:

        return JSONResponse(
            status_code=404,
            content={
                "code": "SESSION_NOT_FOUND",
                "message": "Sesion inexistente o expirada"
            }
        )

    return sesion