from contextlib import asynccontextmanager

from fastapi import (
    FastAPI,
    Request
)

import logging
import time
from uuid import uuid4

from fastapi.responses import JSONResponse

from app.adapters.mongo_adapter import (
    cerrar_cliente as cerrar_mongo
)

from app.adapters.neo4j_adapter import cerrar_driver

from app.adapters.cassandra_adapter import cerrar_conexion

from app.adapters.redis_adapter import (
    cerrar_cliente as cerrar_redis
)


# Configuración de logs

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("fixture2030.api")

from app.routes import (
    selecciones,
    partidos,
    sesiones,
    estadisticas,
    iris_partidos
)



@asynccontextmanager
async def lifespan(app: FastAPI):

    yield

    cerrar_mongo()
    cerrar_driver()
    cerrar_conexion()
    cerrar_redis()


app = FastAPI(
    title="Fixture 2030 API",
    description="API REST integrada del Fixture Mundial 2030",
    version="0.4.0",
    lifespan=lifespan
)

@app.middleware("http")
async def registrar_solicitud(request: Request, call_next):

    request_id = str(uuid4())
    inicio = time.perf_counter()

    try:
        response = await call_next(request)

    except Exception as exc:

        logger.error(
            "Error inesperado | request_id=%s | tipo=%s",
            request_id,
            type(exc).__name__
        )

        response = JSONResponse(
            status_code=500,
            content={
                "code": "INTERNAL_ERROR",
                "message": "Error interno del servidor"
            }
        )

    duracion = round(
        (time.perf_counter() - inicio) * 1000,
        2
    )

    ruta = request.scope.get("route")
    ruta_path = getattr(ruta, "path", request.url.path)

    # Identificar la fuente utilizada

    if ruta_path.startswith("/selecciones/"):
        fuente = "MongoDB"

    elif ruta_path.endswith("/eventos"):
        fuente = "Neo4j"

    elif ruta_path.endswith("/comentarios"):
        fuente = "Cassandra"

    elif ruta_path.startswith("/sesiones/"):
        fuente = "Redis"

    elif ruta_path.endswith("/estadisticas"):
        fuente = "InfluxDB"

    elif ruta_path.endswith("/detalle"):
        fuente = "IRIS"

    else:
        fuente = "API"

    logger.info(
        "RequestID=%s | Metodo=%s | Ruta=%s | "
        "Fuente=%s | Estado=%s | Duracion=%s ms",
        request_id,
        request.method,
        ruta_path,
        fuente,
        response.status_code,
        duracion
    )

    response.headers["X-Request-ID"] = request_id
    response.headers["X-Response-Time-ms"] = str(duracion)

    return response

# MongoDB
app.include_router(selecciones.router)

# Neo4j y Cassandra
app.include_router(partidos.router)

# Redis
app.include_router(sesiones.router)

# InfluxDB
app.include_router(estadisticas.router)

# InterSystems IRIS
app.include_router(iris_partidos.router)