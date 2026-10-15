from datetime import datetime

from pydantic import BaseModel


# Neo4j

class EventoResponse(BaseModel):

    eventoId: str
    tipo: str | None = None
    minuto: int | None = None
    descripcion: str | None = None


class EventosPartidoResponse(BaseModel):

    partidoId: str
    cantidad: int
    eventos: list[EventoResponse]


# Cassandra

class ComentarioResponse(BaseModel):

    comentarioId: str
    usuarioId: str
    contenido: str
    creadoEn: datetime
    likes: int
    estadoModeracion: str


class ComentariosPartidoResponse(BaseModel):

    partidoId: str
    bucketTemporal: str
    cantidad: int
    comentarios: list[ComentarioResponse]


# Errores

class ErrorResponse(BaseModel):

    code: str
    message: str