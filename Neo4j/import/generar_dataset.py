"""
Generador reproducible del dataset del subgrafo del Fixture 2030 (RF6, RNF3).

Toma como ENTRADA los identificadores ya definidos en el Hito 4 (modulo
documental en MongoDB) y GENERA los insumos relacionales que el Hito 5
necesita: sedes, el fixture completo de 128 partidos, las participaciones
de cada seleccion y los eventos deportivos de cada partido.

Trazabilidad de identificadores (RF5 / RNF6)
--------------------------------------------
  seleccion.seleccionId == equipos.json[_id]    -> "ARG"
  (en jugadores.json el campo que referencia al equipo se llama "equipoId":
   se lee con ese nombre y se escribe como "seleccionId" en los CSV)
  jugador.jugadorId == jugadores.json[_id]   -> "ARG-10"

Los equipos y jugadores no se inventan aca: se leen tal cual del Hito 4, de
modo que la misma entidad es reconocible en ambos modulos. Las entidades
propias del Hito 5 (sedes, partidos, eventos) si se generan, con semilla
fija SEED = 2030 para que el resultado sea identico en cualquier notebook.

Salida: CSVs en este mismo directorio, que el contenedor monta en
/var/lib/neo4j/import y que queries/carga.cypher lee con LOAD CSV.

Uso:
    python generar_dataset.py
"""
import csv
import json
import math
import random
from datetime import date, timedelta
from pathlib import Path

SEED = 2030  # misma semilla que el generador del Hito 4

BASE_DIR = Path(__file__).resolve().parent
# Fuentes, en orden de preferencia:
#   1. el modulo documental del Hito 4 dentro del mismo repositorio;
#   2. el snapshot de equipos.json / jugadores.json versionado en Neo4j/data;
#   3. un snapshot propio en import/hito4 (permite ejecutar este modulo aislado).
FUENTES_HITO4 = [
    BASE_DIR.parents[1] / "MongoDB" / "data",
    BASE_DIR.parent / "data",
    BASE_DIR / "hito4",
]

# ---------------------------------------------------------------------------
# Estadios del Mundial 2030
#
# Las tres sedes sudamericanas albergan unicamente los partidos inaugurales de
# sus anfitriones (homenaje del centenario de 1930); el resto del torneo se
# juega en Espana, Portugal y Marruecos. paisId es el codigo FIFA del pais
# anfitrion, es decir el MISMO identificador que el equipo correspondiente:
# eso permite relacionar (:Estadio)-[:EN_PAIS_DE]->(:Seleccion).
# ---------------------------------------------------------------------------
ESTADIOS = [
    # (estadioId, nombre, ciudad, paisId, capacidad)
    ("MVD-CEN", "Estadio Centenario", "Montevideo", "URU", 60_000),
    ("BUE-MON", "Estadio Monumental", "Buenos Aires", "ARG", 84_567),
    ("ASU-DCH", "Estadio Defensores del Chaco", "Asunción", "PAR", 42_000),
    ("MAD-BER", "Estadio Santiago Bernabéu", "Madrid", "ESP", 83_186),
    ("MAD-MET", "Estadio Metropolitano", "Madrid", "ESP", 70_460),
    ("BCN-CAM", "Spotify Camp Nou", "Barcelona", "ESP", 105_000),
    ("SEV-CAR", "Estadio La Cartuja", "Sevilla", "ESP", 70_000),
    ("BIO-SMA", "San Mamés", "Bilbao", "ESP", 53_289),
    ("VAL-MES", "Estadio de Mestalla", "Valencia", "ESP", 49_500),
    ("LIS-LUZ", "Estádio da Luz", "Lisboa", "POR", 64_642),
    ("LIS-ALV", "Estádio José Alvalade", "Lisboa", "POR", 50_095),
    ("OPO-DRA", "Estádio do Dragão", "Oporto", "POR", 50_033),
    ("CAS-HII", "Grand Stade Hassan II", "Casablanca", "MAR", 115_000),
    ("RAB-MAB", "Estadio Moulay Abdellah", "Rabat", "MAR", 68_700),
    ("MRK-MAR", "Estadio de Marrakech", "Marrakech", "MAR", 45_240),
    ("TAN-IBN", "Estadio Ibn Batouta", "Tánger", "MAR", 75_600),
    ("AGA-ADR", "Estadio Adrar", "Agadir", "MAR", 45_480),
    ("FEZ-FEZ", "Estadio de Fez", "Fez", "MAR", 45_000),
]

