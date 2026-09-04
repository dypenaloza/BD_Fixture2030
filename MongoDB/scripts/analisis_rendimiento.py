"""
RF12 / RF13 - Análisis de rendimiento e índices.

Ejecuta la consulta crítica del módulo (jugadores de un equipo filtrados
por posición: la ruta de acceso más frecuente, ej. "ver delanteros del
plantel de un equipo") con `explain("executionStats")`:

  1. ANTES: se elimina temporalmente el índice compuesto
     'idx_equipoId_posicion' para forzar un COLLSCAN.
  2. DESPUÉS: se recrea el índice y se repite exactamente la misma consulta.

Se comparan `totalDocsExamined`, `executionTimeMillis` y el `stage` usado
por el planificador (COLLSCAN vs IXSCAN), evidenciando el efecto real del
índice sobre la consulta más crítica del módulo (RNF4).
"""
from db import get_db

CONSULTA_CRITICA = {"equipoId": "BRA", "posicion": "Delantero"}

# Para aislar el efecto real del índice se eliminan TODOS los índices
# relevantes para esta consulta (el simple sobre 'equipoId' y el compuesto
# 'equipoId+posicion'); de lo contrario Mongo igual podría usar el índice
# simple como acceso parcial y el escenario "antes" no reflejaría un
# COLLSCAN real sobre las 1500+ jugadores.
INDEXES_TO_TOGGLE = [
    ("idx_equipoId", [("equipoId", 1)]),
    ("idx_equipoId_posicion", [("equipoId", 1), ("posicion", 1)]),
]


def run_explain(db, label):
    print(f"\n--- {label} ---")
    explain = db.jugadores.find(CONSULTA_CRITICA).explain()
    stats = explain["executionStats"]
    winning_stage = explain["queryPlanner"]["winningPlan"]
    # El stage puede estar anidado (ej. FETCH -> IXSCAN); buscamos el nombre raíz.
    stage_chain = []
    node = winning_stage
    while node:
        stage_chain.append(node.get("stage"))
        node = node.get("inputStage")

    resumen = {
        "planStages": " -> ".join(stage_chain),
        "totalDocsExamined": stats["totalDocsExamined"],
        "totalKeysExamined": stats["totalKeysExamined"],
        "nReturned": stats["nReturned"],
        "executionTimeMillis": stats["executionTimeMillis"],
    }
    for k, v in resumen.items():
        print(f"  {k}: {v}")
    return resumen


def main():
    db = get_db()
    coleccion = db.jugadores
    total_docs = coleccion.count_documents({})
    print(f"Colección 'jugadores': {total_docs} documentos totales")
    print(f"Consulta crítica analizada: {CONSULTA_CRITICA}")

    print("\n== PASO 1: eliminar índices relevantes para simular escenario 'ANTES' ==")
    existentes = [i["name"] for i in coleccion.list_indexes()]
    for name, _ in INDEXES_TO_TOGGLE:
        if name in existentes:
            coleccion.drop_index(name)
            print(f"Índice '{name}' eliminado temporalmente.")
        else:
            print(f"Índice '{name}' no existía.")

    antes = run_explain(db, "ANTES de crear los índices (esperado: COLLSCAN)")

    print("\n== PASO 2: recrear los índices para el escenario 'DESPUÉS' ==")
    for name, keys in INDEXES_TO_TOGGLE:
        coleccion.create_index(keys, name=name)
        print(f"Índice '{name}' recreado.")

    despues = run_explain(db, "DESPUÉS de crear los índices (esperado: IXSCAN)")

    print("\n== Comparación ==")
    print(f"{'Métrica':<25}{'Antes':<20}{'Después':<20}")
    for key in antes:
        print(f"{key:<25}{str(antes[key]):<20}{str(despues[key]):<20}")

    reduccion = antes["totalDocsExamined"] - despues["totalDocsExamined"]
    print(
        f"\nEl índice reduce los documentos examinados de "
        f"{antes['totalDocsExamined']} a {despues['totalDocsExamined']} "
        f"(-{reduccion} documentos), pasando de un recorrido completo de "
        f"la colección (COLLSCAN) a un acceso directo por índice (IXSCAN)."
    )


if __name__ == "__main__":
    main()
