# Decisiones de diseño — Fixture 2030 (Hito 5)

## 1. Problema relacional

El módulo documental (Hito 4, MongoDB) resuelve bien preguntas sobre una
entidad aislada: "¿quién es el jugador X?", "¿qué selecciones hay en el grupo
A?". Pero el Fixture 2030 necesita responder preguntas que **atraviesan
varias entidades a la vez**, y ahí una colección documental obliga a hacer
varios `$lookup`/joins manuales o a desnormalizar de antemano:

- ¿En qué estadios juega la selección de un jugador determinado, y cuándo?
  (Jugador → Selección → Partido → Estadio.)
- ¿Qué eventos (goles, tarjetas) ocurrieron en los partidos de una selección
  puntual? (Selección → Partido ← Evento.)
- ¿Qué tan "lejos" está una selección de otra dentro del torneo —cuántos
  partidos/sedes hay que atravesar para conectarlas— si nunca compartieron
  grupo? (Recorrido de longitud variable / camino más corto.)
- ¿Qué sedes concentran más partidos y por lo tanto más carga logística?
- ¿Quiénes son las selecciones más "conectadas" del fixture (más partidos,
  más rivales distintos)?

Estas preguntas son navegación de relaciones, no recuperación de un
documento: exactamente el caso de uso que justifica un modelo de grafos
sobre el mismo dominio que el Hito 4, sin reemplazarlo.

## 2. Modelo propuesto

Ver `docs/modelo_grafo.md` para el detalle completo de etiquetas,
propiedades, relaciones (con dirección y cardinalidad) y diagrama. En
resumen:

- **Nodos:** `Jugador`, `Seleccion`, `Partido`, `Estadio`, `Evento`.
- **Relaciones:** `PERTENECE_A` (Jugador→Selección), `PARTICIPA_EN`
  (Selección→Partido, con `rol`/`goles`/`resultado`), `SE_JUEGA_EN`
  (Partido→Estadio), `OCURRE_EN` (Evento→Partido), `PROTAGONIZADO_POR`
  (Evento→Jugador).

## 3. Decisiones de diseño y vínculo con los Hitos 1 a 4

- **D1 — Identificadores compartidos con el Hito 4 (RF5, RNF6).**
  `Seleccion.seleccionId` y `Jugador.jugadorId` son literalmente el `_id` de
  las colecciones `equipos`/`jugadores` del Hito 4. Se cargan leyendo los
  mismos archivos JSON (`data/equipos.json`, `data/jugadores.json`) con
  `scripts/load_data.py`, así que un mismo jugador o selección se reconoce
  con el mismo identificador en ambos módulos sin necesidad de tabla de
  mapeo. Esto responde directamente a la pregunta guía 4 del enunciado.

- **D2 — `confederacion`, `grupo` y `fase` como propiedades, no como nodos.**
  Se evaluó modelarlos como nodos (`:Confederacion`, `:Grupo`, `:Fase`) con
  una relación `AFILIADO_A`/`INTEGRA`/`CORRESPONDE_A`, pero se descartó: son
  atributos de muy baja cardinalidad (6, 16 y 6 valores respectivamente)
  sin propiedades propias más allá del nombre, y ninguna consulta de este
  módulo necesita recorrerlos como entidad intermedia (agrupar por
  `s.confederacion` alcanza). Agregarlos como nodos sólo hubiera sumado
  relaciones sin ganar capacidad de consulta — se prefirió el modelo más
  simple que resuelve las mismas preguntas.

- **D3 — Resultado del partido en dos niveles (Partido y PARTICIPA_EN).**
  `Partido.golesLocal/golesVisitante` guarda el resultado del encuentro;
  `PARTICIPA_EN.goles/golesRecibidos/resultado` guarda el mismo resultado
  pero *desde la perspectiva de cada selección* (para poder responder "¿cuál
  fue el resultado de Argentina en este partido?" sin tener que comparar
  `rol` contra `golesLocal/golesVisitante` en cada consulta). No es
  duplicación redundante: son dos niveles de lectura distintos que ya vienen
  resueltos en la carga (`scripts/generar_fixture.py`), evitando
  recalcularlos en cada consulta.

