from contextlib import asynccontextmanager

from fastapi import (
    FastAPI,
    Request
)

import logging
import time
from uuid import uuid4

from fastapi.responses import JSONResponse, Response

from prometheus_client import (
    Counter,
    Histogram,
    generate_latest,
    CONTENT_TYPE_LATEST
)

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

# Métricas Prometheus (Hito 13).
#
# Se etiquetan por "fuente" (la misma clasificación por ruta que ya usa
# el logging de abajo), no solo por ruta/método: así una consulta PromQL
# puede agrupar por base de datos sin tener que conocer el mapeo
# ruta->fuente de memoria. Son métricas de la API (RED: rate, errors,
# duration), no del contenedor/infraestructura de cada base — esa
# distinción está documentada en docs/metricas_y_consultas.md.
PETICIONES_TOTAL = Counter(
    "fixture2030_http_requests_total",
    "Cantidad de requests HTTP atendidos por la API, por fuente/ruta/metodo/estado",
    ["fuente", "ruta", "metodo", "estado"]
)

DURACION_PETICION = Histogram(
    "fixture2030_http_request_duration_seconds",
    "Duracion de los requests HTTP atendidos por la API, en segundos, por fuente/ruta",
    ["fuente", "ruta"],
    buckets=(0.005, 0.01, 0.025, 0.05, 0.1, 0.25, 0.5, 1, 2.5, 5)
)


@app.get("/metrics", include_in_schema=False)
def metricas():
    # Endpoint de scraping de Prometheus. No requiere autenticacion en
    # este entorno de laboratorio (RNF6: no expone secretos, solo
    # contadores/histogramas agregados).
    return Response(
        generate_latest(),
        media_type=CONTENT_TYPE_LATEST
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

    if ruta_path != "/metrics":

        PETICIONES_TOTAL.labels(
            fuente=fuente,
            ruta=ruta_path,
            metodo=request.method,
            estado=str(response.status_code)
        ).inc()

        DURACION_PETICION.labels(
            fuente=fuente,
            ruta=ruta_path
        ).observe(duracion / 1000)

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