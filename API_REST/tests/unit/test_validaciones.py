"""
Tests unitarios de las validaciones por expresion regular / parsing que
cada router aplica ANTES de tocar la base (RNF3/RF10). No requieren
ninguna base de datos levantada: son funciones puras.
"""

import pytest

from app.routes.partidos import (
    validar_partido_neo4j,
    validar_partido_cassandra,
    validar_limite
)
from app.routes.estadisticas import validar_fecha


# ---------------------------------
# Neo4j: partidoId = "P-<grupo|fase>-<numero>"
# ---------------------------------

@pytest.mark.parametrize("partido_id", [
    "P-A-1", "P-R32-6", "P-QF-2", "P-SF-1", "P-3P-1", "p-a-1"
])
def test_validar_partido_neo4j_acepta_formatos_reales(partido_id):
    assert validar_partido_neo4j(partido_id) is True


@pytest.mark.parametrize("partido_id", [
    "M001",        # formato real de Cassandra, no de Neo4j
    "P--1",
    "P-A-",
    "partido-1",
    ""
])
def test_validar_partido_neo4j_rechaza_formatos_invalidos(partido_id):
    assert validar_partido_neo4j(partido_id) is False


# ---------------------------------
# Cassandra: partido_id = "M###"
# ---------------------------------

@pytest.mark.parametrize("partido_id", ["M001", "A999", "Z000"])
def test_validar_partido_cassandra_acepta_formato_real(partido_id):
    assert validar_partido_cassandra(partido_id) is True


@pytest.mark.parametrize("partido_id", [
    "P-A-1",       # formato real de Neo4j, no de Cassandra
    "M01",
    "M0001",
    ""
])
def test_validar_partido_cassandra_rechaza_formatos_invalidos(partido_id):
    assert validar_partido_cassandra(partido_id) is False


# ---------------------------------
# limit compartido (Neo4j/Cassandra): entero 1-50
# ---------------------------------

@pytest.mark.parametrize("valor,esperado", [
    ("1", 1), ("50", 50), ("20", 20)
])
def test_validar_limite_acepta_rango_valido(valor, esperado):
    assert validar_limite(valor) == esperado


@pytest.mark.parametrize("valor", ["0", "51", "-1", "abc", ""])
def test_validar_limite_rechaza_fuera_de_rango_o_no_numerico(valor):
    assert validar_limite(valor) is None


# ---------------------------------
# InfluxDB: fechas ISO-8601 con zona horaria
# ---------------------------------

def test_validar_fecha_acepta_iso_con_zona_z():
    fecha = validar_fecha("2030-10-08T08:00:00Z")
    assert fecha.tzinfo is not None


def test_validar_fecha_acepta_iso_con_offset():
    fecha = validar_fecha("2030-10-08T08:00:00+00:00")
    assert fecha.tzinfo is not None


def test_validar_fecha_rechaza_sin_zona_horaria():
    with pytest.raises(ValueError):
        validar_fecha("2030-10-08T08:00:00")


def test_validar_fecha_rechaza_formato_no_iso():
    with pytest.raises(ValueError):
        validar_fecha("08/10/2030")
