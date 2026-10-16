#!/usr/bin/env python3
"""
Verifica que las 6 bases respondan ANTES de levantar la API, llamando
directamente a cada adaptador (sin pasar por HTTP). Usa IDs reales de
los datasets de carga de cada hito, asi que un "FAIL" por dato
inexistente es distinto de un "FAIL" por conexion: se reporta el
mensaje real de la excepcion para diferenciarlos.

Uso: python scripts/verificar_conectividad.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

resultados = []


def verificar(nombre, funcion):

    try:

        funcion()
        resultados.append((nombre, True, "OK"))

    except Exception as error:

        resultados.append(
            (nombre, False, f"{type(error).__name__}: {error}")
        )


def chequear_mongo():
    from app.adapters import mongo_adapter
    mongo_adapter.buscar_seleccion("ARG")


def chequear_neo4j():
    from app.services import partidos_service
    partidos_service.obtener_eventos("P-A-1", 1)


def chequear_cassandra():
    from app.services import partidos_service
    partidos_service.obtener_comentarios("M001", "20:00-20:05", 1)


def chequear_redis():
    from app.adapters import redis_adapter
    redis_adapter.buscar_sesion("U27961")


def chequear_influx():
    from app.adapters import influx_adapter
    influx_adapter.buscar_estadisticas(
        "M001", "ARG",
        "2030-10-08T08:00:00Z", "2030-10-08T08:30:00Z",
        1
    )


def chequear_iris():
    from app.adapters import iris_adapter
    iris_adapter.buscar_detalle_partido("M004")


if __name__ == "__main__":

    verificar("MongoDB", chequear_mongo)
    verificar("Neo4j", chequear_neo4j)
    verificar("Cassandra", chequear_cassandra)
    verificar("Redis", chequear_redis)
    verificar("InfluxDB", chequear_influx)
    verificar("IRIS", chequear_iris)

    ancho = max(len(nombre) for nombre, _, _ in resultados)

    todo_ok = True

    for nombre, ok, detalle in resultados:

        estado = "OK  " if ok else "FAIL"
        todo_ok = todo_ok and ok

        print(f"[{estado}] {nombre.ljust(ancho)}  {detalle}")

    sys.exit(0 if todo_ok else 1)
