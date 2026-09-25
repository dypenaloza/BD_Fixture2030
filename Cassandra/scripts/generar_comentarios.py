import csv
import os
import random
import uuid
from datetime import datetime, timedelta

# -----------------------------
# Configuración
# -----------------------------

TOTAL_COMENTARIOS = 1_050_000
TOTAL_PARTIDOS = 100
TOTAL_USUARIOS = 50_000
DURACION_PARTIDO_MINUTOS = 180
BUCKET_MINUTOS = 5

random.seed(2030)

# Carpeta data/ del proyecto
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")

os.makedirs(DATA_DIR, exist_ok=True)

ARCHIVO_PARTIDOS = os.path.join(
    DATA_DIR,
    "comentarios_por_partido.csv"
)

ARCHIVO_USUARIOS = os.path.join(
    DATA_DIR,
    "comentarios_por_usuario.csv"
)

ESTADOS = [
    "visible",
    "visible",
    "visible",
    "visible",
    "pendiente",
    "oculto"
]

TEXTOS = [
    "Gran partido",
    "Que buena jugada",
    "Increible",
    "Vamos equipo",
    "Buen gol",
    "Que atajada",
    "Partidazo",
    "No lo puedo creer",
    "Muy buena jugada",
    "Vamos que se puede"
]

# Fecha base ficticia del Fixture 2030
FECHA_BASE = datetime(2030, 6, 1, 18, 0, 0)


def obtener_bucket(fecha):
    """Devuelve un bucket temporal de 5 minutos."""
    minuto_inicio = (fecha.minute // BUCKET_MINUTOS) * BUCKET_MINUTOS
    minuto_fin = minuto_inicio + BUCKET_MINUTOS

    hora_inicio = fecha.hour
    hora_fin = hora_inicio

    if minuto_fin >= 60:
        minuto_fin = 0
        hora_fin = (hora_inicio + 1) % 24

    return (
        f"{hora_inicio:02d}:{minuto_inicio:02d}-"
        f"{hora_fin:02d}:{minuto_fin:02d}"
    )


def generar():
    print(f"Generando {TOTAL_COMENTARIOS:,} comentarios...")

    with open(
        ARCHIVO_PARTIDOS,
        "w",
        newline="",
        encoding="utf-8"
    ) as archivo_partidos, open(
        ARCHIVO_USUARIOS,
        "w",
        newline="",
        encoding="utf-8"
    ) as archivo_usuarios:

        escritor_partidos = csv.writer(archivo_partidos)
        escritor_usuarios = csv.writer(archivo_usuarios)

        # Encabezados
        escritor_partidos.writerow([
            "partido_id",
            "bucket_temporal",
            "creado_en",
            "comentario_id",
            "usuario_id",
            "contenido",
            "estado_moderacion",
            "likes"
        ])

        escritor_usuarios.writerow([
            "usuario_id",
            "bucket_temporal",
            "creado_en",
            "comentario_id",
            "partido_id",
            "contenido",
            "estado_moderacion",
            "likes"
        ])

        for i in range(TOTAL_COMENTARIOS):

            # Distribución reproducible entre partidos
            numero_partido = (i % TOTAL_PARTIDOS) + 1
            partido_id = f"M{numero_partido:03d}"

            # Usuario distribuido pseudoaleatoriamente
            numero_usuario = random.randint(1, TOTAL_USUARIOS)
            usuario_id = f"U{numero_usuario:05d}"

            # Cada partido comienza en un día/horario diferente
            fecha_partido = (
                FECHA_BASE
                + timedelta(days=(numero_partido - 1) % 30)
                + timedelta(hours=(numero_partido - 1) % 4)
            )

            segundos = random.randint(
                0,
                DURACION_PARTIDO_MINUTOS * 60 - 1
            )

            creado_en = fecha_partido + timedelta(seconds=segundos)

            bucket_partido = obtener_bucket(creado_en)
            bucket_usuario = creado_en.strftime("%Y-%m")

            # UUID determinístico:
            # volver a ejecutar el script genera los mismos IDs
            comentario_id = str(uuid.UUID(int=i + 1))

            contenido = random.choice(TEXTOS)
            estado = random.choice(ESTADOS)
            likes = random.randint(0, 50)

            fecha_cql = creado_en.strftime(
                "%Y-%m-%d %H:%M:%S+0000"
            )

            # Tabla principal
            escritor_partidos.writerow([
                partido_id,
                bucket_partido,
                fecha_cql,
                comentario_id,
                usuario_id,
                contenido,
                estado,
                likes
            ])

            # Tabla secundaria
            escritor_usuarios.writerow([
                usuario_id,
                bucket_usuario,
                fecha_cql,
                comentario_id,
                partido_id,
                contenido,
                estado,
                likes
            ])

            if (i + 1) % 100_000 == 0:
                print(
                    f"{i + 1:,} / "
                    f"{TOTAL_COMENTARIOS:,} comentarios generados"
                )

    print()
    print("Generación terminada.")
    print(f"Comentarios: {TOTAL_COMENTARIOS:,}")
    print(f"Partidos: {TOTAL_PARTIDOS}")
    print(f"Usuarios posibles: {TOTAL_USUARIOS}")
    print(f"Bucket principal: {BUCKET_MINUTOS} minutos")
    print()
    print(f"Archivo principal: {ARCHIVO_PARTIDOS}")
    print(f"Archivo usuarios:  {ARCHIVO_USUARIOS}")


if __name__ == "__main__":
    generar()