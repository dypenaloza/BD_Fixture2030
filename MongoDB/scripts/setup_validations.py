"""
RF7 - Reglas de validación para los atributos críticos de cada documento.
RF12 - Creación de índices para las consultas de mayor frecuencia/criticidad.

Este script es idempotente: puede ejecutarse cualquier cantidad de veces.
  - Si la colección no existe, se crea con el validador $jsonSchema.
  - Si ya existe, se actualiza el validador con `collMod` (no se duplica
    ni se pierde información).
  - `create_index` es idempotente por naturaleza en MongoDB: si el índice
    ya existe con la misma definición, no hace nada.
"""
from pymongo import ASCENDING
from pymongo.errors import OperationFailure

from db import get_db

SELECCIONES_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "title": "Validación de documento Selección",
        "required": [
            "_id",
            "pais",
            "nombre",
            "confederacion",
            "grupo",
            "ranking",
            "entrenador",
            "anfitrion",
        ],
        "properties": {
            "_id": {
                "bsonType": "string",
                "pattern": "^[A-Z]{3}$",
                "description": "Código FIFA de 3 letras. Requerido, identificador natural.",
            },
            "pais": {
                "bsonType": "string",
                "minLength": 1,
                "description": "Texto no vacío. Requerido.",
            },
            "nombre": {
                "bsonType": "string",
                "minLength": 1,
                "description": "Texto no vacío. Requerido.",
            },
            "confederacion": {
                "enum": ["CONMEBOL", "UEFA", "CAF", "AFC", "CONCACAF", "OFC"],
                "description": "Debe ser una confederación FIFA válida. Requerido.",
            },
            "grupo": {
                "bsonType": "string",
                "pattern": "^[A-P]$",
                "description": "Grupo de fase inicial (A-P para 64 equipos). Requerido.",
            },
            "ranking": {
                "bsonType": "int",
                "minimum": 1,
                "description": "Entero mayor a 0. Requerido.",
            },
            "entrenador": {
                "bsonType": "string",
                "minLength": 1,
                "description": "Texto no vacío. Requerido.",
            },
            "escudo": {
                "bsonType": "string",
                "description": "URL opcional al escudo del equipo.",
            },
            "anfitrion": {
                "bsonType": "bool",
                "description": "Indica si el país es sede del Mundial 2030. Requerido.",
            },
            "createdAt": {"bsonType": "date"},
            "updatedAt": {"bsonType": "date"},
        },
        "additionalProperties": False,
    }
}

JUGADORES_SCHEMA = {
    "$jsonSchema": {
        "bsonType": "object",
        "title": "Validación de documento Jugador",
        "required": [
            "_id",
            "nombre",
            "apellido",
            "equipoId",
            "posicion",
            "dorsal",
            "altura",
            "peso",
        ],
        "properties": {
            "_id": {
                "bsonType": "string",
                "pattern": "^[A-Z]{3}-[0-9]{2}$",
                "description": "'{código de equipo}-{dorsal de 2 dígitos}'. Requerido.",
            },
            "nombre": {
                "bsonType": "string",
                "minLength": 1,
                "description": "Texto no vacío. Requerido.",
            },
            "apellido": {
                "bsonType": "string",
                "minLength": 1,
                "description": "Texto no vacío. Requerido.",
            },
            "equipoId": {
                "bsonType": "string",
                "pattern": "^[A-Z]{3}$",
                "description": "Referencia al _id de una selección existente. Requerido.",
            },
            "posicion": {
                "enum": ["Arquero", "Defensor", "Mediocampista", "Delantero"],
                "description": "Restringido a valores válidos de posición. Requerido.",
            },
            "dorsal": {
                "bsonType": "int",
                "minimum": 1,
                "maximum": 99,
                "description": "Entero entre 1 y 99. Requerido.",
            },
            "fechaNacimiento": {
                "bsonType": "date",
                "description": "Fecha de nacimiento del jugador.",
            },
            "altura": {
                "bsonType": "int",
                "minimum": 1,
                "description": "Entero mayor a 0, en centímetros. Requerido.",
            },
            "peso": {
                "bsonType": "double",
                "minimum": 0,
                "exclusiveMinimum": True,
                "description": "Decimal mayor a 0, en kilogramos. Requerido.",
            },
            "club": {"bsonType": "string"},
            "capitan": {"bsonType": "bool"},
            "createdAt": {"bsonType": "date"},
            "updatedAt": {"bsonType": "date"},
        },
        "additionalProperties": False,
    }
}


def ensure_collection_with_validator(db, name, schema):
    if name not in db.list_collection_names():
        db.create_collection(name, validator=schema, validationLevel="strict", validationAction="error")
        print(f"  [creada] Colección '{name}' con validador $jsonSchema.")
    else:
        db.command("collMod", name, validator=schema, validationLevel="strict", validationAction="error")
        print(f"  [actualizada] Validador de '{name}' aplicado (collMod).")


def ensure_indexes(db):
    selecciones = db["selecciones"]
    jugadores = db["jugadores"]

    # --- Índices en 'selecciones' ---
    # grupo: soporta la consulta más frecuente de fixture ("equipos del grupo X")
    idx1 = selecciones.create_index([("grupo", ASCENDING)], name="idx_grupo")
    # confederacion: soporta reportes/filtrado por confederación
    idx2 = selecciones.create_index([("confederacion", ASCENDING)], name="idx_confederacion")
    print(f"  [selecciones] índices asegurados: {idx1}, {idx2}")

    # --- Índices en 'jugadores' ---
    # equipoId: consulta más frecuente y crítica -> "plantel de un equipo"
    idx3 = jugadores.create_index([("equipoId", ASCENDING)], name="idx_equipoId")
    # equipoId + posicion: filtrado compuesto muy usado (ej. delanteros de un equipo)
    idx4 = jugadores.create_index(
        [("equipoId", ASCENDING), ("posicion", ASCENDING)], name="idx_equipoId_posicion"
    )
    # apellido: soporta ordenamiento alfabético + paginación (RF10)
    idx5 = jugadores.create_index([("apellido", ASCENDING)], name="idx_apellido")
    print(f"  [jugadores] índices asegurados: {idx3}, {idx4}, {idx5}")

    print(
        "\n  Nota: no se indexa 'anfitrion' en selecciones ni 'club' en jugadores: "
        "son campos de baja selectividad / bajo uso en consultas críticas, y cada "
        "índice adicional implica costo de escritura y almacenamiento sin beneficio "
        "claro (ver Documento de Decisiones, sección 'Índices principales')."
    )


def main():
    db = get_db()
    print(f"Conectado a base de datos: {db.name}")

    print("\n== Validaciones documentales (RF7) ==")
    ensure_collection_with_validator(db, "selecciones", SELECCIONES_SCHEMA)
    ensure_collection_with_validator(db, "jugadores", JUGADORES_SCHEMA)

    print("\n== Índices (RF12) ==")
    ensure_indexes(db)

    print("\n== Listado final de índices ==")
    for coll_name in ["selecciones", "jugadores"]:
        print(f"-- {coll_name} --")
        for idx in db[coll_name].list_indexes():
            print(f"   {idx['name']}: {idx['key']}")


if __name__ == "__main__":
    main()