- **D4 — Evento como nodo, no como propiedad de Partido.**
  Cada partido tiene entre 0 y varios eventos (goles y tarjetas), cada uno
  con su propio minuto y protagonista. Una propiedad (o incluso un array de
  mapas) en `:Partido` no permitiría indexar, filtrar ni vincular cada
  evento a un jugador real sin desnormalizar texto libre. Modelarlo como
  nodo con `OCURRE_EN`/`PROTAGONIZADO_POR` resuelve RF3 (identificar
  eventos deportivos) y habilita RF8/RF9 sin trucos.

- **D5 — `PROTAGONIZADO_POR` como relación adicional.**
  No la exige RF4 (que sólo pide vincular el evento con *el partido*), pero
  vincular el evento con *el jugador* real (en vez de guardar sólo el nombre
  como texto en `descripcion`) evita inconsistencias si el nombre de un
  jugador cambiara, y habilita la consulta de centralidad de RF9 §3
  ("figuras del torneo" por cantidad de eventos protagonizados).

- **D6 — Carga híbrida: Python (driver oficial) + Cypher.**
  Equipos/jugadores y el fixture generado se cargan con scripts Python
  (`scripts/load_data.py`, `scripts/generar_fixture.py`) que usan `MERGE`
  para toda escritura; las restricciones, índices, el CRUD de demostración y
  las consultas de recuperación/análisis quedan en archivos `.cypher`
  separados por propósito (RNF5). La sección 5.3 del enunciado permite
  explícitamente "sentencias Cypher, archivos de importación u otro
  procedimiento compatible": se eligió Python porque generar de forma
  determinística un fixture de 128 partidos con resultados y eventos
  coherentes (ver §4) es mucho más manejable con lógica de programación
  (round-robin, tabla de posiciones, llaves de eliminatorias) que con Cypher
  puro, sin perder reproducibilidad ni idempotencia.

