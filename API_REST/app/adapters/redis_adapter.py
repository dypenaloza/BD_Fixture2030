from functools import lru_cache

import redis

from app.config import settings


@lru_cache(maxsize=1)
def obtener_cliente():

    return redis.Redis.from_url(
        settings.REDIS_URL,
        decode_responses=True,
        socket_connect_timeout=3,
        socket_timeout=3
    )


def buscar_sesion(usuario_id: str):

    cliente = obtener_cliente()

    clave = f"sesion:{usuario_id}"

    # Recuperar los campos del Hash
    datos = cliente.hgetall(clave)

    if not datos:
        return None

    # Consultar tiempo de vida restante
    ttl = cliente.ttl(clave)

    # Una sesión válida debe tener TTL activo
    if ttl <= 0:
        return None

    return {
        "usuarioId": datos.get("usuario_id", usuario_id),
        "nombre": datos.get("nombre"),
        "rol": datos.get("rol"),
        "ultimoAcceso": datos.get("ultimo_acceso"),
        "partidoSiguiendo": datos.get("partido_siguiendo"),
        "ttlSegundos": ttl
    }


def cerrar_cliente():

    if obtener_cliente.cache_info().currsize:

        obtener_cliente().close()
        obtener_cliente.cache_clear()