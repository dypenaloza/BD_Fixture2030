"""
Generador reproducible del dataset de muestra del módulo Redis (Hito 7).

No se conecta a Redis: escribe un archivo de comandos `redis-cli` plano
(scripts/carga_muestra.redis) que después se ejecuta con:

    docker exec -i fixture2030-redis redis-cli < scripts/carga_muestra.redis

Es la misma idea que "CSV + LOAD/COPY" usada en los módulos de Mongo/Neo4j/
Cassandra, adaptada al modelo clave-valor: en vez de un archivo de datos
separado, el "dataset" es directamente la secuencia de comandos que lo
construye (HSET, SET, ZADD...), porque eso es lo que Redis entiende.

Reproducibilidad (RNF3) e idempotencia (RNF4): la semilla es fija
(SEED = 2030, la misma de los Hitos 4/5/6) y todas las escrituras son HSET/
SET/ZADD sobre claves determinísticas — volver a cargar el mismo archivo
sobre un Redis ya cargado sobrescribe cada clave con el mismo valor, nunca
duplica nada (no existe un "INSERT" en Redis que pueda fallar por clave
repetida).

No usa librerías externas (solo stdlib): no hace falta instalar nada para
regenerar el archivo.
"""
import random
from datetime import datetime, timedelta
from pathlib import Path

SEED = 2030
random.seed(SEED)

BASE_DIR = Path(__file__).resolve().parent.parent
SALIDA = BASE_DIR / "scripts" / "carga_muestra.redis"

# ---------------------------------------------------------------------------
# Usuarios: mismo formato de identificador que ya usa Cassandra para
# usuario_id (U00001..U50000, ver Cassandra/scripts/generar_comentarios.py)
# -- se toma una muestra chica de ese mismo espacio de IDs en vez de
# inventar un esquema nuevo (RNF6: coherencia con hitos anteriores).
# ---------------------------------------------------------------------------
TOTAL_USUARIOS_MUESTRA = 200
TOTAL_USUARIOS_CASSANDRA = 50_000

NOMBRES = [
    "Sofía", "Mateo", "Valentina", "Lucas", "Martina", "Bruno", "Camila",
    "Thiago", "Lucía", "Benjamín", "Emma", "Joaquín", "Mía", "Santiago",
    "Julieta", "Facundo", "Abril", "Tomás", "Renata", "Agustín",
]

ROLES = ["fan"] * 9 + ["moderador"]  # 90% fan, 10% moderador

# Partidos reales del fixture generado en el Hito 5 (rama main/Neo4j):
# tres de fase de grupos y tres de instancias de eliminación, para mostrar
# tanto partidos "en curso" (fase de grupos, varios por día) como partidos
# únicos de eliminación directa.
PARTIDOS_DEMO = ["P-A-1", "P-A-3", "P-E-4", "P-QF-2", "P-R16-3", "P-R32-6"]

# Selecciones/jugadores de ejemplo (mismo formato EQUIPO-DORSAL del Hito 4)
# para la encuesta de figura del partido. No se listan por nombre: Redis
# sólo guarda el identificador y el conteo de votos, el nombre se resuelve
# contra MongoDB cuando la aplicación necesita mostrarlo (ver
# docs/ciclo_de_vida_e_invalidacion.md).
CANDIDATOS_FIGURA = {
    "P-A-1": ["ARG-10", "ARG-09", "ESP-07", "ESP-11"],
    "P-A-3": ["ARG-10", "ARG-07", "ESP-09", "ESP-04"],
    "P-E-4": ["JPN-07", "JPN-10", "SEN-09", "SEN-11"],
    "P-QF-2": ["JPN-10", "JPN-22", "BRA-09", "BRA-10"],
    "P-R16-3": ["JPN-07", "JPN-14", "SEN-01", "SEN-08"],
    "P-R32-6": ["JPN-10", "USA-19", "USA-07"],
}

FECHA_REFERENCIA = datetime(2030, 6, 13, 20, 0, 0)

lineas = []


def comentario(texto):
    lineas.append(f"# {texto}")


def comando(texto):
    lineas.append(texto)


