"""
RF9 - Operaciones de inserción y actualización de equipos y jugadores.

Notas de diseño de esta demo:
  - Para 'jugadores' se inserta y actualiza un jugador adicional del plantel
    de Uruguay (una convocatoria extra / lesión de último momento). Queda
    persistido: no rompe ningún requisito (RNF2 exige "al menos" 1000).
  - Para 'selecciones' se inserta un equipo de PRUEBA ("ZZZ"), se actualiza
    y finalmente se elimina al final de la demo, para no alterar el
    requisito estricto de "64 equipos" (RF4) en el estado final de la base.
"""
from datetime import datetime

from pymongo.errors import DuplicateKeyError, WriteError

from db import get_db


def demo_insert_update_jugador(db):
    print("\n" + "=" * 90)
    print("Operación 1: Insertar un nuevo jugador (convocatoria adicional)")
    print("-" * 90)
    nuevo_jugador = {
        "_id": "URU-99",
        "nombre": "Bruno",
        "apellido": "Delgado",
        "equipoId": "URU",
        "posicion": "Delantero",
        "dorsal": 99,
        "fechaNacimiento": datetime(2001, 3, 14),
        "altura": 181,
        "peso": 76.4,
        "club": "Montevideo FC",
        "capitan": False,
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow(),
    }
    try:
        db.jugadores.insert_one(nuevo_jugador)
        print("Insertado correctamente:", nuevo_jugador["_id"])
    except DuplicateKeyError:
        print("El jugador ya existía (ejecución repetida), no se duplica.")
    except WriteError as e:
        print("Rechazado por validación $jsonSchema:", e.details)

    print("\nOperación 2: Actualizar información del jugador insertado")
    print("-" * 90)
    result = db.jugadores.update_one(
        {"_id": "URU-99"},
        {"$set": {"club": "Peñarol", "peso": 77.0, "updatedAt": datetime.utcnow()}},
    )
    print(f"matched={result.matched_count} modified={result.modified_count}")
    print(db.jugadores.find_one({"_id": "URU-99"}))


def demo_insert_update_seleccion(db):
    print("\n" + "=" * 90)
    print("Operación 3: Insertar un equipo de prueba (valida el esquema)")
    print("-" * 90)
    equipo_prueba = {
        "_id": "ZZZ",
        "pais": "País de Prueba",
        "nombre": "Selección de Prueba",
        "confederacion": "UEFA",
        "grupo": "A",
        "ranking": 999,
        "entrenador": "DT de Prueba",
        "anfitrion": False,
        "createdAt": datetime.utcnow(),
        "updatedAt": datetime.utcnow(),
    }
    db.selecciones.insert_one(equipo_prueba)
    print("Insertado correctamente:", equipo_prueba["_id"])

    print("\nOperación 4: Actualizar información del equipo de prueba")
    print("-" * 90)
    result = db.selecciones.update_one(
        {"_id": "ZZZ"}, {"$set": {"ranking": 500, "updatedAt": datetime.utcnow()}}
    )
    print(f"matched={result.matched_count} modified={result.modified_count}")
    print(db.selecciones.find_one({"_id": "ZZZ"}))

    print("\nOperación 5: Intento de inserción inválida (violación de validador)")
    print("-" * 90)
    try:
        db.selecciones.insert_one({"_id": "zz", "pais": "Inválido"})
    except WriteError as e:
        print("Rechazado correctamente por $jsonSchema (esperado). Detalle:")
        print(e.details)

    print("\nLimpieza: se elimina el equipo de prueba para preservar RF4 (64 equipos exactos)")
    print("-" * 90)
    result = db.selecciones.delete_one({"_id": "ZZZ"})
    print(f"deleted_count={result.deleted_count}")


def main():
    db = get_db()
    demo_insert_update_jugador(db)
    demo_insert_update_seleccion(db)

    print("\n" + "=" * 90)
    print("Estado final de conteos tras las operaciones de demostración:")
    print(f"  selecciones: {db.selecciones.count_documents({})}")
    print(f"  jugadores  : {db.jugadores.count_documents({})}")


if __name__ == "__main__":
    main()
