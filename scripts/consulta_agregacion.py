"""
RF11 - Consultas de agregación pertinentes para el módulo documental.
"""
import pprint

from db import get_db

pp = pprint.PrettyPrinter(indent=2, width=100)


def header(titulo, objetivo):
    print(f"\n{'='*90}\n{titulo}\nObjetivo: {objetivo}\n{'-'*90}")


def agregacion_1_plantel_consolidado(db):
    header(
        "Agregación 1: Plantel consolidado por selección ($lookup)",
        "Aunque el modelo usa REFERENCIA (equipoId) y no embebe a los jugadores "
        "dentro de la selección, un $lookup permite construir bajo demanda una "
        "vista consolidada 'equipo + plantel completo' sin necesidad de "
        "desnormalizar en la escritura. Se muestra para Argentina.",
    )
    pipeline = [
        {"$match": {"_id": "ARG"}},
        {
            "$lookup": {
                "from": "jugadores",
                "localField": "_id",
                "foreignField": "equipoId",
                "as": "plantel",
            }
        },
        {
            "$project": {
                "pais": 1,
                "entrenador": 1,
                "cantidadJugadores": {"$size": "$plantel"},
                "capitan": {
                    "$first": {
                        "$filter": {
                            "input": "$plantel",
                            "as": "j",
                            "cond": "$$j.capitan",
                        }
                    }
                },
            }
        },
    ]
    for doc in db.selecciones.aggregate(pipeline):
        pp.pprint(doc)


def agregacion_2_distribucion_por_posicion(db):
    header(
        "Agregación 2: Distribución global de jugadores por posición",
        "Obtener, para todo el torneo, la cantidad de jugadores por posición y "
        "el promedio de altura y peso de cada una. Útil para validar la "
        "composición de planteles cargados (control de calidad del dataset).",
    )
    pipeline = [
        {
            "$group": {
                "_id": "$posicion",
                "cantidad": {"$sum": 1},
                "alturaPromedio": {"$avg": "$altura"},
                "pesoPromedio": {"$avg": "$peso"},
            }
        },
        {"$sort": {"cantidad": -1}},
    ]
    for doc in db.jugadores.aggregate(pipeline):
        doc["alturaPromedio"] = round(doc["alturaPromedio"], 1)
        doc["pesoPromedio"] = round(doc["pesoPromedio"], 1)
        pp.pprint(doc)


def agregacion_3_ranking_promedio_por_grupo(db):
    header(
        "Agregación 3: Ranking FIFA promedio y cantidad de jugadores por grupo",
        "Combinar selecciones y jugadores ($lookup + $unwind + $group) para "
        "obtener, por cada grupo de fase inicial, el ranking promedio de sus "
        "4 selecciones y el total de jugadores convocados.",
    )
    pipeline = [
        {
            "$lookup": {
                "from": "jugadores",
                "localField": "_id",
                "foreignField": "equipoId",
                "as": "plantel",
            }
        },
        {
            "$group": {
                "_id": "$grupo",
                "equipos": {"$push": "$pais"},
                "rankingPromedio": {"$avg": "$ranking"},
                "totalJugadores": {"$sum": {"$size": "$plantel"}},
            }
        },
        {"$sort": {"_id": 1}},
    ]
    for doc in db.selecciones.aggregate(pipeline):
        doc["rankingPromedio"] = round(doc["rankingPromedio"], 1)
        pp.pprint(doc)


def main():
    db = get_db()
    agregacion_1_plantel_consolidado(db)
    agregacion_2_distribucion_por_posicion(db)
    agregacion_3_ranking_promedio_por_grupo(db)


if __name__ == "__main__":
    main()
