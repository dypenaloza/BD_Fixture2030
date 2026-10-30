import os
from functools import lru_cache

from app.adapters import mongo_adapter


# Caché en memoria para consultas repetidas
@lru_cache(maxsize=64)
def _buscar_seleccion_cacheada(codigo: str):
    return mongo_adapter.buscar_seleccion(codigo)


def obtener_seleccion(codigo: str):
    codigo = codigo.upper()

    # Permite desactivar la caché para las pruebas
    usar_cache = os.getenv("HITO12_USAR_CACHE", "1")

    if usar_cache == "0":
        return mongo_adapter.buscar_seleccion(codigo)

    return _buscar_seleccion_cacheada(codigo)