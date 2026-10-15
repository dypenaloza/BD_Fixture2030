from pydantic import BaseModel


class SesionResponse(BaseModel):

    usuarioId: str
    nombre: str | None = None
    rol: str | None = None
    ultimoAcceso: str | None = None
    partidoSiguiendo: str | None = None
    ttlSegundos: int


class ErrorResponse(BaseModel):

    code: str
    message: str