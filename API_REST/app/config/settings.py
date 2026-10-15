import os
from pathlib import Path

from dotenv import load_dotenv

# Carpeta raíz de la API
BASE_DIR = Path(__file__).resolve().parents[2]

# Cargar configuración local
load_dotenv(BASE_DIR / ".env")

#Mongo

MONGO_USER = os.getenv("MONGO_USER", "admin")
MONGO_PASSWORD = os.getenv("MONGO_PASSWORD")

MONGO_HOST = os.getenv("MONGO_HOST", "127.0.0.1")
MONGO_PORT = os.getenv("MONGO_PORT", "27017")

MONGO_DB = os.getenv("MONGO_DB", "fixture2030")

# Neo4j
NEO4J_URI = os.getenv(
    "NEO4J_URI", "bolt://127.0.0.1:7687"
)

NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")
NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")


# Cassandra
CASSANDRA_HOST = os.getenv(
    "CASSANDRA_HOST", "127.0.0.1"
)

CASSANDRA_PORT = int(
    os.getenv("CASSANDRA_PORT", "9042")
)

CASSANDRA_KEYSPACE = os.getenv(
    "CASSANDRA_KEYSPACE", "fixture2030"
)

# Redis
REDIS_URL = os.getenv(
    "REDIS_URL",
    "redis://127.0.0.1:6379/0"
)

# InfluxDB
INFLUX_URL = os.getenv(
    "INFLUX_URL",
    "http://127.0.0.1:8181"
)

INFLUX_DATABASE = os.getenv(
    "INFLUX_DATABASE",
    "fixture2030"
)

INFLUX_TOKEN = os.getenv("INFLUX_TOKEN", "").strip()

INFLUX_TOKEN_FILE = os.getenv(
    "INFLUX_TOKEN_FILE",
    "../InfluxDB/.influxdb3-token"
)