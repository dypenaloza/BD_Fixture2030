from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.routes import (
    selecciones,
    partidos,
    sesiones,
    estadisticas
)

from app.adapters.mongo_adapter import (
    cerrar_cliente as cerrar_mongo
)

from app.adapters.neo4j_adapter import cerrar_driver

from app.adapters.cassandra_adapter import cerrar_conexion

from app.adapters.redis_adapter import (
    cerrar_cliente as cerrar_redis
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
    version="0.3.0",
    lifespan=lifespan
)


# MongoDB
app.include_router(selecciones.router)

# Neo4j y Cassandra
app.include_router(partidos.router)

# Redis
app.include_router(sesiones.router)

# InfluxDB
app.include_router(estadisticas.router)