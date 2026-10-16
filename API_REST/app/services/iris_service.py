from app.adapters import iris_adapter


def obtener_detalle_partido(codigo: str):

    return iris_adapter.buscar_detalle_partido(
        codigo.upper()
    )