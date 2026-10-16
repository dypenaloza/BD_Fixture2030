import iris.dbapi

from app.config import settings


class IrisNoDisponible(Exception):
    pass


class IrisConsultaError(Exception):
    pass


def obtener_conexion():

    if not settings.IRIS_PASSWORD:
        raise IrisNoDisponible(
            "Credenciales de IRIS no configuradas"
        )

    try:

        conexion = iris.dbapi.connect(
            hostname=settings.IRIS_HOST,
            port=settings.IRIS_PORT,
            namespace=settings.IRIS_NAMESPACE,
            username=settings.IRIS_USERNAME,
            password=settings.IRIS_PASSWORD,
            timeout=5,
            sharedmemory=False
        )

        return conexion

    except (iris.dbapi.Error, OSError) as exc:

        raise IrisNoDisponible(
            "No se pudo establecer conexion con IRIS"
        ) from exc


def buscar_detalle_partido(codigo: str):

    conexion = obtener_conexion()

    try:

        cursor = conexion.cursor()

        try:

            cursor.setQueryTimeout(5)

            # Buscar el partido mediante su codigo
            cursor.execute(
                """
                SELECT ID, Codigo, Estado
                FROM Fixture.Partido
                WHERE Codigo = ?
                """,
                [codigo]
            )

            partido = cursor.fetchone()

            if partido is None:
                return None

            partido_id = partido[0]
            partido_codigo = partido[1]
            partido_estado = partido[2]

            # Recuperar sus eventos relacionados
            cursor.execute(
                """
                SELECT ID, Tipo, Minuto
                FROM Fixture.Evento
                WHERE Partido = ?
                ORDER BY Minuto ASC
                """,
                [partido_id]
            )

            registros = cursor.fetchall()

            eventos = []

            for registro in registros:

                eventos.append({
                    "id": str(registro[0]),
                    "tipo": registro[1],
                    "minuto": int(registro[2])
                })

            return {
                "id": str(partido_id),
                "codigo": partido_codigo,
                "estado": partido_estado,
                "cantidadEventos": len(eventos),
                "eventos": eventos
            }

        finally:

            cursor.close()

    except iris.dbapi.Error as exc:

        raise IrisConsultaError(
            "Error al consultar los objetos de IRIS"
        ) from exc

    finally:

        conexion.close()