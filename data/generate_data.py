"""
Generador de datos sintéticos y reproducibles para el módulo documental
(RF4, RF5, RNF2, RNF8).

Genera:
  - data/equipos.json    -> 64 selecciones nacionales (fase de grupos A-P)
  - data/jugadores.json  -> 24 jugadores por selección (1.536 jugadores en total)

El script usa una semilla fija (SEED) para que el dataset sea 100%
reproducible entre corridas y entre integrantes del grupo, cumpliendo
RNF1 (reproducibilidad) sin depender de servicios externos.

Estrategia de identificadores (ver documento de decisiones):
  - selección._id  = código FIFA de 3 letras, ej. "ARG"
  - jugador._id    = "{código de selección}-{dorsal de 2 dígitos}", ej. "ARG-10"
    Esto garantiza unicidad natural (no puede haber dos jugadores con el
    mismo dorsal en el mismo equipo) sin necesitar un índice compuesto
    adicional para esa regla de negocio.
"""
import json
import random
from datetime import date, datetime
from pathlib import Path

from faker import Faker

SEED = 2030
random.seed(SEED)
fake = Faker("es_ES")
fake.seed_instance(SEED)

BASE_DIR = Path(__file__).resolve().parent

# 64 selecciones: 6 anfitriones (Hito 2030 con 6 sedes) + 58 selecciones
# adicionales de las distintas confederaciones, agrupadas en 16 grupos (A-P)
# de 4 equipos cada uno, como corresponde a un mundial de 64 equipos.
EQUIPOS_RAW = [
    # (codigo, pais, confederacion, anfitrion, ranking_base)
    ("ARG", "Argentina", "CONMEBOL", True, 1),
    ("PAR", "Paraguay", "CONMEBOL", True, 45),
    ("URU", "Uruguay", "CONMEBOL", True, 14),
    ("ESP", "España", "UEFA", True, 3),
    ("POR", "Portugal", "UEFA", True, 6),
    ("MAR", "Marruecos", "CAF", True, 12),
    ("BRA", "Brasil", "CONMEBOL", False, 5),
    ("FRA", "Francia", "UEFA", False, 2),
    ("ENG", "Inglaterra", "UEFA", False, 4),
    ("GER", "Alemania", "UEFA", False, 8),
    ("ITA", "Italia", "UEFA", False, 9),
    ("NED", "Países Bajos", "UEFA", False, 7),
    ("BEL", "Bélgica", "UEFA", False, 10),
    ("CRO", "Croacia", "UEFA", False, 11),
    ("COL", "Colombia", "CONMEBOL", False, 13),
    ("USA", "Estados Unidos", "CONCACAF", False, 15),
    ("MEX", "México", "CONCACAF", False, 16),
    ("JPN", "Japón", "AFC", False, 17),
    ("KOR", "Corea del Sur", "AFC", False, 18),
    ("SEN", "Senegal", "CAF", False, 19),
    ("SUI", "Suiza", "UEFA", False, 20),
    ("DEN", "Dinamarca", "UEFA", False, 21),
    ("AUT", "Austria", "UEFA", False, 22),
    ("POL", "Polonia", "UEFA", False, 23),
    ("SRB", "Serbia", "UEFA", False, 24),
    ("CHL", "Chile", "CONMEBOL", False, 25),
    ("PER", "Perú", "CONMEBOL", False, 26),
    ("ECU", "Ecuador", "CONMEBOL", False, 27),
    ("CAN", "Canadá", "CONCACAF", False, 28),
    ("CRC", "Costa Rica", "CONCACAF", False, 29),
    ("JAM", "Jamaica", "CONCACAF", False, 30),
    ("PAN", "Panamá", "CONCACAF", False, 31),
    ("NGA", "Nigeria", "CAF", False, 32),
    ("GHA", "Ghana", "CAF", False, 33),
    ("EGY", "Egipto", "CAF", False, 34),
    ("TUN", "Túnez", "CAF", False, 35),
    ("CMR", "Camerún", "CAF", False, 36),
    ("CIV", "Costa de Marfil", "CAF", False, 37),
    ("ALG", "Argelia", "CAF", False, 38),
    ("RSA", "Sudáfrica", "CAF", False, 39),
    ("KSA", "Arabia Saudita", "AFC", False, 40),
    ("IRN", "Irán", "AFC", False, 41),
    ("AUS", "Australia", "AFC", False, 42),
    ("QAT", "Catar", "AFC", False, 43),
    ("IRQ", "Irak", "AFC", False, 44),
    ("UZB", "Uzbekistán", "AFC", False, 46),
    ("CHN", "China", "AFC", False, 47),
    ("NZL", "Nueva Zelanda", "OFC", False, 48),
    ("SWE", "Suecia", "UEFA", False, 49),
    ("NOR", "Noruega", "UEFA", False, 50),
    ("UKR", "Ucrania", "UEFA", False, 51),
    ("CZE", "Chequia", "UEFA", False, 52),
    ("SCO", "Escocia", "UEFA", False, 53),
    ("WAL", "Gales", "UEFA", False, 54),
    ("HUN", "Hungría", "UEFA", False, 55),
    ("ROU", "Rumania", "UEFA", False, 56),
    ("TUR", "Turquía", "UEFA", False, 57),
    ("VEN", "Venezuela", "CONMEBOL", False, 58),
    ("BOL", "Bolivia", "CONMEBOL", False, 59),
    ("HON", "Honduras", "CONCACAF", False, 60),
    ("HAI", "Haití", "CONCACAF", False, 61),
    ("CIW", "Curazao", "CONCACAF", False, 62),
    ("IND", "India", "AFC", False, 63),
    ("VIE", "Vietnam", "AFC", False, 64),
]

