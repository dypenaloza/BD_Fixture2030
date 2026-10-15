import re

from fastapi import APIRouter
from fastapi.responses import JSONResponse
from pymongo.errors import PyMongoError

from app.services import selecciones_service

from app.schemas.seleccion_schema import (
    SeleccionResponse,
    ErrorResponse
)


router = APIRouter(
    prefix="/selecciones",
    tags=["MongoDB"]
)


@router.get(
    "/{codigo}",
    response_model=SeleccionResponse,
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        503: {"model": ErrorResponse}
    }
)
def consultar_seleccion(codigo: str):

    # Validar el identificador
    if not re.fullmatch(r"[A-Za-z]{3}", codigo):

        return JSONResponse(
            status_code=400,
            content={
                "code": "VALIDATION_ERROR",
                "message": "El codigo debe tener 3 letras"
            }
        )

    try:

        seleccion = selecciones_service.obtener_seleccion(
            codigo
        )

    except PyMongoError:

        return JSONResponse(
            status_code=503,
            content={
                "code": "DATABASE_UNAVAILABLE",
                "message": "MongoDB no esta disponible"
            }
        )

    # Selección inexistente
    if seleccion is None:

        return JSONResponse(
            status_code=404,
            content={
                "code": "SELECCION_NOT_FOUND",
                "message": "La seleccion no existe"
            }
        )

    return seleccion