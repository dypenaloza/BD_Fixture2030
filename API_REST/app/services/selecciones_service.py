from app.adapters import mongo_adapter


def obtener_seleccion(codigo: str):

    codigo = codigo.upper()

    return mongo_adapter.buscar_seleccion(codigo)