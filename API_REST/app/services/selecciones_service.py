from functools import lru_cache
from app.adapters import mongo_adapter


# Caché en memoria para consultas repetidas
@lru_cache(maxsize=64)
def _buscar_seleccion_cacheada(codigo: str):
    return mongo_adapter.buscar_seleccion(codigo)


def obtener_seleccion(codigo: str):
    codigo = codigo.upper()
    return _buscar_seleccion_cacheada(codigo)