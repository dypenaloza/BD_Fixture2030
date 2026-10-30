#!/usr/bin/env python3
"""
Chequeo nativo alternativo para cuando la CLI del producto (mongosh,
cypher-shell, cqlsh, redis-cli) no esta instalada en la máquina que
corre la evaluación. Usa los mismos drivers Python que ya requiere la
API del Hito 10 (pymongo, neo4j, cassandra-driver, redis-py) para
hacer una verificación de protocolo + contexto + lectura mínima
equivalente, en vez de dejar la capa nativa como "no evaluada" (SKIP).

No reemplaza la prueba con la CLI real cuando esta disponible: es un
complemento para no dejar RNF4 sin cubrir quien no tiene esas
herramientas instaladas (por ejemplo, en Windows sin WSL).

No imprime passwords ni tokens.

Uso: python3 chequeo_nativo_python.py <mongodb|neo4j|cassandra|redis>
Salida: una linea "OK <detalle>" o "FAIL <detalle>"; exit 0 si OK, 1 si FAIL.
"""

import os
import sys


def chequear_mongo():

    try:
        from pymongo import MongoClient
        from pymongo.errors import PyMongoError
    except ImportError:
        return False, "pymongo no esta instalado en este entorno Python"

    host = os.getenv("MONGO_HOST", "127.0.0.1")
    port = os.getenv("MONGO_PORT", "27017")
    database = os.getenv("MONGO_DATABASE", "fixture2030")
    user = os.getenv("MONGO_USER", "admin")
    password = os.getenv("MONGO_PASSWORD")

    if not password:
        return None, "definir MONGO_PASSWORD en el entorno local para este chequeo"

    uri = f"mongodb://{user}:{password}@{host}:{port}/?authSource=admin"

    try:
        cliente = MongoClient(
            uri,
            serverSelectionTimeoutMS=3000,
            connectTimeoutMS=3000
        )
        cliente.admin.command("ping")
        db = cliente[database]
        db.list_collection_names()
        cliente.close()
        return True, f"autenticacion y ping correctos en {database}"
    except PyMongoError as error:
        return False, f"{type(error).__name__}: fallo de conexion, autenticacion o contexto"


def chequear_neo4j():

    try:
        from neo4j import GraphDatabase
        from neo4j.exceptions import Neo4jError, ServiceUnavailable, AuthError
    except ImportError:
        return False, "el paquete neo4j no esta instalado en este entorno Python"

    host = os.getenv("NEO4J_HOST", "127.0.0.1")
    port = os.getenv("NEO4J_BOLT_PORT", "7687")
    user = os.getenv("NEO4J_USER", "neo4j")
    password = os.getenv("NEO4J_PASSWORD")
    database = os.getenv("NEO4J_DATABASE", "neo4j")

    if not password:
        return None, "definir NEO4J_PASSWORD en el entorno local para este chequeo"

    try:
        driver = GraphDatabase.driver(
            f"bolt://{host}:{port}",
            auth=(user, password),
            connection_timeout=3
        )
        with driver.session(database=database) as session:
            session.run("RETURN 1 AS connectivity").single()
        driver.close()
        return True, f"sesion Bolt y lectura minima correctas en {database}"
    except (ServiceUnavailable, AuthError, Neo4jError) as error:
        return False, f"{type(error).__name__}: fallo de Bolt, autenticacion o base"


def chequear_cassandra():

    try:
        from cassandra.cluster import Cluster, NoHostAvailable
        from cassandra import OperationTimedOut, Unavailable
    except ImportError:
        return False, "cassandra-driver no esta instalado en este entorno Python"

    host = os.getenv("CASSANDRA_HOST", "127.0.0.1")
    port = int(os.getenv("CASSANDRA_PORT", "9042"))
    keyspace = os.getenv("CASSANDRA_KEYSPACE", "fixture2030")

    try:
        cluster = Cluster([host], port=port, connect_timeout=3)
        session = cluster.connect(keyspace)
        session.execute(
            "SELECT comentario_id FROM comentarios_por_partido "
            "WHERE partido_id = %s AND bucket_temporal = %s LIMIT 1",
            ("M001", "20:00-20:05")
        )
        cluster.shutdown()
        return True, f"keyspace {keyspace} y lectura limitada correctos"
    except (NoHostAvailable, OperationTimedOut, Unavailable) as error:
        return False, f"{type(error).__name__}: no se pudo conectar o seleccionar el keyspace"


def chequear_redis():

    try:
        import redis
        from redis.exceptions import RedisError
    except ImportError:
        return False, "redis-py no esta instalado en este entorno Python"

    host = os.getenv("REDIS_HOST", "127.0.0.1")
    port = int(os.getenv("REDIS_PORT", "6379"))

    try:
        cliente = redis.Redis(
            host=host, port=port,
            socket_connect_timeout=3, socket_timeout=3
        )
        if cliente.ping():
            return True, "PING/PONG correctos"
        return False, "respuesta inesperada al PING"
    except RedisError as error:
        return False, f"{type(error).__name__}: no se obtuvo PONG"


CHEQUEOS = {
    "mongodb": chequear_mongo,
    "neo4j": chequear_neo4j,
    "cassandra": chequear_cassandra,
    "redis": chequear_redis
}


if __name__ == "__main__":

    if len(sys.argv) != 2 or sys.argv[1] not in CHEQUEOS:
        print(f"Uso: {sys.argv[0]} <{'|'.join(CHEQUEOS)}>", file=sys.stderr)
        sys.exit(2)

    resultado, detalle = CHEQUEOS[sys.argv[1]]()

    if resultado is None:
        print(f"SKIP {detalle}")
        sys.exit(3)
    elif resultado:
        print(f"OK {detalle}")
        sys.exit(0)
    else:
        print(f"FAIL {detalle}")
        sys.exit(1)
