"""
Genera y carga de forma reproducible/idempotente el fixture del Mundial 2030:
estadios, partidos (fase de grupos + eliminatorias), la participación de cada
selección en sus partidos y los eventos (goles/tarjetas) de cada partido.

Es determinístico: usa una semilla fija (SEED = 2030) para el sorteo de
resultados, sedes y protagonistas de eventos, de modo que ejecutarlo varias
veces sobre el mismo ambiente produce siempre los mismos identificadores y
propiedades. La carga usa MERGE en todos los nodos y relaciones (RNF4).

Requisitos: equipos.json y jugadores.json ya deben estar cargados
(ejecutar antes scripts/load_data.py), porque este script sólo hace MATCH
sobre :Seleccion y :Jugador para crear las relaciones del fixture.

Uso:
    python scripts/generar_fixture.py
"""

import os
import json
import random
from collections import defaultdict
from datetime import date, timedelta
from pathlib import Path

from neo4j import GraphDatabase
from dotenv import load_dotenv

SEED = 2030

BASE_DIR = Path(__file__).resolve().parent.parent
load_dotenv(BASE_DIR / ".env")

USUARIO = os.environ.get("NEO4J_USER", "neo4j")
CLAVE = os.environ["NEO4J_PASSWORD"]
BOLT_PORT = os.environ.get("NEO4J_BOLT_PORT", "7687")
URI = f"bolt://localhost:{BOLT_PORT}"

ARCHIVO_EQUIPOS = BASE_DIR / "data" / "equipos.json"
ARCHIVO_JUGADORES = BASE_DIR / "data" / "jugadores.json"

FECHA_INICIO = date(2030, 6, 8)

# 16 sedes repartidas entre los seis países anfitriones del Mundial 2030
# (Argentina, Uruguay, Paraguay y España, con Portugal y Marruecos como
# confederaciones/host adicionales del contexto histórico del torneo).
ESTADIOS = [
    {"estadioId": "EST01", "nombre": "Estadio Monumental", "ciudad": "Buenos Aires", "pais": "Argentina", "capacidad": 84567},
    {"estadioId": "EST02", "nombre": "Estadio Mario Alberto Kempes", "ciudad": "Córdoba", "pais": "Argentina", "capacidad": 57000},
    {"estadioId": "EST03", "nombre": "Estadio Gigante de Arroyito", "ciudad": "Rosario", "pais": "Argentina", "capacidad": 41654},
    {"estadioId": "EST04", "nombre": "Estadio Ciudad de La Plata", "ciudad": "La Plata", "pais": "Argentina", "capacidad": 53000},
    {"estadioId": "EST05", "nombre": "Estadio Centenario", "ciudad": "Montevideo", "pais": "Uruguay", "capacidad": 60235},
    {"estadioId": "EST06", "nombre": "Estadio Defensores del Chaco", "ciudad": "Asunción", "pais": "Paraguay", "capacidad": 42354},
    {"estadioId": "EST07", "nombre": "Santiago Bernabéu", "ciudad": "Madrid", "pais": "España", "capacidad": 81044},
    {"estadioId": "EST08", "nombre": "Camp Nou", "ciudad": "Barcelona", "pais": "España", "capacidad": 99354},
    {"estadioId": "EST09", "nombre": "Estadio La Cartuja", "ciudad": "Sevilla", "pais": "España", "capacidad": 60000},
    {"estadioId": "EST10", "nombre": "San Mamés", "ciudad": "Bilbao", "pais": "España", "capacidad": 53289},
    {"estadioId": "EST11", "nombre": "Estádio da Luz", "ciudad": "Lisboa", "pais": "Portugal", "capacidad": 64642},
    {"estadioId": "EST12", "nombre": "Estádio do Dragão", "ciudad": "Oporto", "pais": "Portugal", "capacidad": 50033},
    {"estadioId": "EST13", "nombre": "Estádio José Alvalade", "ciudad": "Lisboa", "pais": "Portugal", "capacidad": 50095},
    {"estadioId": "EST14", "nombre": "Grand Stade de Tanger", "ciudad": "Tánger", "pais": "Marruecos", "capacidad": 65000},
    {"estadioId": "EST15", "nombre": "Estadio Mohammed V", "ciudad": "Casablanca", "pais": "Marruecos", "capacidad": 45891},
    {"estadioId": "EST16", "nombre": "Grand Stade de Marrakech", "ciudad": "Marrakech", "pais": "Marruecos", "capacidad": 45240},
]

