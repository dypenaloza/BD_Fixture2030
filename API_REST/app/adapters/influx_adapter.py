from pathlib import Path

import requests

from app.config import settings


def obtener_token():

    if settings.INFLUX_TOKEN:
        return settings.INFLUX_TOKEN

    archivo = Path(settings.INFLUX_TOKEN_FILE)

    if not archivo.is_absolute():
        archivo = settings.BASE_DIR / archivo

    token = archivo.read_text(
        encoding="utf-8"
    ).strip()

    if not token:
        raise RuntimeError(
            "El token de InfluxDB esta vacio"
        )

    return token


def buscar_estadisticas(
    partido_id: str,
    equipo_id: str,
    desde: str,
    hasta: str,
    limit: int
):

    sql = f"""
        SELECT
            time,
            equipo_id,
            posesion_pct,
            pases,
            tiros

        FROM estadisticas

        WHERE partido_id = $partido_id
          AND equipo_id = $equipo_id
          AND time >= $desde
          AND time <= $hasta

        ORDER BY time ASC

        LIMIT {limit}
    """

    token = obtener_token()

    respuesta = requests.post(
        f"{settings.INFLUX_URL}/api/v3/query_sql",

        headers={
            "Authorization": f"Bearer {token}"
        },

        json={
            "db": settings.INFLUX_DATABASE,
            "q": sql,
            "format": "json",
            "params": {
                "partido_id": partido_id,
                "equipo_id": equipo_id,
                "desde": desde,
                "hasta": hasta
            }
        },

        timeout=(3, 8)
    )

    respuesta.raise_for_status()

    datos = respuesta.json()

    if not isinstance(datos, list):
        raise ValueError(
            "Respuesta inesperada de InfluxDB"
        )

    return datos