ESTADIOS_INAUGURALES = {"URU": "MVD-CEN", "ARG": "BUE-MON", "PAR": "ASU-DCH"}
# Estadios disponibles para el resto del torneo (Espana, Portugal, Marruecos).
ESTADIOS_PRINCIPALES = [s[0] for s in ESTADIOS if s[3] not in ESTADIOS_INAUGURALES]

CONFEDERACIONES = {
    "CONMEBOL": "Confederación Sudamericana de Fútbol",
    "UEFA": "Unión de Asociaciones Europeas de Fútbol",
    "CAF": "Confederación Africana de Fútbol",
    "CONCACAF": "Confederación de Norteamérica, Centroamérica y el Caribe",
    "AFC": "Confederación Asiática de Fútbol",
    "OFC": "Confederación de Fútbol de Oceanía",
}

# (codigo, nombre, orden, cantidad de partidos esperada)
FASES = [
    ("GRUPOS", "Fase de grupos", 1, 96),
    ("DIECISEIS", "Dieciseisavos de final", 2, 16),
    ("OCTAVOS", "Octavos de final", 3, 8),
    ("CUARTOS", "Cuartos de final", 4, 4),
    ("SEMIS", "Semifinales", 5, 2),
    ("TERCERO", "Partido por el tercer puesto", 6, 1),
    ("FINAL", "Final", 7, 1),
]

HORARIOS = ["13:00", "16:00", "19:00", "22:00"]

# Probabilidad relativa de que un gol lo convierta cada posicion.
PESO_GOL_POR_POSICION = {
    "Delantero": 0.52,
    "Mediocampista": 0.31,
    "Defensor": 0.16,
    "Arquero": 0.01,
}
# Probabilidad relativa de recibir una tarjeta.
PESO_TARJETA_POR_POSICION = {
    "Delantero": 0.20,
    "Mediocampista": 0.34,
    "Defensor": 0.42,
    "Arquero": 0.04,
}


# ---------------------------------------------------------------------------
# 1. Entrada: equipos y jugadores del Hito 4
# ---------------------------------------------------------------------------
def cargar_hito4():
    for carpeta in FUENTES_HITO4:
        equipos_path = carpeta / "equipos.json"
        jugadores_path = carpeta / "jugadores.json"
        if equipos_path.exists() and jugadores_path.exists():
            with open(equipos_path, encoding="utf-8") as f:
                equipos = json.load(f)
            with open(jugadores_path, encoding="utf-8") as f:
                jugadores = json.load(f)
            print("Fuente Hito 4:", carpeta)
            return equipos, jugadores
    raise SystemExit(
        "No se encontraron equipos.json / jugadores.json del Hito 4 en:\n  "
        + "\n  ".join(str(c) for c in FUENTES_HITO4)
    )


# ---------------------------------------------------------------------------
# 2. Simulacion de resultados (deterministica por la semilla)
# ---------------------------------------------------------------------------
def fuerza(ranking):
    """Traduce el ranking FIFA (1 = mejor) a una fuerza relativa en (0, 1]."""
    return (65 - ranking) / 64


def poisson(lam, rnd):
    """Muestra una Poisson(lam) por el algoritmo de Knuth (sin dependencias)."""
    limite = math.exp(-lam)
    k, p = 0, 1.0
    while True:
        p *= rnd.random()
        if p <= limite:
            return k
        k += 1


def goles_esperados(f_propia, f_rival, ventaja=0.0):
    lam = 1.15 + 1.45 * f_propia - 0.95 * f_rival + ventaja
    return min(max(lam, 0.25), 4.0)


def simular_marcador(eq_local, eq_visit, rnd, ventaja_local=0.15):
    fl, fv = fuerza(eq_local["ranking"]), fuerza(eq_visit["ranking"])
    gl = poisson(goles_esperados(fl, fv, ventaja_local), rnd)
    gv = poisson(goles_esperados(fv, fl), rnd)
    return gl, gv


def definir_por_penales(eq_local, eq_visit, rnd):
    """Desempate de eliminatoria. Devuelve (penales_local, penales_visitante)."""
    fl, fv = fuerza(eq_local["ranking"]), fuerza(eq_visit["ranking"])
    gana_local = rnd.random() < 0.5 + 0.25 * (fl - fv)
    perdedor = rnd.choice([2, 3, 4])
    return (5, perdedor) if gana_local else (perdedor, 5)


