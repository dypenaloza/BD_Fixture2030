from functools import lru_cache
from urllib.parse import quote_plus

from pymongo import MongoClient

from app.config import settings


@lru_cache(maxsize=1)
def obtener_cliente():

    if not settings.MONGO_PASSWORD:
        raise RuntimeError(
            "Falta configurar MONGO_PASSWORD"
        )

    usuario = quote_plus(settings.MONGO_USER)
    password = quote_plus(settings.MONGO_PASSWORD)

    uri = (
        f"mongodb://{usuario}:{password}"
        f"@{settings.MONGO_HOST}:{settings.MONGO_PORT}/"
        "?authSource=admin"
    )

    return MongoClient(
        uri,
        serverSelectionTimeoutMS=3000,
        connectTimeoutMS=3000,
        socketTimeoutMS=3000
    )


def buscar_seleccion(codigo: str):

    cliente = obtener_cliente()

    db = cliente[settings.MONGO_DB]

    coleccion = db["selecciones"]

    documento = coleccion.find_one(
        {"_id": codigo},
        {
            "_id": 1,
            "pais": 1,
            "nombre": 1,
            "confederacion": 1,
            "grupo": 1,
            "ranking": 1,
            "anfitrion": 1
        }
    )

    if documento is None:
        return None

    return {
        "id": documento["_id"],
        "pais": documento["pais"],
        "nombre": documento["nombre"],
        "confederacion": documento["confederacion"],
        "grupo": documento["grupo"],
        "ranking": documento["ranking"],
        "anfitrion": documento["anfitrion"]
    }


def cerrar_cliente():

    if obtener_cliente.cache_info().currsize:
        obtener_cliente().close()
        obtener_cliente.cache_clear()