ARBITROS_POOL = [
    "Marciano Elizondo", "Herminia Bosque", "Facundo Riobó", "Celia Palazuelos",
    "Norberto Casals", "Aurora Villanueva", "Ignacio Zabaleta", "Milagros Terán",
    "Cayetano Prado", "Encarnación Solórzano",
]


def cargar_json(ruta):
    with open(ruta, "r", encoding="utf-8") as archivo:
        return json.load(archivo)


def agrupar_por(items, clave):
    resultado = defaultdict(list)
    for item in items:
        resultado[item[clave]].append(item)
    return resultado


def fuerza(ranking):
    """Convierte el ranking FIFA (1 = mejor) en una fuerza relativa (0, 1]."""
    return max(1, 65 - ranking) / 64


def simular_goles(rng, fuerza_propia, fuerza_rival):
    """Aproxima una Poisson con una binomial de 10 ensayos (sin dependencias
    externas): reproducible con random.Random y sin necesidad de numpy."""
    base = 1.15 + 1.6 * fuerza_propia - 0.55 * fuerza_rival
    intentos = 10
    prob = min(0.9, max(0.03, base / intentos))
    return sum(1 for _ in range(intentos) if rng.random() < prob)


def elegir_arbitros(rng):
    return rng.sample(ARBITROS_POOL, 3)


PARTIDOS_POR_DIA_GRUPOS = 8