# ---------------------------------------------------------------------------
# 3. Fixture: fase de grupos + eliminatorias
# ---------------------------------------------------------------------------
# Rondas de un round-robin de 4 equipos (indices dentro del grupo).
JORNADAS_GRUPO = [((0, 1), (2, 3)), ((0, 2), (1, 3)), ((0, 3), (1, 2))]

FECHAS_JORNADA = {
    1: [date(2030, 6, 14) + timedelta(days=d) for d in range(4)],   # 14-17/06
    2: [date(2030, 6, 19) + timedelta(days=d) for d in range(4)],   # 19-22/06
    3: [date(2030, 6, 24) + timedelta(days=d) for d in range(3)],   # 24-26/06
}
FECHA_INAUGURAL = date(2030, 6, 13)

FECHAS_ELIMINATORIA = {
    "DIECISEIS": [date(2030, 6, 29) + timedelta(days=d) for d in range(4)],
    "OCTAVOS": [date(2030, 7, 4) + timedelta(days=d) for d in range(2)],
    "CUARTOS": [date(2030, 7, 8) + timedelta(days=d) for d in range(2)],
    "SEMIS": [date(2030, 7, 12), date(2030, 7, 13)],
    "TERCERO": [date(2030, 7, 16)],
    "FINAL": [date(2030, 7, 17)],
}
# Estadios reservadas para las instancias decisivas.
ESTADIOS_FIJOS = {
    "SEMIS": ["BCN-CAM", "LIS-LUZ"],
    "TERCERO": ["CAS-HII"],
    "FINAL": ["MAD-BER"],
}


def construir_fase_de_grupos(equipos_por_grupo, equipos_idx, rnd):
    partidos = []
    for grupo, codigos in sorted(equipos_por_grupo.items()):
        # Orden interno del grupo por ranking: define local/visitante y cruces.
        codigos = sorted(codigos, key=lambda c: equipos_idx[c]["ranking"])
        for nro_jornada, cruces in enumerate(JORNADAS_GRUPO, start=1):
            for (i, j) in cruces:
                local, visitante = codigos[i], codigos[j]
                gl, gv = simular_marcador(
                    equipos_idx[local], equipos_idx[visitante], rnd
                )
                partidos.append(
                    {
                        "fase": "GRUPOS",
                        "grupo": grupo,
                        "jornada": nro_jornada,
                        "local": local,
                        "visitante": visitante,
                        "golesLocal": gl,
                        "golesVisitante": gv,
                        "definidoPor": "tiempo_reglamentario",
                        "penalesLocal": "",
                        "penalesVisitante": "",
                    }
                )
    return partidos


