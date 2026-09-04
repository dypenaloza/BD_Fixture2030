"""
RF8 - Carga de datos reproducible e idempotente.
RF4, RF5 - Persistencia de 64 equipos y 1.000+ jugadores.

Vuelve a ejecutarse tantas veces como sea necesario sin generar duplicados
ni inconsistencias: usa `bulk_write` con `UpdateOne(..., upsert=True)`
sobre el `_id` natural de cada documento (código de equipo / "{equipo}-{dorsal}").
Si el documento ya existe, se sobreescribe con los mismos datos (no-op real);
si no existe, se inserta.
"""
import json
from datetime import datetime
from pathlib import Path

from pymongo import UpdateOne

from db import get_db

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

DATE_FIELDS = {"createdAt", "updatedAt", "fechaNacimiento"}


def _parse_dates(doc: dict) -> dict:
    for field in DATE_FIELDS:
        if field in doc and isinstance(doc[field], str):
            doc[field] = datetime.fromisoformat(doc[field])
    return doc


def load_collection(db, collection_name: str, file_name: str):
    path = DATA_DIR / file_name
    with open(path, encoding="utf-8") as f:
        docs = json.load(f)

    ops = []
    for doc in docs:
        doc = _parse_dates(doc)
        doc_id = doc.pop("_id")
        ops.append(UpdateOne({"_id": doc_id}, {"$set": doc}, upsert=True))

    result = db[collection_name].bulk_write(ops, ordered=False)
    print(
        f"[{collection_name}] leídos: {len(docs)} | "
        f"insertados: {result.upserted_count} | "
        f"actualizados: {result.modified_count} | "
        f"sin cambios: {len(docs) - result.upserted_count - result.modified_count}"
    )
    return len(docs)


def main():
    db = get_db()
    print(f"Conectado a base de datos: {db.name}")
    print("\n== Carga idempotente (RF8) ==")

    total_equipos = load_collection(db, "selecciones", "equipos.json")
    total_jugadores = load_collection(db, "jugadores", "jugadores.json")

    print("\n== Verificación de volumen (RF4, RF5, RNF2) ==")
    count_selecciones = db["selecciones"].count_documents({})
    count_jugadores = db["jugadores"].count_documents({})
    print(f"Documentos en 'selecciones': {count_selecciones} (esperado: {total_equipos})")
    print(f"Documentos en 'jugadores'  : {count_jugadores} (esperado >= 1000, archivo: {total_jugadores})")

    assert count_selecciones == 64, "Se esperaban exactamente 64 selecciones"
    assert count_jugadores >= 1000, "Se esperaban al menos 1000 jugadores"

    print("\n== Verificación de integridad referencial (RNF3) ==")
    equipos_validos = set(d["_id"] for d in db["selecciones"].find({}, {"_id": 1}))
    huerfanos = db["jugadores"].count_documents({"equipoId": {"$nin": list(equipos_validos)}})
    print(f"Jugadores con equipoId inválido/huérfano: {huerfanos} (esperado: 0)")
    assert huerfanos == 0, "Existen jugadores sin selección válida asociada"

    print("\nCarga finalizada sin duplicados ni inconsistencias.")


if __name__ == "__main__":
    main()
