from app.adapters import redis_adapter


def obtener_sesion(usuario_id: str):

    return redis_adapter.buscar_sesion(
        usuario_id.upper()
    )