def asignar_fechas_y_sedes_grupos(partidos):
    """Programa cada partido de grupos en una fecha, horario y sede.

    Reglas aplicadas:
      - Cada anfitrion sudamericano (ARG, URU, PAR) juega exactamente un
        partido en su propia sede, como homenaje del centenario de 1930. Se
        elige su partido mas temprano cuyo rival no sea otro anfitrion que
        todavia no tenga su partido asignado, de modo que las tres sedes
        sudamericanas reciban un partido cada una. Los de la jornada 1 se
        juegan el 13/06 (fecha inaugural del torneo).
      - Ninguna seleccion juega dos partidos el mismo dia.
      - Ninguna sede recibe dos partidos en el mismo dia y horario.
    """
    pendientes = dict(ESTADIOS_INAUGURALES)
    en_orden = sorted(partidos, key=lambda x: (x["jornada"], x["grupo"]))
    inaugurales = []

    for anfitrion in ("ARG", "URU", "PAR"):
        candidatos = [
            p for p in en_orden
            if "estadioId" not in p and anfitrion in (p["local"], p["visitante"])
        ]
        # Preferencia: rival que no sea otro anfitrion aun sin sede asignada.
        elegido = next(
            (
                p for p in candidatos
                if next(c for c in (p["local"], p["visitante"]) if c != anfitrion)
                not in pendientes
            ),
            candidatos[0] if candidatos else None,
        )
        assert elegido is not None, "Sin partido disponible para " + anfitrion
        jornada = elegido["jornada"]
        elegido["fecha"] = (
            FECHA_INAUGURAL if jornada == 1 else FECHAS_JORNADA[jornada][0]
        )
        elegido["hora"] = HORARIOS[len(inaugurales) % len(HORARIOS)]
        elegido["estadioId"] = pendientes.pop(anfitrion)
        inaugurales.append(elegido)

    resto = [p for p in partidos if "estadioId" not in p]

    # El resto se reparte respetando las dos reglas de no solapamiento.
    ocupacion_equipo = set()   # (seleccionId, fecha)
    ocupacion_sede = set()     # (estadioId, fecha, hora)
    for p in inaugurales:
        ocupacion_equipo.add((p["local"], p["fecha"]))
        ocupacion_equipo.add((p["visitante"], p["fecha"]))
        ocupacion_sede.add((p["estadioId"], p["fecha"], p["hora"]))

    rotacion = list(ESTADIOS_PRINCIPALES)
    for p in sorted(resto, key=lambda x: (x["jornada"], x["grupo"])):
        asignado = False
        for fecha in FECHAS_JORNADA[p["jornada"]]:
            if (p["local"], fecha) in ocupacion_equipo:
                continue
            if (p["visitante"], fecha) in ocupacion_equipo:
                continue
            for hora in HORARIOS:
                for sede in rotacion:
                    if (sede, fecha, hora) in ocupacion_sede:
                        continue
                    p["fecha"], p["hora"], p["estadioId"] = fecha, hora, sede
                    ocupacion_equipo.add((p["local"], fecha))
                    ocupacion_equipo.add((p["visitante"], fecha))
                    ocupacion_sede.add((sede, fecha, hora))
                    rotacion.append(rotacion.pop(0))  # rota para repartir sedes
                    asignado = True
                    break
                if asignado:
                    break
            if asignado:
                break
        assert asignado, "No se pudo programar el partido " + str(p)
    return inaugurales + resto


def tabla_de_posiciones(partidos_grupo, equipos_idx):
    """Posiciones del grupo: puntos, diferencia de gol, goles a favor, ranking."""
    tabla = {}
    for p in partidos_grupo:
        for codigo, gf, gc in (
            (p["local"], p["golesLocal"], p["golesVisitante"]),
            (p["visitante"], p["golesVisitante"], p["golesLocal"]),
        ):
            fila = tabla.setdefault(codigo, {"pts": 0, "gf": 0, "gc": 0})
            fila["gf"] += gf
            fila["gc"] += gc
            fila["pts"] += 3 if gf > gc else (1 if gf == gc else 0)
    return sorted(
        tabla.items(),
        key=lambda kv: (
            -kv[1]["pts"],
            -(kv[1]["gf"] - kv[1]["gc"]),
            -kv[1]["gf"],
            equipos_idx[kv[0]]["ranking"],
        ),
    )