assert len(EQUIPOS_RAW) == 64, "El Fixture 2030 exige exactamente 64 selecciones"

GRUPOS = [chr(ord("A") + i) for i in range(16)]  # A..P

POSICIONES = ["Arquero", "Defensor", "Mediocampista", "Delantero"]
# Composición típica de un plantel de 24 jugadores.
COMPOSICION_PLANTEL = (
    ["Arquero"] * 3
    + ["Defensor"] * 8
    + ["Mediocampista"] * 8
    + ["Delantero"] * 5
)


def build_equipos():
    equipos = []
    now = datetime.utcnow()
    for idx, (codigo, pais, confederacion, anfitrion, ranking) in enumerate(EQUIPOS_RAW):
        grupo = GRUPOS[idx // 4]
        equipos.append(
            {
                "_id": codigo,
                "pais": pais,
                "nombre": f"Selección de {pais}",
                "confederacion": confederacion,
                "grupo": grupo,
                "ranking": ranking,
                "entrenador": fake.name(),
                "escudo": f"https://fixture2030.example.com/escudos/{codigo.lower()}.png",
                "anfitrion": anfitrion,
                "createdAt": now,
                "updatedAt": now,
            }
        )
    return equipos


def random_altura(posicion: str) -> int:
    rangos = {
        "Arquero": (185, 200),
        "Defensor": (178, 195),
        "Mediocampista": (170, 188),
        "Delantero": (168, 190),
    }
    lo, hi = rangos[posicion]
    return random.randint(lo, hi)


def random_peso(altura_cm: int) -> float:
    # Peso coherente con la altura (IMC aproximado entre 20 y 25).
    imc = random.uniform(20.5, 24.5)
    altura_m = altura_cm / 100
    return round(imc * (altura_m ** 2), 1)


def build_jugadores(equipos):
    jugadores = []
    now = datetime.utcnow()
    for equipo in equipos:
        codigo = equipo["_id"]
        dorsales = list(range(1, len(COMPOSICION_PLANTEL) + 1))
        random.shuffle(dorsales)
        capitan_idx = random.randrange(len(COMPOSICION_PLANTEL))
        for i, posicion in enumerate(COMPOSICION_PLANTEL):
            dorsal = dorsales[i]
            altura = random_altura(posicion)
            nacimiento = fake.date_of_birth(minimum_age=18, maximum_age=36)
            jugadores.append(
                {
                    "_id": f"{codigo}-{dorsal:02d}",
                    "nombre": fake.first_name_male(),
                    "apellido": fake.last_name(),
                    "equipoId": codigo,
                    "posicion": posicion,
                    "dorsal": dorsal,
                    "fechaNacimiento": datetime(
                        nacimiento.year, nacimiento.month, nacimiento.day
                    ),
                    "altura": altura,
                    "peso": random_peso(altura),
                    "club": f"{fake.city()} {random.choice(['FC', 'CF', 'SC', 'AC'])}",
                    "capitan": i == capitan_idx,
                    "createdAt": now,
                    "updatedAt": now,
                }
            )
    return jugadores


class _JSONEncoder(json.JSONEncoder):
    def default(self, o):
        if isinstance(o, (datetime, date)):
            return o.isoformat()
        return super().default(o)


def main():
    equipos = build_equipos()
    jugadores = build_jugadores(equipos)

    equipos_path = BASE_DIR / "equipos.json"
    jugadores_path = BASE_DIR / "jugadores.json"

    with open(equipos_path, "w", encoding="utf-8") as f:
        json.dump(equipos, f, ensure_ascii=False, indent=2, cls=_JSONEncoder)

    with open(jugadores_path, "w", encoding="utf-8") as f:
        json.dump(jugadores, f, ensure_ascii=False, indent=2, cls=_JSONEncoder)

    print(f"Equipos generados: {len(equipos)} -> {equipos_path}")
    print(f"Jugadores generados: {len(jugadores)} -> {jugadores_path}")
    assert len(equipos) == 64
    assert len(jugadores) >= 1000


if __name__ == "__main__":
    main()