def generar_partidos_grupos(rng, equipos_por_grupo):
    """Round-robin (todos contra todos) dentro de cada uno de los 16 grupos:
    6 partidos por grupo x 16 grupos = 96 partidos de fase de grupos, a
    razón de PARTIDOS_POR_DIA_GRUPOS partidos simultáneos por jornada."""
    partidos = []
    indice_estadio = 0
    indice_partido_global = 0
    resultados_por_grupo = {}

    for grupo in sorted(equipos_por_grupo):
        equipos = equipos_por_grupo[grupo]
        enfrentamientos = [
            (equipos[i], equipos[j])
            for i in range(len(equipos))
            for j in range(i + 1, len(equipos))
        ]
        tabla = {e["_id"]: {"pj": 0, "pts": 0, "gf": 0, "gc": 0, "ranking": e["ranking"]} for e in equipos}

        for numero, (local, visitante) in enumerate(enfrentamientos, start=1):
            estadio = ESTADIOS[indice_estadio % len(ESTADIOS)]
            indice_estadio += 1
            fecha = FECHA_INICIO + timedelta(days=indice_partido_global // PARTIDOS_POR_DIA_GRUPOS)
            indice_partido_global += 1

            f_local, f_visitante = fuerza(local["ranking"]), fuerza(visitante["ranking"])
            goles_local = simular_goles(rng, f_local, f_visitante)
            goles_visitante = simular_goles(rng, f_visitante, f_local)

            partido_id = f"P-{grupo}-{numero}"
            partidos.append({
                "partidoId": partido_id,
                "fecha": fecha.isoformat(),
                "fase": "Fase de grupos",
                "grupo": grupo,
                "estado": "Finalizado",
                "arbitros": elegir_arbitros(rng),
                "estadioId": estadio["estadioId"],
                "local": local["_id"], "visitante": visitante["_id"],
                "golesLocal": goles_local, "golesVisitante": goles_visitante,
            })

            for equipo_id, goles_favor, goles_contra in (
                (local["_id"], goles_local, goles_visitante),
                (visitante["_id"], goles_visitante, goles_local),
            ):
                t = tabla[equipo_id]
                t["pj"] += 1
                t["gf"] += goles_favor
                t["gc"] += goles_contra
                if goles_favor > goles_contra:
                    t["pts"] += 3
                elif goles_favor == goles_contra:
                    t["pts"] += 1

        clasificados = sorted(
            tabla.items(),
            key=lambda kv: (-kv[1]["pts"], -(kv[1]["gf"] - kv[1]["gc"]), -kv[1]["gf"], kv[1]["ranking"]),
        )
        resultados_por_grupo[grupo] = [equipo_id for equipo_id, _ in clasificados]

    fecha_final_grupos = FECHA_INICIO + timedelta(days=(indice_partido_global - 1) // PARTIDOS_POR_DIA_GRUPOS)
    return partidos, resultados_por_grupo, fecha_final_grupos, indice_estadio


# Emparejamiento clásico de octavos por grupos adyacentes (1°A-2°B, 1°B-2°A, ...)
EMPAREJAMIENTOS_R32 = [
    ("A", 1, "B", 2), ("B", 1, "A", 2),
    ("C", 1, "D", 2), ("D", 1, "C", 2),
    ("E", 1, "F", 2), ("F", 1, "E", 2),
    ("G", 1, "H", 2), ("H", 1, "G", 2),
    ("I", 1, "J", 2), ("J", 1, "I", 2),
    ("K", 1, "L", 2), ("L", 1, "K", 2),
    ("M", 1, "N", 2), ("N", 1, "M", 2),
    ("O", 1, "P", 2), ("P", 1, "O", 2),
]


def generar_eliminatorias(rng, resultados_por_grupo, equipos_por_id, fecha_inicio, indice_estadio_inicial):
    fases = [
        ("R32", "Dieciseisavos de Final", 16),
        ("R16", "Octavos de Final", 8),
        ("QF", "Cuartos de Final", 4),
        ("SF", "Semifinales", 2),
    ]
    partidos = []
    fecha = fecha_inicio + timedelta(days=3)
    indice_estadio = indice_estadio_inicial

    clasificados = []
    for grupo, posicion, _, _ in EMPAREJAMIENTOS_R32:
        clasificados.append(resultados_por_grupo[grupo][posicion - 1])
    rivales = []
    for _, _, grupo_rival, posicion_rival in EMPAREJAMIENTOS_R32:
        rivales.append(resultados_por_grupo[grupo_rival][posicion_rival - 1])

    ronda_actual = list(zip(clasificados, rivales))

    for prefijo, nombre_fase, cantidad in fases:
        siguiente_ronda = []
        for numero, (local_id, visitante_id) in enumerate(ronda_actual[:cantidad], start=1):
            estadio = ESTADIOS[indice_estadio % len(ESTADIOS)]
            indice_estadio += 1

            local, visitante = equipos_por_id[local_id], equipos_por_id[visitante_id]
            f_local, f_visitante = fuerza(local["ranking"]), fuerza(visitante["ranking"])
            goles_local = simular_goles(rng, f_local, f_visitante)
            goles_visitante = simular_goles(rng, f_visitante, f_local)

            definicion_penales = False
            ganador_id = local_id if goles_local > goles_visitante else visitante_id
            if goles_local == goles_visitante:
                definicion_penales = True
                ganador_id = local_id if rng.random() < (0.5 + 0.05 * (f_local - f_visitante)) else visitante_id

            partido_id = f"P-{prefijo}-{numero}"
            partidos.append({
                "partidoId": partido_id,
                "fecha": fecha.isoformat(),
                "fase": nombre_fase,
                "grupo": None,
                "estado": "Finalizado",
                "arbitros": elegir_arbitros(rng),
                "estadioId": estadio["estadioId"],
                "local": local_id, "visitante": visitante_id,
                "golesLocal": goles_local, "golesVisitante": goles_visitante,
                "definicionPenales": definicion_penales,
                "ganador": ganador_id,
            })
            siguiente_ronda.append(ganador_id)
        fecha += timedelta(days=4)
        # Empareja secuencialmente a los ganadores para la siguiente ronda
        ronda_actual = list(zip(siguiente_ronda[0::2], siguiente_ronda[1::2]))

    # Tercer puesto (perdedores de semifinal) y final (ganadores de semifinal)
    semis = [p for p in partidos if p["fase"] == "Semifinales"]
    perdedores_semi = [p["local"] if p["ganador"] == p["visitante"] else p["visitante"] for p in semis]
    ganadores_semi = [p["ganador"] for p in semis]

    for prefijo, nombre_fase, pareja in (("3P", "Tercer Puesto", perdedores_semi), ("FIN", "Final", ganadores_semi)):
        estadio = ESTADIOS[indice_estadio % len(ESTADIOS)]
        # La final se juega en el estadio de mayor capacidad del circuito.
        if nombre_fase == "Final":
            estadio = max(ESTADIOS, key=lambda e: e["capacidad"])
        indice_estadio += 1
        local_id, visitante_id = pareja
        local, visitante = equipos_por_id[local_id], equipos_por_id[visitante_id]
        f_local, f_visitante = fuerza(local["ranking"]), fuerza(visitante["ranking"])
        goles_local = simular_goles(rng, f_local, f_visitante)
        goles_visitante = simular_goles(rng, f_visitante, f_local)
        definicion_penales = False
        ganador_id = local_id if goles_local > goles_visitante else visitante_id
        if goles_local == goles_visitante:
            definicion_penales = True
            ganador_id = local_id if rng.random() < 0.5 else visitante_id

        partidos.append({
            "partidoId": f"P-{prefijo}-1",
            "fecha": fecha.isoformat(),
            "fase": nombre_fase,
            "grupo": None,
            "estado": "Finalizado",
            "arbitros": elegir_arbitros(rng),
            "estadioId": estadio["estadioId"],
            "local": local_id, "visitante": visitante_id,
            "golesLocal": goles_local, "golesVisitante": goles_visitante,
            "definicionPenales": definicion_penales,
            "ganador": ganador_id,
        })
        fecha += timedelta(days=3)

    return partidos


PESOS_GOLEADOR = {"Delantero": 5, "Mediocampista": 3, "Defensor": 1, "Arquero": 0.2}
PESOS_TARJETA = {"Defensor": 3, "Mediocampista": 3, "Delantero": 2, "Arquero": 1}


def generar_eventos(rng, partidos, jugadores_por_equipo):
    eventos = []
    contador = 1

    for partido in partidos:
        for equipo_id, goles in (
            (partido["local"], partido["golesLocal"]),
            (partido["visitante"], partido["golesVisitante"]),
        ):
            plantel = jugadores_por_equipo[equipo_id]
            pesos = [PESOS_GOLEADOR[j["posicion"]] for j in plantel]
            for _ in range(goles):
                goleador = rng.choices(plantel, weights=pesos, k=1)[0]
                eventos.append({
                    "eventoId": f"EV{contador:04d}",
                    "tipo": "Gol",
                    "minuto": rng.randint(1, 90),
                    "descripcion": f"Gol de {goleador['nombre']} {goleador['apellido']}",
                    "partidoId": partido["partidoId"],
                    "jugadorId": goleador["_id"],
                })
                contador += 1

        # Tarjetas: 0 a 3 amonestados repartidos entre ambos planteles + baja probabilidad de roja.
        ambos = jugadores_por_equipo[partido["local"]] + jugadores_por_equipo[partido["visitante"]]
        pesos_tarjeta = [PESOS_TARJETA[j["posicion"]] for j in ambos]
        cantidad_amarillas = rng.choices([0, 1, 2, 3], weights=[15, 35, 35, 15], k=1)[0]
        for _ in range(cantidad_amarillas):
            amonestado = rng.choices(ambos, weights=pesos_tarjeta, k=1)[0]
            eventos.append({
                "eventoId": f"EV{contador:04d}",
                "tipo": "Tarjeta Amarilla",
                "minuto": rng.randint(1, 90),
                "descripcion": f"Amonestación a {amonestado['nombre']} {amonestado['apellido']}",
                "partidoId": partido["partidoId"],
                "jugadorId": amonestado["_id"],
            })
            contador += 1

        if rng.random() < 0.06:
            expulsado = rng.choices(ambos, weights=pesos_tarjeta, k=1)[0]
            eventos.append({
                "eventoId": f"EV{contador:04d}",
                "tipo": "Tarjeta Roja",
                "minuto": rng.randint(1, 90),
                "descripcion": f"Expulsión de {expulsado['nombre']} {expulsado['apellido']}",
                "partidoId": partido["partidoId"],
                "jugadorId": expulsado["_id"],
            })
            contador += 1

    return eventos


# --------------------------------------------------
# CARGA A NEO4J (MERGE — reproducible/idempotente)
# --------------------------------------------------

def cargar_estadios(tx, estadios):
    tx.run(
        """
        UNWIND $estadios AS e
        MERGE (est:Estadio {estadioId: e.estadioId})
        SET est.nombre = e.nombre,
            est.ciudad = e.ciudad,
            est.pais = e.pais,
            est.capacidad = e.capacidad
        """,
        estadios=estadios,
    )


def cargar_partidos_y_participaciones(tx, partidos):
    tx.run(
        """
        UNWIND $partidos AS p
        MERGE (partido:Partido {partidoId: p.partidoId})
        SET partido.fecha = date(p.fecha),
            partido.fase = p.fase,
            partido.grupo = p.grupo,
            partido.estado = p.estado,
            partido.arbitros = p.arbitros,
            partido.golesLocal = p.golesLocal,
            partido.golesVisitante = p.golesVisitante,
            partido.definicionPenales = coalesce(p.definicionPenales, false)

        WITH partido, p
        MATCH (estadio:Estadio {estadioId: p.estadioId})
        MERGE (partido)-[:SE_JUEGA_EN]->(estadio)

        WITH partido, p
        MATCH (local:Seleccion {seleccionId: p.local})
        MATCH (visitante:Seleccion {seleccionId: p.visitante})
        MERGE (local)-[rl:PARTICIPA_EN]->(partido)
        SET rl.rol = 'Local', rl.goles = p.golesLocal, rl.golesRecibidos = p.golesVisitante,
            rl.resultado = CASE
                WHEN p.golesLocal > p.golesVisitante THEN 'Ganado'
                WHEN p.golesLocal < p.golesVisitante THEN 'Perdido'
                ELSE 'Empate' END
        MERGE (visitante)-[rv:PARTICIPA_EN]->(partido)
        SET rv.rol = 'Visitante', rv.goles = p.golesVisitante, rv.golesRecibidos = p.golesLocal,
            rv.resultado = CASE
                WHEN p.golesVisitante > p.golesLocal THEN 'Ganado'
                WHEN p.golesVisitante < p.golesLocal THEN 'Perdido'
                ELSE 'Empate' END
        """,
        partidos=partidos,
    )


def cargar_eventos(tx, eventos):
    tx.run(
        """
        UNWIND $eventos AS ev
        MERGE (evento:Evento {eventoId: ev.eventoId})
        SET evento.tipo = ev.tipo,
            evento.minuto = ev.minuto,
            evento.descripcion = ev.descripcion

        WITH evento, ev
        MATCH (partido:Partido {partidoId: ev.partidoId})
        MERGE (evento)-[:OCURRE_EN]->(partido)

        WITH evento, ev
        MATCH (jugador:Jugador {jugadorId: ev.jugadorId})
        MERGE (evento)-[:PROTAGONIZADO_POR]->(jugador)
        """,
        eventos=eventos,
    )


def limpiar_datos_exploratorios(tx):
    """Elimina el partido y el evento de prueba manual (P001/EV001) creados
    durante la exploración inicial del modelo: mezclaban selecciones de
    grupos distintos (ARG vs BRA) y quedaban fuera de la fase de grupos
    round-robin generada por este script. El estadio E001 (Estadio
    Monumental) se conserva porque es el mismo EST01 del fixture generado."""
    tx.run("MATCH (p:Partido {partidoId: 'P001'}) DETACH DELETE p")
    tx.run("MATCH (e:Evento {eventoId: 'EV001'}) DETACH DELETE e")


def main():
    equipos = cargar_json(ARCHIVO_EQUIPOS)
    jugadores = cargar_json(ARCHIVO_JUGADORES)

    equipos_por_id = {e["_id"]: e for e in equipos}
    equipos_por_grupo = agrupar_por(equipos, "grupo")
    jugadores_por_equipo = agrupar_por(jugadores, "equipoId")

    rng = random.Random(SEED)

    partidos_grupos, resultados_por_grupo, fecha_tras_grupos, indice_estadio = generar_partidos_grupos(rng, equipos_por_grupo)
    partidos_eliminatorias = generar_eliminatorias(rng, resultados_por_grupo, equipos_por_id, fecha_tras_grupos, indice_estadio)
    partidos = partidos_grupos + partidos_eliminatorias

    eventos = generar_eventos(rng, partidos, jugadores_por_equipo)

    driver = GraphDatabase.driver(URI, auth=(USUARIO, CLAVE))
    with driver.session() as session:
        session.execute_write(limpiar_datos_exploratorios)
        session.execute_write(cargar_estadios, ESTADIOS)
        session.execute_write(cargar_partidos_y_participaciones, partidos)
        session.execute_write(cargar_eventos, eventos)

        total_estadios = session.run("MATCH (e:Estadio) RETURN count(e) AS total").single()["total"]
        total_partidos = session.run("MATCH (p:Partido) RETURN count(p) AS total").single()["total"]
        total_participaciones = session.run("MATCH ()-[r:PARTICIPA_EN]->() RETURN count(r) AS total").single()["total"]
        total_sejuega = session.run("MATCH ()-[r:SE_JUEGA_EN]->() RETURN count(r) AS total").single()["total"]
        total_eventos = session.run("MATCH (e:Evento) RETURN count(e) AS total").single()["total"]
        total_ocurre = session.run("MATCH ()-[r:OCURRE_EN]->() RETURN count(r) AS total").single()["total"]
        total_protagoniza = session.run("MATCH ()-[r:PROTAGONIZADO_POR]->() RETURN count(r) AS total").single()["total"]
    driver.close()

    print()
    print("===== RESULTADO DE LA CARGA DEL FIXTURE =====")
    print(f"Partidos generados en memoria: {len(partidos)} (grupos: {len(partidos_grupos)}, eliminatorias: {len(partidos_eliminatorias)})")
    print(f"Eventos generados en memoria: {len(eventos)}")
    print(f"Estadio: {total_estadios}")
    print(f"Partido: {total_partidos}")
    print(f"PARTICIPA_EN: {total_participaciones}")
    print(f"SE_JUEGA_EN: {total_sejuega}")
    print(f"Evento: {total_eventos}")
    print(f"OCURRE_EN: {total_ocurre}")
    print(f"PROTAGONIZADO_POR: {total_protagoniza}")


if __name__ == "__main__":
    main()
