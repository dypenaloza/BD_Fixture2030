from datetime import datetime

from pydantic import BaseModel


class EstadisticaResponse(BaseModel):

    time: datetime
    equipo_id: str
    posesion_pct: float | None = None
    pases: int | None = None
    tiros: int | None = None


class EstadisticasPartidoResponse(BaseModel):

    partidoId: str
    equipoId: str
    cantidad: int
    estadisticas: list[EstadisticaResponse]


class ErrorResponse(BaseModel):

    code: str
    message: str