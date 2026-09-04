"""
RF10 - Consultas de recuperación: identificación directa, filtrado,
proyección, ordenamiento y paginación.

Cada función imprime su objetivo funcional y los campos/condiciones usados,
seguido del resultado, para que quede como evidencia reproducible (RF13).
"""
import pprint

from db import get_db

pp = pprint.PrettyPrinter(indent=2, width=100)


def header(titulo, objetivo):
    print(f"\n{'='*90}\n{titulo}\nObjetivo: {objetivo}\n{'-'*90}")


def q1_recuperacion_por_id_seleccion(db):
    header(
        "Consulta 1: Recuperación por identificador — Selección",
        "Obtener una selección puntual a partir de su código FIFA (_id).",
    )
    doc = db.selecciones.find_one({"_id": "ARG"})
    pp.pprint(doc)


def q2_recuperacion_por_id_jugador(db):
    header(
        "Consulta 2: Recuperación por identificador — Jugador",
        "Obtener un jugador puntual a partir de su identificador "
        "'{equipo}-{dorsal}' (_id).",
    )
    doc = db.jugadores.find_one({"_id": "ARG-10"})
    pp.pprint(doc)


def q3_filtrado_selecciones_por_grupo(db):
    header(
        "Consulta 3: Recuperación filtrada — Selecciones de un grupo",
        "Listar las selecciones del Grupo A (condición de negocio: fase de grupos).",
    )
    cursor = db.selecciones.find({"grupo": "A"}, {"pais": 1, "ranking": 1, "grupo": 1})
    for doc in cursor:
        pp.pprint(doc)


def q4_filtrado_jugadores_equipo_posicion(db):
    header(
        "Consulta 4: Recuperación filtrada — Delanteros de un equipo",
        "Listar jugadores de Brasil (equipoId='BRA') con posicion='Delantero'.",
    )
    cursor = db.jugadores.find(
        {"equipoId": "BRA", "posicion": "Delantero"},
        {"nombre": 1, "apellido": 1, "dorsal": 1, "posicion": 1},
    )
    for doc in cursor:
        pp.pprint(doc)


def q5_filtrado_selecciones_anfitrionas(db):
    header(
        "Consulta 5: Recuperación filtrada — Selecciones anfitrionas",
        "Listar los 6 países sede del Mundial 2030, ordenados por ranking FIFA.",
    )
    cursor = db.selecciones.find({"anfitrion": True}).sort("ranking", 1)
    for doc in cursor:
        pp.pprint({"pais": doc["pais"], "ranking": doc["ranking"], "grupo": doc["grupo"]})


def q6_filtrado_jugadores_por_rango_altura(db):
    header(
        "Consulta 6: Recuperación filtrada — Rango de altura",
        "Listar arqueros con altura entre 195 y 200 cm (operador $gte/$lte).",
    )
    cursor = db.jugadores.find(
        {"posicion": "Arquero", "altura": {"$gte": 195, "$lte": 200}},
        {"nombre": 1, "apellido": 1, "altura": 1, "equipoId": 1},
    )
    for doc in cursor:
        pp.pprint(doc)


def q7_proyeccion(db):
    header(
        "Consulta 7: Proyección",
        "Devolver solo nombre, apellido y posición del plantel de España, "
        "excluyendo el resto de los atributos y el _id.",
    )
    cursor = db.jugadores.find(
        {"equipoId": "ESP"}, {"_id": 0, "nombre": 1, "apellido": 1, "posicion": 1}
    )
    for doc in cursor:
        pp.pprint(doc)


def q8_ordenamiento_y_paginacion(db):
    header(
        "Consulta 8: Ordenamiento y paginación",
        "Listar jugadores ordenados alfabéticamente por apellido, "
        "página 3 con 10 resultados por página (skip=20, limit=10). "
        "Útil para una interfaz de consulta tipo tabla/listado con scroll o "
        "paginado, evitando traer los 1500+ jugadores de una sola vez.",
    )
    page_size = 10
    page_number = 3  # 1-indexed
    skip = (page_number - 1) * page_size
    cursor = (
        db.jugadores.find({}, {"nombre": 1, "apellido": 1, "equipoId": 1})
        .sort("apellido", 1)
        .skip(skip)
        .limit(page_size)
    )
    for doc in cursor:
        pp.pprint(doc)


def main():
    db = get_db()
    q1_recuperacion_por_id_seleccion(db)
    q2_recuperacion_por_id_jugador(db)
    q3_filtrado_selecciones_por_grupo(db)
    q4_filtrado_jugadores_equipo_posicion(db)
    q5_filtrado_selecciones_anfitrionas(db)
    q6_filtrado_jugadores_por_rango_altura(db)
    q7_proyeccion(db)
    q8_ordenamiento_y_paginacion(db)


if __name__ == "__main__":
    main()
