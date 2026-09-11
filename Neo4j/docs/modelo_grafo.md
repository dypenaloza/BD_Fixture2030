# Modelo del grafo — Fixture 2030 (Hito 5)

Módulo de grafos del Fixture 2030, implementado en Neo4j. Este documento
describe el modelo tal como quedó implementado en `queries/constraints.cypher`,
`queries/indices.cypher`, `scripts/load_data.py` y `scripts/generar_fixture.py`.

## 1. Etiquetas de nodo

| Etiqueta | Atributo de identificación | Propiedades relevantes | Justificación |
|---|---|---|---|
| `:Seleccion` | `seleccionId` (= `_id` de `equipos` del Hito 4, ej. `"ARG"`) | `pais`, `nombre`, `confederacion`, `grupo`, `ranking`, `entrenador`, `escudo`, `anfitrion` | Es la entidad que participa en partidos y agrupa jugadores; se modela como nodo (no como propiedad de Jugador) porque tiene identidad y atributos propios y participa en más de una relación (jugadores que pertenecen a ella, partidos en los que participa). |
| `:Jugador` | `jugadorId` (= `_id` de `jugadores` del Hito 4, ej. `"ARG-01"`) | `nombre`, `apellido`, `posicion`, `dorsal`, `fechaNacimiento`, `altura`, `peso`, `club`, `capitan` | Entidad con identidad propia y relaciones hacia su selección y (opcionalmente) hacia eventos del torneo. |
| `:Partido` | `partidoId` (ej. `"P-A-1"`, `"P-R16-3"`, `"P-FIN-1"`) | `fecha`, `fase`, `grupo` (sólo fase de grupos), `estado`, `arbitros`, `golesLocal`, `golesVisitante`, `definicionPenales` | Núcleo del fixture: conecta selecciones, sede y eventos. Los goles quedan tanto en el partido (resultado) como en los eventos (detalle), ver §4. |
| `:Estadio` | `estadioId` (ej. `"EST01"`) | `nombre`, `ciudad`, `pais`, `capacidad` | Sede física, reutilizable entre partidos (relación 1\:N, ver §3). |
| `:Evento` | `eventoId` (ej. `"EV0001"`) | `tipo` (`"Gol"`, `"Tarjeta Amarilla"`, `"Tarjeta Roja"`), `minuto`, `descripcion` | Se modela como nodo y no como propiedad de `:Partido` porque cada partido tiene *varios* eventos, cada uno con su propio protagonista y minuto — una propiedad no podría representar esa multiplicidad ni permitir consultarlos individualmente (ver pregunta guía 2 del enunciado). |

No se creó una etiqueta `:Confederacion`, `:Grupo` ni `:Fase` como nodos
aparte: en este modelo `confederacion` y `grupo` son *propiedades* de
`Seleccion`/`Partido` (cardinalidad baja, sin atributos propios más allá del
nombre) en lugar de entidades con las que valga la pena relacionar por
separado — ver la justificación en `decisiones.md` §3 (D2).

## 2. Identificadores y coherencia con el Hito 4 (RF5)

- `Seleccion.seleccionId` es exactamente el `_id` de la colección `equipos`
  del módulo documental (Mongo), por ejemplo `"ARG"`.
- `Jugador.jugadorId` es exactamente el `_id` de la colección `jugadores`,
  por ejemplo `"ARG-08"`.
- Ambos se cargan leyendo los mismos archivos `data/equipos.json` y
  `data/jugadores.json` que alimentan el Hito 4 (`scripts/load_data.py`), por
  lo que cualquier equipo o jugador se reconoce con el mismo identificador en
  los dos módulos.
- Los partidos, sedes y eventos no existen en el Hito 4 (son exclusivos del
  módulo de grafos, como habilita la sección 5.3 del enunciado); sus IDs
  (`P-*`, `EST*`, `EV*`) son internos de este módulo.

## 3. Relaciones

| Relación | Dirección | Cardinalidad | Propiedades | Descripción |
|---|---|---|---|---|
| `(:Jugador)-[:PERTENECE_A]->(:Seleccion)` | Jugador → Selección | N:1 (cada jugador pertenece a una única selección; cada selección tiene 24 jugadores) | — | Plantel del Hito 4. |
| `(:Seleccion)-[:PARTICIPA_EN]->(:Partido)` | Selección → Partido | N:M (cada selección participa en 3 a 7 partidos según cuánto avanzó; cada partido tiene exactamente 2 selecciones) | `rol` (`"Local"`/`"Visitante"`), `goles`, `golesRecibidos`, `resultado` (`"Ganado"`/`"Perdido"`/`"Empate"`) | Núcleo del fixture: qué selecciones jugaron qué partido y con qué resultado. Las propiedades quedan en la relación (y no en el nodo Partido) porque son propias de *esa* selección en *ese* partido, no del partido en sí. |
| `(:Partido)-[:SE_JUEGA_EN]->(:Estadio)` | Partido → Estadio | N:1 (cada partido tiene una sede; cada estadio aloja varios partidos — 7 a 9 en la carga generada) | — | Programación de sede. |
| `(:Evento)-[:OCURRE_EN]->(:Partido)` | Evento → Partido | N:1 (cada evento ocurre en un único partido; cada partido tiene 0..N eventos) | — | Vincula goles/tarjetas con el partido correspondiente (RF4). |
| `(:Evento)-[:PROTAGONIZADO_POR]->(:Jugador)` | Evento → Jugador | N:1 (cada evento tiene un único protagonista; cada jugador puede protagonizar 0..N eventos) | — | Relación adicional (no exigida por RF4, pero coherente con RF3/RF8): permite responder "quién anotó/fue amonestado" sin duplicar el nombre del jugador como propiedad de texto en el evento. |

