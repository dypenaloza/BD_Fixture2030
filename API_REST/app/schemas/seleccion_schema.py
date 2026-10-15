from pydantic import BaseModel


class SeleccionResponse(BaseModel):

    id: str
    pais: str
    nombre: str
    confederacion: str
    grupo: str
    ranking: int
    anfitrion: bool


class ErrorResponse(BaseModel):

    code: str
    message: str