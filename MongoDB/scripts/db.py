"""
Conexión centralizada a MongoDB para todos los scripts del Hito 4.

Las credenciales por defecto coinciden con las definidas en docker-compose.yml.
Pueden sobreescribirse mediante variables de entorno para no hardcodear
credenciales en el código (buena práctica, aunque para este entorno local
de desarrollo se documentan valores por defecto para simplificar la
reproducibilidad exigida por RNF1).
"""
import os
from pymongo import MongoClient

MONGO_USER = os.getenv("MONGO_USER", "admin")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD", "password123")
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = os.getenv("MONGO_PORT", "27017")
MONGO_DB = os.getenv("MONGO_DB", "fixture2030")

MONGO_URI = (
    f"mongodb://{MONGO_USER}:{MONGO_PASSWORD}@{MONGO_HOST}:{MONGO_PORT}/"
    f"?authSource=admin"
)


def get_client() -> MongoClient:
    return MongoClient(MONGO_URI, serverSelectionTimeoutMS=5000)


def get_db():
    return get_client()[MONGO_DB]