Todas las direcciones siguen el mismo criterio: **de la entidad más específica
hacia la más general/contenedora** (Jugador→Selección, Evento→Partido,
Evento→Jugador, Partido→Estadio) o hacia la entidad de la que se es
participante (Selección→Partido). Esto hace que los recorridos "hacia
arriba" (¿a qué selección pertenece?, ¿en qué partido ocurrió?) sean
`MATCH` directos con la flecha, y los recorridos "hacia abajo" (¿qué
jugadores tiene esta selección?, ¿qué eventos tuvo este partido?) inviertan
la flecha en el patrón — Cypher no distingue costo por sentido de recorrido.

## 4. Dónde vive cada dato (evitar duplicación, RNF6)

- El **resultado global** de un partido (`golesLocal`, `golesVisitante`) vive
  en `:Partido` y también, desagregado por selección, en las propiedades de
  `PARTICIPA_EN` (`goles`, `golesRecibidos`, `resultado`) — no se duplica sin
  motivo: son dos niveles de agregación distintos (el resultado del partido
  vs. el resultado *desde la perspectiva de una selección*) que conviene
  tener disponibles sin recalcular en cada consulta.
- El **detalle de cada gol/tarjeta** (minuto, tipo, protagonista) vive
  exclusivamente en `:Evento`, no se repite como lista dentro de `:Partido`,
  para poder filtrar/ordenar eventos individualmente (RF8) y agregar por
  jugador (RF9 §3) sin desnormalizar un array.
- El **nombre del jugador** no se copia dentro de `:Evento` como propiedad
  "fuente de verdad": `descripcion` incluye el nombre como texto libre sólo a
  fin descriptivo, pero la relación `PROTAGONIZADO_POR` es la que vincula al
  jugador real (evita que un cambio de nombre deje datos inconsistentes).

## 5. Restricciones de unicidad (`queries/constraints.cypher`)

```
CREATE CONSTRAINT jugador_id_unique   FOR (j:Jugador)   REQUIRE j.jugadorId   IS UNIQUE;
CREATE CONSTRAINT seleccion_id_unique FOR (s:Seleccion) REQUIRE s.seleccionId IS UNIQUE;
CREATE CONSTRAINT partido_id_unique   FOR (p:Partido)   REQUIRE p.partidoId   IS UNIQUE;
CREATE CONSTRAINT estadio_id_unique   FOR (e:Estadio)   REQUIRE e.estadioId   IS UNIQUE;
CREATE CONSTRAINT evento_id_unique    FOR (e:Evento)    REQUIRE e.eventoId    IS UNIQUE;
```

Las cinco etiquetas del modelo tienen una restricción de unicidad sobre su
identificador de negocio. Esto además crea automáticamente un índice
respaldo para cada una (búsquedas por ID son O(1) en vez de escanear la
etiqueta), y es lo que permite que la carga con `MERGE` sea idempotente
(RNF4): un `MERGE` por una propiedad con restricción de unicidad nunca puede
crear un duplicado.

## 6. Índices adicionales (`queries/indices.cypher`, RF10)

| Índice | Motivo |
|---|---|
| `Seleccion.pais` | Varias consultas de recuperación filtran por nombre de país (`"Argentina"`) en vez del código interno. |
| `Jugador.posicion` | Filtro frecuente para armar planteles por rol (arqueros, defensores, etc.). |
| `Partido.fecha` | Acceso típico de un calendario/fixture: ordenar y filtrar partidos por fecha. |
| `Estadio.pais` | Agrupar/filtrar partidos o sedes por país anfitrión. |

No se creó índice sobre `Partido.fase` ni `Evento.tipo`: tienen muy baja
cardinalidad (5-8 valores distintos) frente al volumen de nodos, así que un
escaneo completo de la etiqueta ya es barato y el índice sólo agregaría
costo de mantenimiento en cada carga sin acelerar ninguna consulta real de
este módulo.

## 7. Diagrama del modelo

```
(:Jugador {jugadorId, nombre, apellido, posicion, dorsal, ...})
     -[:PERTENECE_A]-> (:Seleccion {seleccionId, pais, confederacion, grupo, ranking, ...})
                              -[:PARTICIPA_EN {rol, goles, golesRecibidos, resultado}]-> (:Partido {partidoId, fecha, fase, estado, ...})
                                                                                              -[:SE_JUEGA_EN]-> (:Estadio {estadioId, nombre, ciudad, pais, capacidad})

(:Evento {eventoId, tipo, minuto, descripcion})
     -[:OCURRE_EN]-> (:Partido)
     -[:PROTAGONIZADO_POR]-> (:Jugador)
```

## 8. Volumen cargado (RF6)

64 `Seleccion` · 1536 `Jugador` · 16 `Estadio` · 128 `Partido` (96 fase de
grupos + 32 eliminatorias) · 591 `Evento` — ver `docs/decisiones.md` §4 para
el detalle de cómo se generó el fixture y `evidencias/evidencia_subgrafo_completo.txt`
para el conteo verificado de nodos y relaciones.
