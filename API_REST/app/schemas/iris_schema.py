from pydantic import BaseModel


class EventoIRISResponse(BaseModel):

    id: str
    tipo: str
    minuto: int


class PartidoIRISResponse(BaseModel):

    id: str
    codigo: str
    estado: str
    cantidadEventos: int
    eventos: list[EventoIRISResponse]


class ErrorResponse(BaseModel):

    code: str
    message: str