# ---------------------------------------------------------------------------
# 1. Sesiones de usuario (RF3, RF4, RF5)
# ---------------------------------------------------------------------------
comentario("=" * 70)
comentario("1. SESIONES DE USUARIO (RF3/RF4/RF5)")
comentario("Hash por usuario + TTL de 1800s (30 min de inactividad, ver")
comentario("docs/ciclo_de_vida_e_invalidacion.md). La mayoría se carga con")
comentario("TTL completo; un grupo chico se carga con TTL muy corto (5s)")
comentario("para poder demostrar la expiración real en la práctica en vivo")
comentario("sin esperar 30 minutos.")
comentario("=" * 70)

usuarios_muestra = random.sample(range(1, TOTAL_USUARIOS_CASSANDRA + 1), TOTAL_USUARIOS_MUESTRA)

for i, numero_usuario in enumerate(usuarios_muestra):
    usuario_id = f"U{numero_usuario:05d}"
    nombre = random.choice(NOMBRES)
    rol = random.choice(ROLES)
    minutos_atras = random.randint(0, 25)
    ultimo_acceso = FECHA_REFERENCIA - timedelta(minutes=minutos_atras)
    partido_siguiendo = random.choice(PARTIDOS_DEMO)

    comando(
        f'HSET sesion:{usuario_id} usuario_id "{usuario_id}" nombre "{nombre}" '
        f'rol "{rol}" ultimo_acceso "{ultimo_acceso.strftime("%Y-%m-%dT%H:%M:%SZ")}" '
        f'partido_siguiendo "{partido_siguiendo}"'
    )
    if i < 10:
        # Las primeras 10 sesiones quedan con TTL de 5s: alcanza para que,
        # durante la práctica, se las vea vencer sin esperar los 30 min
        # reales de producción (ver scripts/sesiones.redis, sección 4).
        comando(f"EXPIRE sesion:{usuario_id} 5")
    else:
        comando(f"EXPIRE sesion:{usuario_id} 1800")

# ---------------------------------------------------------------------------
# 2. Caché de resultado de partido (RF6, RF7)
# ---------------------------------------------------------------------------
comentario("")
comentario("=" * 70)
comentario("2. CACHE DE RESULTADO DE PARTIDO (RF6/RF7)")
comentario("Fuente de verdad: Neo4j (nodo :Partido). TTL corto (45s) porque")
comentario("es un dato que cambia mientras el partido está en curso -- ver")
comentario("docs/ciclo_de_vida_e_invalidacion.md.")
comentario("=" * 70)

marcadores = {
    "P-A-1": (1, 2, "finalizado"),
    "P-A-3": (2, 1, "finalizado"),
    "P-E-4": (0, 0, "en_juego"),
    "P-QF-2": (3, 1, "finalizado"),
    "P-R16-3": (2, 1, "finalizado"),
    "P-R32-6": (1, 0, "en_juego"),
}

for partido_id, (local, visitante, estado) in marcadores.items():
    comando(
        f'SET cache:partido:{partido_id} '
        f'"{{\\"golesLocal\\":{local},\\"golesVisitante\\":{visitante},'
        f'\\"estado\\":\\"{estado}\\"}}" EX 45'
    )

# ---------------------------------------------------------------------------
# 3. Contadores de visitas y encuesta de figura del partido (RF8, RF9)
# ---------------------------------------------------------------------------
comentario("")
comentario("=" * 70)
comentario("3. CONTADOR DE VISITAS Y ENCUESTA DE FIGURA (RF8/RF9)")
comentario("INCRBY simula visitas ya acumuladas antes de la demo en vivo.")
comentario("ZADD precarga votos de la encuesta; en la demo se agregan mas")
comentario("con ZINCRBY para mostrar la actualizacion atomica concurrente.")
comentario("=" * 70)

for partido_id in PARTIDOS_DEMO:
    visitas_previas = random.randint(500, 5000)
    comando(f"SET contador:partido:{partido_id}:visitas {visitas_previas}")

    candidatos = CANDIDATOS_FIGURA[partido_id]
    for jugador_id in candidatos:
        votos = random.randint(5, 80)
        comando(f'ZADD encuesta:{partido_id}:figura {votos} "{jugador_id}"')

print(f"Generando {SALIDA} ...")
SALIDA.write_text("\n".join(lineas) + "\n", encoding="utf-8")
print(f"Listo: {len(usuarios_muestra)} sesiones, {len(marcadores)} partidos en caché,")
print(f"{len(PARTIDOS_DEMO)} contadores de visitas y encuestas de figura.")
