"""
Tests de integracion: pegan por HTTP contra una instancia real de la
API (requieren las 6 bases levantadas con sus datos de carga y
`uvicorn app.main:app` corriendo).

No son unitarios: no hay mocks de ninguna base. Validan exactamente lo
que se verifico a mano durante el desarrollo de este hito (ver
docs/pruebas_y_evidencia.md), pero de forma repetible y multiplataforma
(complementa a tests/pruebas_integracion.ps1).

Ejecutar (con la API arriba en 127.0.0.1:8000):
    pytest tests/integration/ -v

Si la API no esta disponible en BASE_URL, todos los tests de este
archivo se saltean (no fallan) via el fixture `api_arriba`.
"""

import os

import pytest
import requests

BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


@pytest.fixture(scope="session", autouse=True)
def api_arriba():
    try:
        requests.get(f"{BASE_URL}/docs", timeout=2)
    except requests.RequestException:
        pytest.skip(
            f"API no disponible en {BASE_URL}: "
            "levantar las 6 bases y 'uvicorn app.main:app' antes de "
            "correr los tests de integracion."
        )


def get(path, **kwargs):
    return requests.get(f"{BASE_URL}{path}", timeout=10, **kwargs)


# ---------------------------------
# MongoDB
# ---------------------------------

def test_mongo_seleccion_existente():
    r = get("/selecciones/ARG")
    assert r.status_code == 200
    assert r.json()["id"] == "ARG"


def test_mongo_seleccion_inexistente():
    r = get("/selecciones/ZZZ")
    assert r.status_code == 404
    assert r.json()["code"] == "SELECCION_NOT_FOUND"


def test_mongo_codigo_invalido():
    r = get("/selecciones/1234")
    assert r.status_code == 400
    assert r.json()["code"] == "VALIDATION_ERROR"


# ---------------------------------
# Neo4j
# ---------------------------------

def test_neo4j_eventos_partido_existente():
    r = get("/partidos/P-A-1/eventos")
    assert r.status_code == 200
    body = r.json()
    assert body["partidoId"] == "P-A-1"
    assert body["cantidad"] == len(body["eventos"])


def test_neo4j_partido_id_invalido():
    # Formato real de Cassandra ("M001"), no de Neo4j: debe rechazarse.
    r = get("/partidos/M001/eventos")
    assert r.status_code == 400
    assert r.json()["code"] == "VALIDATION_ERROR"


# ---------------------------------
# Cassandra
# ---------------------------------

def test_cassandra_comentarios_con_datos():
    r = get(
        "/partidos/M001/comentarios",
        params={"bucket_temporal": "20:00-20:05", "limit": 10}
    )
    assert r.status_code == 200
    body = r.json()
    assert body["cantidad"] == len(body["comentarios"])


def test_cassandra_particion_sin_comentarios_responde_vacio():
    r = get(
        "/partidos/M001/comentarios",
        params={"bucket_temporal": "00:00-00:05", "limit": 10}
    )
    assert r.status_code == 200
    assert r.json()["comentarios"] == []


def test_cassandra_falta_bucket_temporal():
    r = get("/partidos/M001/comentarios")
    assert r.status_code == 400


# ---------------------------------
# Redis
# ---------------------------------

def test_redis_sesion_invalida_formato():
    r = get("/sesiones/123")
    assert r.status_code == 400
    assert r.json()["code"] == "VALIDATION_ERROR"


def test_redis_sesion_formato_valido_pero_inexistente():
    r = get("/sesiones/U99999")
    assert r.status_code == 404
    assert r.json()["code"] == "SESSION_NOT_FOUND"


# ---------------------------------
# InfluxDB
# ---------------------------------

def test_influx_estadisticas_con_datos():
    r = get(
        "/partidos/M001/estadisticas",
        params={
            "equipo_id": "ARG",
            "desde": "2030-10-08T08:00:00Z",
            "hasta": "2030-10-08T08:30:00Z",
            "limit": 10
        }
    )
    assert r.status_code == 200
    body = r.json()
    assert body["cantidad"] == len(body["estadisticas"])


def test_influx_intervalo_sin_observaciones_responde_vacio():
    r = get(
        "/partidos/M001/estadisticas",
        params={
            "equipo_id": "ARG",
            "desde": "2030-01-01T00:00:00Z",
            "hasta": "2030-01-01T01:00:00Z",
            "limit": 10
        }
    )
    assert r.status_code == 200
    assert r.json()["estadisticas"] == []


def test_influx_falta_equipo_id():
    r = get(
        "/partidos/M001/estadisticas",
        params={"desde": "2030-10-08T08:00:00Z", "hasta": "2030-10-08T08:30:00Z"}
    )
    assert r.status_code == 400


def test_influx_intervalo_mayor_a_un_dia():
    r = get(
        "/partidos/M001/estadisticas",
        params={
            "equipo_id": "ARG",
            "desde": "2030-10-01T00:00:00Z",
            "hasta": "2030-10-03T00:00:00Z",
            "limit": 10
        }
    )
    assert r.status_code == 400


# ---------------------------------
# IRIS
# ---------------------------------

def test_iris_detalle_partido_existente():
    r = get("/partidos/M004/detalle")
    assert r.status_code == 200
    body = r.json()
    assert body["codigo"] == "M004"
    assert body["cantidadEventos"] == len(body["eventos"])


def test_iris_codigo_invalido():
    r = get("/partidos/ABC-1/detalle")
    assert r.status_code == 400
    assert r.json()["code"] == "VALIDATION_ERROR"


def test_iris_partido_inexistente():
    r = get("/partidos/Z999/detalle")
    assert r.status_code == 404
    assert r.json()["code"] == "PARTIDO_NOT_FOUND"


# ---------------------------------
# Transversal
# ---------------------------------

def test_todas_las_respuestas_incluyen_request_id():
    r = get("/selecciones/ARG")
    assert "X-Request-ID" in r.headers


def test_todas_las_respuestas_incluyen_tiempo_de_respuesta():
    r = get("/selecciones/ARG")
    assert "X-Response-Time-ms" in r.headers
