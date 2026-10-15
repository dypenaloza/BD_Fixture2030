from app.adapters import influx_adapter


def obtener_estadisticas(
    partido_id,
    equipo_id,
    desde,
    hasta,
    limit
):

    return influx_adapter.buscar_estadisticas(
        partido_id.upper(),
        equipo_id.upper(),
        desde,
        hasta,
        limit
    )