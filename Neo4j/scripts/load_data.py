import os
import json
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv

# --------------------------------------------------
# CONFIGURACIÓN DE NEO4J (RNF8: credenciales por variables de entorno,
# nunca escritas directamente en el código)
# --------------------------------------------------

# Carpeta Neo4j/
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

USUARIO = os.environ.get("NEO4J_USER", "neo4j")
CLAVE = os.environ["NEO4J_PASSWORD"]
BOLT_PORT = os.environ.get("NEO4J_BOLT_PORT", "7687")
URI = f"bolt://localhost:{BOLT_PORT}"

ARCHIVO_EQUIPOS = BASE_DIR / "data" / "equipos.json"
ARCHIVO_JUGADORES = BASE_DIR / "data" / "jugadores.json"


# --------------------------------------------------
# LEER JSON
# --------------------------------------------------

def cargar_json(ruta):
    with open(ruta, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


equipos = cargar_json(ARCHIVO_EQUIPOS)
jugadores = cargar_json(ARCHIVO_JUGADORES)


# --------------------------------------------------
# CONEXIÓN
# --------------------------------------------------

driver = GraphDatabase.driver(
    URI,
    auth=(USUARIO, CLAVE)
)


# --------------------------------------------------
# CARGAR SELECCIONES
# --------------------------------------------------

def cargar_selecciones(tx, equipos):
    query = """
    UNWIND $equipos AS equipo

    MERGE (s:Seleccion {seleccionId: equipo._id})

    SET s.pais = equipo.pais,
        s.nombre = equipo.nombre,
        s.confederacion = equipo.confederacion,
        s.grupo = equipo.grupo,
        s.ranking = equipo.ranking,
        s.entrenador = equipo.entrenador,
        s.escudo = equipo.escudo,
        s.anfitrion = equipo.anfitrion
    """

    tx.run(query, equipos=equipos)


# --------------------------------------------------
# CARGAR JUGADORES Y RELACIONES
# --------------------------------------------------

def cargar_jugadores(tx, jugadores):
    query = """
    UNWIND $jugadores AS jugador

    MATCH (s:Seleccion {seleccionId: jugador.equipoId})

    MERGE (j:Jugador {jugadorId: jugador._id})

    SET j.nombre = jugador.nombre,
        j.apellido = jugador.apellido,
        j.posicion = jugador.posicion,
        j.dorsal = jugador.dorsal,
        j.fechaNacimiento = jugador.fechaNacimiento,
        j.altura = jugador.altura,
        j.peso = jugador.peso,
        j.club = jugador.club,
        j.capitan = jugador.capitan

    MERGE (j)-[:PERTENECE_A]->(s)
    """

    tx.run(query, jugadores=jugadores)


# --------------------------------------------------
# EJECUTAR CARGA
# --------------------------------------------------

with driver.session() as session:

    session.execute_write(cargar_selecciones, equipos)
    print("Selecciones cargadas.")

    session.execute_write(cargar_jugadores, jugadores)
    print("Jugadores y relaciones cargados.")


# --------------------------------------------------
# VERIFICACIÓN
# --------------------------------------------------

with driver.session() as session:

    cantidad_selecciones = session.run(
        "MATCH (s:Seleccion) RETURN count(s) AS total"
    ).single()["total"]

    cantidad_jugadores = session.run(
        "MATCH (j:Jugador) RETURN count(j) AS total"
    ).single()["total"]

    cantidad_relaciones = session.run(
        """
        MATCH (:Jugador)-[r:PERTENECE_A]->(:Seleccion)
        RETURN count(r) AS total
        """
    ).single()["total"]

    jugadores_sin_seleccion = session.run(
        """
        MATCH (j:Jugador)
        WHERE NOT (j)-[:PERTENECE_A]->(:Seleccion)
        RETURN count(j) AS total
        """
    ).single()["total"]


print()
print("===== RESULTADO DE LA CARGA =====")
print(f"Selecciones: {cantidad_selecciones}")
print(f"Jugadores: {cantidad_jugadores}")
print(f"Relaciones PERTENECE_A: {cantidad_relaciones}")
print(f"Jugadores sin selección: {jugadores_sin_seleccion}")

driver.close()