- **D7 — Direcciones de relación: de lo específico a lo general/contenedor.**
  Todas las relaciones apuntan "hacia arriba" (Jugador→Selección,
  Evento→Partido, Evento→Jugador) o hacia la entidad de la que se participa
  (Selección→Partido, Partido→Estadio). Responde a la pregunta guía 3: los
  recorridos típicos ("¿a qué selección pertenece?", "¿en qué partido
  ocurrió?") son un `MATCH` directo con la flecha; los recorridos inversos
  ("¿qué jugadores tiene?", "¿qué eventos tuvo?") simplemente invierten el
  sentido del patrón — Cypher recorre relaciones en ambos sentidos con el
  mismo costo, así que la dirección es una decisión de legibilidad del
  modelo, no de rendimiento.

- **D8 — Consistencia con Hitos 1-3.** El dominio (Mundial de 64 equipos,
  16 grupos de 4, fase de grupos + eliminatorias) y el vocabulario
  (selección, plantel, fase, sede) son los mismos definidos desde el Hito 1;
  este módulo no introduce entidades nuevas fuera de ese dominio (partidos,
  sedes y eventos ya estaban previstos como parte del "fixture" desde el
  planteo original del proyecto).

## 4. Datos cargados

- **Equipos y jugadores (RF6, alta prioridad):** se leen tal cual de
  `data/equipos.json` (64 selecciones) y `data/jugadores.json` (1536
  jugadores, 24 por selección) — los mismos archivos del Hito 4 — con
  `scripts/load_data.py`. Ningún dato se inventa en este paso.

- **Fixture (partidos, sedes, eventos):** el enunciado permite generarlos o
  seleccionarlos siempre que sean consistentes con un Mundial de 64 equipos
  (sección 5.3). Se generan con `scripts/generar_fixture.py`, determinístico
  (semilla fija `SEED = 2030`, ver RNF4):
  1. **16 sedes** (`EST01`..`EST16`) repartidas entre los seis países
     anfitriones reales del Mundial 2030 (Argentina, Uruguay, Paraguay,
     España, Portugal y Marruecos).
  2. **Fase de grupos:** round-robin completo dentro de los 16 grupos ya
     cargados en `Seleccion.grupo` (6 partidos × 16 grupos = 96 partidos).
     El resultado de cada partido se simula con una probabilidad de gol
     proporcional al ranking FIFA de cada selección (no son goles al azar
     uniforme: una selección mejor rankeada tiene más chances de convertir
     y menos de recibir).
  3. **Tabla de posiciones y clasificación:** se calculan puntos, diferencia
     de gol y goles a favor por grupo para determinar los 2 clasificados de
     cada uno (32 selecciones).
  4. **Eliminatorias:** dieciseisavos (16 partidos) → octavos (8) → cuartos
     (4) → semifinales (2) → tercer puesto y final (1 cada uno) = 32
     partidos, con emparejamientos cruzados clásicos entre grupos
     adyacentes y definición por penales si hay empate. Total: **128
     partidos**, entre el 8 de junio y el 4 de octubre de 2030 (fechas
     comprimidas a 8 partidos/día en la fase de grupos para que la ventana
     del torneo sea realista).
  5. **Eventos:** por cada partido se generan tantos goles como indica el
     marcador (asignados con más probabilidad a delanteros/mediocampistas
     del equipo que anotó) y una cantidad variable de tarjetas
     amarillas/rojas (asignadas a cualquier jugador de ambos planteles, con
     algo más de probabilidad para defensores/mediocampistas). Total: **591
     eventos** (421 goles, 166 amarillas, 4 rojas).

- **Controles de coherencia aplicados por el generador:**
  - Ningún `partidoId` se repite (verificado: 128 IDs únicos sobre 128
    partidos).
  - La cantidad de eventos de tipo "Gol" por partido coincide exactamente
    con `golesLocal + golesVisitante` de ese partido (verificado sobre las
    128 filas antes de cargar).
  - Los 2 clasificados de cada grupo a eliminatorias surgen de la tabla de
    posiciones real calculada sobre los resultados simulados, no de una
    lista arbitraria.
  - Al ejecutarse, el script elimina primero el partido y el evento de
    prueba manual (`P001`/`EV001`) creados durante la exploración inicial
    del modelo, que mezclaban selecciones de grupos distintos (ARG vs BRA)
    y quedaban fuera de la fase de grupos round-robin generada — ver la
    nota en `queries/carga_fixture.cypher`.

- **Alcance:** no se pretende reproducir el fixture real de un Mundial 2030
  (los resultados son simulados), sino tener una muestra completa y
  coherente —fase de grupos entera más una llave de eliminatorias
  completa— que sea suficiente para validar todos los recorridos exigidos
  (RF6, RF8, RF9) sobre un volumen realista.

## 5. Consultas

Ver `queries/consultas.cypher` (recuperación/agregación + las 2 consultas
multi-salto de RF8), `queries/crud.cypher` (RF7) y `queries/analisis.cypher`
(RF9). Resumen de propósito:

| Archivo | Consulta | Propósito |
|---|---|---|
| `consultas.cypher` #1-2 | Plantel por selección / filtro por posición | Recuperación básica con filtro. |
| `consultas.cypher` #3 | Capitanes por selección | Filtro + recorrido simple. |
| `consultas.cypher` #4-7 | Conteos y promedios | Agregación (`count`, `avg`). |
| `consultas.cypher` #8 | Compañeros de selección de un jugador | Recorrido de 2 saltos (mismo tipo de relación, ida y vuelta). |
| `consultas.cypher` #9 | Jugador→Selección→Partido→Estadio | **RF8:** 3 relaciones consecutivas — sedes donde jugó la selección de un jugador. |
| `consultas.cypher` #10 | Selección→Partido←Evento | **RF8:** 2 relaciones consecutivas convergentes — eventos de los partidos de una selección. |
| `crud.cypher` | Alta/lectura/edición/baja de un jugador y un evento de prueba | **RF7:** ciclo CRUD completo sobre etiquetas reales, con borrado acotado. |
| `analisis.cypher` | Ver §7 | **RF9.** |

La evidencia de los resultados reales de cada una está en `evidencias/` (ver
§7 de este documento y el README).

## 6. Integridad y rendimiento

- **Restricciones (RF10):** unicidad de `jugadorId`, `seleccionId`,
  `partidoId`, `estadioId`, `eventoId` — evita duplicados por `MERGE`
  (RNF4) y son la base de la idempotencia de la carga (ver
  `docs/modelo_grafo.md` §5 y `evidencias/evidencia_constraints_indices.txt`).
- **Índices (RF10):** `Seleccion.pais`, `Jugador.posicion`, `Partido.fecha`,
  `Estadio.pais` — elegidos porque son exactamente los campos de filtro
  usados en `consultas.cypher` (ver justificación completa en
  `docs/modelo_grafo.md` §6). Deliberadamente no se indexó `Partido.fase` ni
  `Evento.tipo` por su baja cardinalidad.
- **Recorridos frecuentes** que se beneficiaron de esta combinación de
  restricciones + índices: búsqueda de un jugador/selección/partido por ID
  (constraint), filtro de jugadores por posición o selección por país
  (índice), y filtrado/orden de partidos por fecha (índice).

## 7. Análisis relacional (RF9)

Se implementaron dos análisis en `queries/analisis.cypher` (detalle y
resultados verificados en `evidencias/evidencia_analisis_rf9.txt`):

1. **Camino más corto (conectividad) entre dos selecciones.** Usando
   `shortestPath()` sobre `PARTICIPA_EN`/`SE_JUEGA_EN` como grafo no
   dirigido, se calculó el camino más corto entre Argentina (grupo A) y
   Japón (grupo E), que no comparten grupo. Resultado: **4 saltos**, porque
   —según el sorteo de eliminatorias generado a partir de las posiciones de
   grupo— terminaron enfrentándose directamente en Octavos de Final.
   **Qué aporta al Fixture 2030:** permite responder "¿qué tan conectadas
   están dos selecciones dentro del torneo?" sin reconstruir manualmente la
   llave de eliminatorias, y sirve como control de coherencia del propio
   fixture generado (un camino inesperadamente largo indicaría un bracket
   mal formado).

2. **Centralidad de grado de estadios.** Conteo de partidos alojados por
   cada sede (grado de entrada de `SE_JUEGA_EN`). Resultado: entre 7 y 9
   partidos por sede, con el estadio elegido para la Final levemente por
   encima. **Qué aporta:** identifica qué sedes concentran más carga
   operativa (seguridad, transporte, logística) sin tener que agregar
   partido por partido.

3. **(Complementaria) Centralidad de grado de jugadores por eventos
   protagonizados** (`PROTAGONIZADO_POR`): quiénes concentran más goles y
   tarjetas, útil para un tablero de "figuras del torneo".

## Cobertura de requisitos

| Req. | Dónde se cumple |
|---|---|
| RF1 | `docker-compose.yml` (Neo4j Browser en `:7474`, Bolt en `:7687`) |
| RF2 | `docs/modelo_grafo.md` |
| RF3 | 5 etiquetas de nodo, justificadas en §3 (D2, D4) |
| RF4 | `PERTENECE_A`, `PARTICIPA_EN`, `SE_JUEGA_EN`, `OCURRE_EN` |
| RF5 | `seleccionId`/`jugadorId` = `_id` del Hito 4 (§3 D1) |
| RF6 | `scripts/load_data.py` (64 selecciones, 1536 jugadores) + `scripts/generar_fixture.py` (16 sedes, 128 partidos, 591 eventos) |
| RF7 | `queries/crud.cypher` · evidencia `evidencias/evidencia_crud.txt` |
| RF8 | `queries/consultas.cypher` #9 y #10 (2+ relaciones consecutivas) · evidencia `evidencias/evidencia_multisalto.txt` |
| RF9 | `queries/analisis.cypher` · interpretación en §7 · evidencia `evidencias/evidencia_analisis_rf9.txt` |
| RF10 | `queries/constraints.cypher` + `queries/indices.cypher` · evidencia `evidencias/evidencia_constraints_indices.txt` |
| RF11 | `evidencias/` (capturas + evidencia de texto) |
| RNF1 | `image: neo4j:latest`, sin versión fijada |
| RNF2 | Volúmenes nombrados (`neo4j_data`, `neo4j_logs`, `neo4j_import`, `neo4j_plugins`) |
| RNF3 | README + `.env.example` + scripts reproducibles |
| RNF4 | `MERGE` en toda la carga · evidencia `evidencias/evidencia_carga_idempotente.txt` |
| RNF5 | Archivos `.cypher`/`.py` separados por propósito y comentados |
| RNF6 | Identificadores del Hito 4 · trazabilidad con Hitos 1-3 (§3 D8) |
| RNF7 | Cada consulta devuelve un resultado verificable contra los datos cargados (ver evidencias) |
| RNF8 | Credenciales por variables de entorno (`.env`, excluido por `.gitignore`); `.env.example` versionado |