def construir_eliminatorias(partidos_grupos, equipos_por_grupo, equipos_idx, rnd):
    """Genera las 6 rondas eliminatorias a partir de las posiciones reales."""
    grupos = sorted(equipos_por_grupo)
    clasificados = {}
    for grupo in grupos:
        del_grupo = [p for p in partidos_grupos if p["grupo"] == grupo]
        posiciones = tabla_de_posiciones(del_grupo, equipos_idx)
        clasificados[grupo] = [posiciones[0][0], posiciones[1][0]]

    # Cruce de dieciseisavos: 1o de un grupo contra 2o del grupo siguiente,
    # de modo que dos equipos del mismo grupo no se reencuentren en la ronda.
    llaves = [
        (clasificados[grupos[i]][0], clasificados[grupos[(i + 1) % len(grupos)]][1])
        for i in range(len(grupos))
    ]

    partidos = []
    finalistas = []
    for codigo, _nombre, _orden, _cant in FASES[1:]:
        fechas = FECHAS_ELIMINATORIA[codigo]
        estadios_fijos = ESTADIOS_FIJOS.get(codigo)
        ganadores, perdedores = [], []
        for nro, (local, visitante) in enumerate(llaves):
            gl, gv = simular_marcador(
                equipos_idx[local], equipos_idx[visitante], rnd, ventaja_local=0.0
            )
            pen_l = pen_v = ""
            definido = "tiempo_reglamentario"
            if gl == gv:
                pen_l, pen_v = definir_por_penales(
                    equipos_idx[local], equipos_idx[visitante], rnd
                )
                definido = "penales"
            gano_local = gl > gv or (definido == "penales" and pen_l > pen_v)
            ganadores.append(local if gano_local else visitante)
            perdedores.append(visitante if gano_local else local)

            sede = (
                estadios_fijos[nro % len(estadios_fijos)]
                if estadios_fijos
                else ESTADIOS_PRINCIPALES[
                    (nro * 3 + len(partidos)) % len(ESTADIOS_PRINCIPALES)
                ]
            )
            partidos.append(
                {
                    "fase": codigo,
                    "grupo": "",
                    "jornada": "",
                    "local": local,
                    "visitante": visitante,
                    "golesLocal": gl,
                    "golesVisitante": gv,
                    "definidoPor": definido,
                    "penalesLocal": pen_l,
                    "penalesVisitante": pen_v,
                    "fecha": fechas[nro % len(fechas)],
                    "hora": HORARIOS[(nro // len(fechas)) % len(HORARIOS)],
                    "estadioId": sede,
                }
            )

        if codigo == "FINAL":
            break  # ultima ronda: no hay cruce siguiente que derivar
        if codigo == "SEMIS":
            # El tercer puesto lo juegan los perdedores de las semifinales.
            finalistas = ganadores
            llaves = [(perdedores[0], perdedores[1])]
        elif codigo == "TERCERO":
            llaves = [(finalistas[0], finalistas[1])]
        else:
            llaves = [
                (ganadores[i], ganadores[i + 1]) for i in range(0, len(ganadores), 2)
            ]

    return partidos


# ---------------------------------------------------------------------------
# 4. Eventos deportivos coherentes con el marcador
# ---------------------------------------------------------------------------
def elegir_jugador(plantel, pesos, rnd):
    poblacion = [j["_id"] for j in plantel]
    ponderacion = [pesos[j["posicion"]] for j in plantel]
    return rnd.choices(poblacion, weights=ponderacion, k=1)[0]


def generar_eventos(partidos, planteles, rnd):
    """Un evento por gol (coherente con el marcador) mas tarjetas por partido."""
    eventos = []
    for p in partidos:
        prorroga = p["definidoPor"] == "penales"
        minuto_max = 120 if prorroga else 90
        nro = 0
        for equipo, goles in (
            (p["local"], p["golesLocal"]),
            (p["visitante"], p["golesVisitante"]),
        ):
            for _ in range(goles):
                nro += 1
                jugador = elegir_jugador(planteles[equipo], PESO_GOL_POR_POSICION, rnd)
                de_penal = rnd.random() < 0.12
                eventos.append(
                    {
                        "eventoId": "EV-{}-{:02d}".format(p["partidoId"], nro),
                        "partidoId": p["partidoId"],
                        "jugadorId": jugador,
                        "seleccionId": equipo,
                        "tipo": "penal_convertido" if de_penal else "gol",
                        "minuto": rnd.randint(1, minuto_max),
                        "detalle": "Gol de penal" if de_penal else "Gol en jugada",
                    }
                )
        for equipo in (p["local"], p["visitante"]):
            for _ in range(rnd.randint(0, 3)):
                nro += 1
                jugador = elegir_jugador(
                    planteles[equipo], PESO_TARJETA_POR_POSICION, rnd
                )
                roja = rnd.random() < 0.08
                eventos.append(
                    {
                        "eventoId": "EV-{}-{:02d}".format(p["partidoId"], nro),
                        "partidoId": p["partidoId"],
                        "jugadorId": jugador,
                        "seleccionId": equipo,
                        "tipo": "tarjeta_roja" if roja else "tarjeta_amarilla",
                        "minuto": rnd.randint(1, minuto_max),
                        "detalle": "Expulsión" if roja else "Infracción táctica",
                    }
                )
    eventos.sort(key=lambda e: (e["partidoId"], e["minuto"], e["eventoId"]))
    return eventos


# ---------------------------------------------------------------------------
# 5. Escritura de CSVs
# ---------------------------------------------------------------------------
def escribir_csv(nombre, columnas, filas):
    ruta = BASE_DIR / nombre
    with open(ruta, "w", encoding="utf-8", newline="") as f:
        escritor = csv.DictWriter(f, fieldnames=columnas, lineterminator="\n")
        escritor.writeheader()
        for fila in filas:
            escritor.writerow({c: fila.get(c, "") for c in columnas})
    print("  {:<24} {:>5} filas".format(nombre, len(filas)))


def resultado(gf, gc, definido, pen_propios, pen_rival):
    if gf > gc:
        return "victoria"
    if gf < gc:
        return "derrota"
    if definido == "penales":
        return "victoria_penales" if pen_propios > pen_rival else "derrota_penales"
    return "empate"


def main():
    rnd = random.Random(SEED)
    equipos, jugadores = cargar_hito4()

    equipos_idx = {e["_id"]: e for e in equipos}
    planteles = {}
    for j in jugadores:
        # "equipoId" es el nombre del campo en jugadores.json (Hito 4).
        planteles.setdefault(j["equipoId"], []).append(j)

    assert len(equipos) == 64, "El Fixture 2030 exige exactamente 64 selecciones"
    assert len(jugadores) > 1000, "RF6 exige mas de 1.000 jugadores"

    equipos_por_grupo = {}
    for e in equipos:
        equipos_por_grupo.setdefault(e["grupo"], []).append(e["_id"])

    # --- Fixture --------------------------------------------------------
    grupos = construir_fase_de_grupos(equipos_por_grupo, equipos_idx, rnd)
    grupos = asignar_fechas_y_sedes_grupos(grupos)
    eliminatorias = construir_eliminatorias(
        grupos, equipos_por_grupo, equipos_idx, rnd
    )

    partidos = sorted(
        grupos + eliminatorias,
        key=lambda p: (p["fecha"], p["hora"], p.get("grupo", ""), p["local"]),
    )
    orden_fase = {c: o for c, _n, o, _q in FASES}
    for nro, p in enumerate(partidos, start=1):
        p["partidoId"] = "F2030-{:03d}".format(nro)
        p["estado"] = "finalizado"
        p["ordenFase"] = orden_fase[p["fase"]]

    # --- Participaciones (una fila por equipo y partido) ----------------
    participaciones = []
    for p in partidos:
        for equipo, rol, gf, gc, pp, pr in (
            (p["local"], "local", p["golesLocal"], p["golesVisitante"],
             p["penalesLocal"], p["penalesVisitante"]),
            (p["visitante"], "visitante", p["golesVisitante"], p["golesLocal"],
             p["penalesVisitante"], p["penalesLocal"]),
        ):
            participaciones.append(
                {
                    "partidoId": p["partidoId"],
                    "seleccionId": equipo,
                    "rol": rol,
                    "goles": gf,
                    "golesRecibidos": gc,
                    "resultado": resultado(gf, gc, p["definidoPor"], pp, pr),
                }
            )

    eventos = generar_eventos(partidos, planteles, rnd)

    # --- Controles de coherencia (RNF7) ---------------------------------
    goles_por_partido_equipo = {}
    for ev in eventos:
        if ev["tipo"] in ("gol", "penal_convertido"):
            clave = (ev["partidoId"], ev["seleccionId"])
            goles_por_partido_equipo[clave] = goles_por_partido_equipo.get(clave, 0) + 1
    for par in participaciones:
        clave = (par["partidoId"], par["seleccionId"])
        assert goles_por_partido_equipo.get(clave, 0) == par["goles"], (
            "Eventos de gol inconsistentes con el marcador en " + str(clave)
        )
    jugador_a_equipo = {j["_id"]: j["equipoId"] for j in jugadores}
    for ev in eventos:
        assert jugador_a_equipo[ev["jugadorId"]] == ev["seleccionId"], (
            "Evento atribuido a un jugador ajeno al equipo"
        )
    for codigo, _n, _o, cantidad in FASES:
        real = sum(1 for p in partidos if p["fase"] == codigo)
        assert real == cantidad, (
            "Fase {}: {} partidos, se esperaban {}".format(codigo, real, cantidad)
        )
    estadios_validos = {s[0] for s in ESTADIOS}
    assert all(p["estadioId"] in estadios_validos for p in partidos), "Estadio inexistente"
    estadios_usados = {p["estadioId"] for p in partidos}
    assert estadios_usados == estadios_validos, (
        "Estadios sin ningun partido programado: " + str(sorted(estadios_validos - estadios_usados))
    )
    assert len({p["partidoId"] for p in partidos}) == len(partidos), "partidoId duplicado"
    assert len({e["eventoId"] for e in eventos}) == len(eventos), "eventoId duplicado"
    # Ninguna seleccion juega dos veces el mismo dia.
    agenda = set()
    for p in partidos:
        for equipo in (p["local"], p["visitante"]):
            clave = (equipo, p["fecha"])
            assert clave not in agenda, "Seleccion con dos partidos el mismo dia: " + str(clave)
            agenda.add(clave)

    # --- Escritura ------------------------------------------------------
    print("\nCSVs generados en", BASE_DIR)
    escribir_csv(
        "confederaciones.csv",
        ["codigo", "nombre"],
        [{"codigo": c, "nombre": n} for c, n in CONFEDERACIONES.items()],
    )
    escribir_csv(
        "grupos.csv",
        ["codigo"],
        [{"codigo": g} for g in sorted(equipos_por_grupo)],
    )
    escribir_csv(
        "fases.csv",
        ["codigo", "nombre", "orden"],
        [{"codigo": c, "nombre": n, "orden": o} for c, n, o, _q in FASES],
    )
    escribir_csv(
        "selecciones.csv",
        ["seleccionId", "pais", "nombre", "confederacion", "grupo", "ranking",
         "entrenador", "escudo", "anfitrion"],
        [
            {
                "seleccionId": e["_id"],
                "pais": e["pais"],
                "nombre": e["nombre"],
                "confederacion": e["confederacion"],
                "grupo": e["grupo"],
                "ranking": e["ranking"],
                "entrenador": e["entrenador"],
                "escudo": e["escudo"],
                "anfitrion": "true" if e["anfitrion"] else "false",
            }
            for e in equipos
        ],
    )
    escribir_csv(
        "jugadores.csv",
        ["jugadorId", "nombre", "apellido", "seleccionId", "posicion", "dorsal",
         "fechaNacimiento", "altura", "peso", "club", "capitan"],
        [
            {
                "jugadorId": j["_id"],
                "nombre": j["nombre"],
                "apellido": j["apellido"],
                "seleccionId": j["equipoId"],
                "posicion": j["posicion"],
                "dorsal": j["dorsal"],
                "fechaNacimiento": str(j["fechaNacimiento"])[:10],
                "altura": j["altura"],
                "peso": j["peso"],
                "club": j["club"],
                "capitan": "true" if j["capitan"] else "false",
            }
            for j in jugadores
        ],
    )
    escribir_csv(
        "estadios.csv",
        ["estadioId", "nombre", "ciudad", "paisId", "capacidad"],
        [
            {"estadioId": s, "nombre": n, "ciudad": c, "paisId": p, "capacidad": cap}
            for s, n, c, p, cap in ESTADIOS
        ],
    )
    escribir_csv(
        "partidos.csv",
        ["partidoId", "fecha", "hora", "fase", "ordenFase", "jornada", "grupo",
         "estadioId", "estado", "golesLocal", "golesVisitante", "definidoPor",
         "penalesLocal", "penalesVisitante"],
        [dict(p, fecha=p["fecha"].isoformat()) for p in partidos],
    )
    escribir_csv(
        "participaciones.csv",
        ["partidoId", "seleccionId", "rol", "goles", "golesRecibidos", "resultado"],
        participaciones,
    )
    escribir_csv(
        "eventos.csv",
        ["eventoId", "partidoId", "jugadorId", "seleccionId", "tipo", "minuto", "detalle"],
        eventos,
    )

    # --- Resumen --------------------------------------------------------
    final = partidos[-1]
    campeon = (
        final["local"]
        if final["golesLocal"] > final["golesVisitante"]
        or (final["definidoPor"] == "penales"
            and final["penalesLocal"] > final["penalesVisitante"])
        else final["visitante"]
    )
    print("\nSemilla: {} (dataset reproducible)".format(SEED))
    print(
        "Equipos: {} | Jugadores: {} | Estadios: {} | Partidos: {} | "
        "Participaciones: {} | Eventos: {}".format(
            len(equipos), len(jugadores), len(ESTADIOS), len(partidos),
            len(participaciones), len(eventos)
        )
    )
    print(
        "Final ({}): {} {}-{} {} -> campeon {} ({})".format(
            final["partidoId"], final["local"], final["golesLocal"],
            final["golesVisitante"], final["visitante"], campeon,
            equipos_idx[campeon]["pais"],
        )
    )
    print("Todos los controles de coherencia pasaron.")


if __name__ == "__main__":
    main()
