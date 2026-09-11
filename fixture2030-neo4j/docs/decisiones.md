# Análisis y decisiones de diseño — Módulo de grafos del Fixture 2030

**Grupo 12** · Ingeniería de Datos II · Hito 5
Integrantes: Dayana Peñaloza · Franco Churba · Juan Bautista Mangoni

Este documento cubre los siete apartados exigidos por la sección 8 de los
requisitos técnicos. El detalle del modelo está en
[`modelo_grafo.md`](modelo_grafo.md); la evidencia técnica, en
[`evidencia/`](evidencia/).

---

## 1. Problema relacional

### 1.1 Por qué el Hito 5 no reemplaza al Hito 4

El módulo documental (Hito 4) responde muy bien a una clase de preguntas: *dame
el documento del jugador `ARG-10`*, *listame el plantel de una selección*,
*actualizá la ficha de un equipo*. Son accesos por identificador o por un campo
de un documento, y MongoDB los resuelve con un índice y una lectura.

Lo que ese modelo no resuelve con naturalidad son las preguntas cuya respuesta
**no está en ningún documento**, sino en la forma en que los documentos se
encadenan. En una colección de partidos, el documento de `F2030-124` sabe que
Suecia enfrentó a Uruguay; no sabe que Uruguay llegó ahí tras eliminar a
Bolivia, que Bolivia venía del Grupo N, ni que Nueva Zelanda está a dos cruces
de distancia de Uruguay. Cada uno de esos pasos exige una consulta adicional
desde la aplicación, y la cantidad de consultas crece con la profundidad del
recorrido.

En un grafo, esas mismas preguntas son un único patrón y su costo depende del
vecindario recorrido, no del tamaño total de la base.

### 1.2 Preguntas del Fixture 2030 que motivan el grafo

| # | Pregunta | Relaciones a recorrer | Consulta |
|---|---|---|---|
| P1 | ¿Contra quién jugó una selección y con qué resultado? | 2 | 4.3 |
| P2 | ¿Qué jugadores rivales enfrentó una selección a lo largo del torneo? | 3 | 4.4 |
| P3 | ¿Quiénes son los goleadores, de qué selección y en qué fases convirtieron? | 4 | 4.5 |
| P4 | ¿Qué selecciones jugaron en un estadio de su propio país? | 3 (ciclo) | 4.6 |
| P5 | ¿Qué camino recorrió el campeón desde su debut hasta la final? | 2 | 4.8 |
| P6 | ¿Con qué selecciones no se cruzó un equipo, pero sí sus rivales? | 4 | 4.9 |
| P7 | ¿Quién vio la roja, de qué selección, en qué partido y en qué sede? | 4 | 4.11 |
| P8 | ¿Cuál es la cadena de enfrentamientos más corta entre dos selecciones que nunca se enfrentaron? | variable | 5.1 |
| P9 | ¿Qué selecciones sostuvieron estructuralmente el torneo? | toda la red | 5.3 |

Las preguntas P8 y P9 son las que mejor ilustran el punto: **su respuesta no
está contenida en ningún registro**. P8 requiere explorar la red hasta
encontrar el camino mínimo —sin saber de antemano cuántos saltos hacen falta—
y P9 depende de la topología completa de la red de enfrentamientos.

### 1.3 Qué queda en cada módulo

| Necesidad | Módulo | Motivo |
|---|---|---|
| Ficha completa de un equipo o jugador | MongoDB (Hito 4) | Acceso por clave a un documento autocontenido |
| Alta y edición de planteles | MongoDB (Hito 4) | Validación de esquema con `$jsonSchema` |
| Navegación del fixture, rivales y eventos | **Neo4j (Hito 5)** | Recorridos de 2 a 4 relaciones |
| Análisis de caminos y centralidad | **Neo4j (Hito 5)** | Algoritmos de grafos sobre la red completa |

---

## 2. Modelo propuesto

Resumen; el detalle completo con propiedades y cardinalidades está en
[`modelo_grafo.md`](modelo_grafo.md).

**8 etiquetas de nodo:** `:Seleccion` (64), `:Jugador` (1.536), `:Partido` (128),
`:Estadio` (18), `:Evento` (753), `:Confederacion` (6), `:Grupo` (16), `:Fase` (7)
— **2.528 nodos**.

**9 tipos de relación:** `:PERTENECE_A`, `:AFILIADO_A`, `:INTEGRA`,
`:PARTICIPA_EN`, `:SE_JUEGA_EN`, `:CORRESPONDE_A`, `:EN_PAIS_DE`,
`:OCURRE_EN`, `:PROTAGONIZADO_POR` — **3.700 relaciones**.

Cubre con holgura el mínimo del RF3 (equipos, jugadores, partidos, eventos y
sedes) y del RF4 (pertenencia, participación, programación en sede y vínculo de
eventos con su partido).

---

## 3. Decisiones de diseño

### D1 — Los identificadores del Hito 4 son la clave primaria del grafo

`:Seleccion.seleccionId` y `:Jugador.jugadorId` son, carácter por carácter, los `_id`
de las colecciones `equipos` y `jugadores` del módulo documental.

*Alternativa descartada:* usar el identificador interno de Neo4j o un UUID
propio y guardar el id de Mongo como atributo secundario. Se descartó porque
obligaría a mantener una tabla de correspondencia entre módulos, que es
exactamente la fuente de inconsistencia que el RF5 busca evitar.

*Refuerzo:* el dataset no se transcribe: `import/generar_dataset.py` **lee los
JSON del Hito 4**. Si el módulo documental cambia, el grafo cambia con él.
Verificado en los controles 6.6.1–6.6.3: 1.536/1.536 prefijos coincidentes.

### D2 — Confederación, Grupo y Fase son nodos, no cadenas de texto

Podrían haber sido propiedades (`e.confederacion = 'UEFA'`). Se modelaron como
nodos porque son **puntos de reunión** del recorrido: permiten preguntar
"¿cuántos cruces hubo entre confederaciones?" (consulta 5.2.1) navegando el
grafo, y garantizan un único valor canónico —con propiedad `codigo` bajo
restricción de unicidad— en lugar de 64 cadenas repetidas que podrían diverger
por un error de tipeo.

`:Fase` además lleva `orden` (1–7), lo que permite recorrer el torneo en
secuencia cronológica sin interpretar el nombre de la fase.

*Contraejemplo deliberado:* `posicion` del jugador y `ciudad` de la sede
quedaron como propiedades. No son puntos de reunión de ningún recorrido: nadie
pregunta "qué comparten los delanteros entre sí" navegando relaciones.

### D3 — El dorsal y la capitanía son propiedades del nodo `:Jugador`

`(:Jugador {dorsal, capitan})-[:PERTENECE_A]->(:Seleccion)`

Se evaluó la alternativa de guardarlos en la relación
`(:Jugador)-[:PERTENECE_A {dorsal, capitan}]->(:Seleccion)`, con el argumento
de que el número de camiseta describe la *convocatoria* y no a la persona: el
mismo futbolista podría tener otro dorsal en otro torneo.

**Se descartó por coherencia con el Hito 4 (RNF6).** En el documento del
jugador del módulo documental, `dorsal` y `capitan` son campos del propio
jugador. Separarlos acá obligaría a recordar que la misma información se lee de
dos lugares distintos según la base que se consulte, y dejaría a las consultas
de plantel de este hito sin correspondencia directa con las del Hito 4. Además,
el Fixture 2030 es un torneo único: cada jugador tiene exactamente una
convocatoria, así que la flexibilidad que daría ponerlos en la relación no se
usaría.

El ejemplo de propiedades sobre una relación lo aporta `:PARTICIPA_EN`
(decisión D4), donde el dato **sí** es irreductiblemente del vínculo: los goles
de un equipo en un partido no pertenecen ni al equipo ni al partido por
separado.

### D4 — `:PARTICIPA_EN` lleva el resultado de ese equipo en ese partido

`(:Seleccion)-[:PARTICIPA_EN {rol, goles, golesRecibidos, resultado}]->(:Partido)`

`rol` (local/visitante) y `goles` no pertenecen ni al equipo ni al partido por
separado: describen el cruce entre ambos. Dos relaciones por partido bastan
para reconstruir el marcador desde cualquiera de los dos lados.

*Consecuencia práctica:* la tabla de posiciones (consulta 4.7) **no se
almacena**: se calcula sumando `resultado` sobre las relaciones. No hay puntos
precalculados que puedan quedar desactualizados respecto de los partidos.

*Alternativa descartada:* dos tipos de relación separados (`:JUEGA_DE_LOCAL` y
`:JUEGA_DE_VISITANTE`). Habría obligado a escribir dos patrones en cada
consulta de rivales, cuando el 80 % de las preguntas no distingue la localía.

### D5 — La sede se vincula al país anfitrión por relación

`(:Estadio)-[:EN_PAIS_DE]->(:Seleccion)`

Aprovecha que el país anfitrión de un estadio **es** una de las 64 selecciones,
identificada con el mismo código FIFA. Esa relación habilita un recorrido que
con una propiedad de texto sería imposible de expresar como patrón: el ciclo de
la consulta 4.6, que parte de un equipo y vuelve a él pasando por un partido y
una sede, para detectar quién jugó realmente en su propio país.

### D6 — El evento es un nodo, no una propiedad del partido

Un gol tiene **dos vínculos independientes**: el partido donde ocurrió y el
jugador que lo convirtió. Como propiedad embebida en el documento del partido
—la forma natural en el módulo documental— el segundo vínculo se pierde: para
armar la tabla de goleadores habría que recorrer los 128 partidos y agrupar por
un identificador de jugador del lado de la aplicación. Como nodo, la tabla de
goleadores es un solo patrón de cuatro relaciones (consulta 4.5).

Es el mejor ejemplo de la complementariedad entre los dos hitos: la misma
información que en Mongo conviene embeber, en el grafo conviene separar.

### D7 — Sin relación materializada de rivalidad

Se evaluó crear `(:Seleccion)-[:ENFRENTO]->(:Seleccion)` para acelerar las consultas
de rivales. Se descartó: sería información derivada, redundante con
`:PARTICIPA_EN`, y habría que mantenerla sincronizada ante cada alta o
corrección de partido —una fuente de inconsistencia a cambio de un salto menos
en un grafo de 128 partidos. Cuando el análisis la necesita como grafo propio
(centralidad, sección 5.3), se la **proyecta en memoria con GDS** y se la
descarta al terminar, sin tocar los datos persistidos.

### D8 — Vínculo con los Hitos 1 a 3

| Hito | Decisión previa | Cómo se sostiene acá |
|---|---|---|
| Hito 1 | El fixture se identificó como dominio altamente conectado (equipos, partidos, sedes, eventos) | Es exactamente el subgrafo implementado |
| Hito 2 | La matriz de decisión asignó a cada necesidad el motor adecuado, reservando el grafo para las relaciones deportivas | El módulo se limita a relaciones: no duplica la ficha documental |
| Hito 3 | Arquitectura poliglota con un módulo por tipo de necesidad y consistencia por identificadores compartidos | Neo4j es un módulo más; la integración es **semántica** (mismos `_id`), sin acoplamiento por código, tal como habilita la restricción de implementación del enunciado |
| Hito 4 | `_id` naturales: `ARG` y `ARG-10` | Son las claves del grafo (D1) |

---

## 4. Datos cargados

### 4.1 Origen

| Entidad | Origen | Cantidad |
|---|---|---|
| Equipos | **Leídos del Hito 4** (`equipos.json`) | 64 |
| Jugadores | **Leídos del Hito 4** (`jugadores.json`) | 1.536 |
| Estadios | Definidas por el grupo: 18 estadios reales de los 6 países anfitriones | 18 |
| Partidos | Generados: fixture completo de un Mundial de 64 equipos | 128 |
| Participaciones | Derivadas de los partidos | 256 |
| Eventos | Generados de forma coherente con cada marcador | 753 |

Supera el mínimo del RF6 (64 equipos y más de 1.000 jugadores) y agrega una
muestra suficiente de partidos, sedes y eventos para validar todos los
recorridos.

### 4.2 Estructura del torneo generado

Fase de grupos de 16 grupos (A–P) de 4 selecciones, 3 jornadas, 96 partidos;
eliminatorias de 32 (dieciseisavos, 16), octavos (8), cuartos (4), semifinales
(2), tercer puesto (1) y final (1). **128 partidos, del 13/06 al 17/07 de 2030.**

Los resultados **no son aleatorios en cada corrida**: se simulan con una
distribución de Poisson cuya media depende del ranking FIFA de cada selección,
con semilla fija `SEED = 2030` —la misma del generador del Hito 4—. Las
eliminatorias se arman a partir de las **posiciones reales** de cada grupo
(puntos, diferencia de gol, goles a favor, ranking), de modo que el cuadro es
consecuencia de los resultados y no una lista inventada.

Detalles de realismo incorporados:

- las tres sedes sudamericanas (Centenario, Monumental y Defensores del Chaco)
  reciben un partido cada una, homenaje del centenario de 1930, y el resto del
  torneo se juega en España, Portugal y Marruecos;
- la final se disputa en el Santiago Bernabéu;
- ninguna selección juega dos partidos el mismo día y ninguna sede recibe dos
  partidos en el mismo día y horario.

Campeón del torneo generado: **Uruguay**, que venció 2-0 a Alemania en la final
(`F2030-128`).

### 4.3 Controles de coherencia

El generador **falla antes de escribir** si alguna de estas condiciones no se
cumple (`import/generar_dataset.py`):

- 64 equipos y más de 1.000 jugadores;
- cantidad de partidos exacta por fase (96/16/8/4/2/1/1);
- los eventos de gol de cada equipo en cada partido **coinciden con el
  marcador**;
- ningún evento atribuido a un jugador que no pertenece a un equipo de ese
  partido;
- sin identificadores duplicados; todas las sedes con al menos un partido;
  ninguna selección con dos partidos el mismo día.

Ya cargados en Neo4j, los mismos controles se repiten **sobre el grafo** en
`queries/verificacion.cypher` (sección 6), más los de cardinalidad y
trazabilidad. Evidencia:
[`evidencia/05_verificacion_coherencia.txt`](evidencia/05_verificacion_coherencia.txt).

### 4.4 Mecanismo de carga e idempotencia

`LOAD CSV` desde el directorio de importación montado en el contenedor, con
`MERGE` sobre identificadores bajo restricción de unicidad, tanto para nodos
como para relaciones.

La prueba está en
[`evidencia/04_carga_idempotente.txt`](evidencia/04_carga_idempotente.txt): dos
corridas consecutivas de `carga.cypher` sobre el mismo ambiente dejan
**2.528 nodos y 3.700 relaciones** en ambos casos, y la consulta que busca
relaciones paralelas entre el mismo par de nodos no devuelve ninguna fila.

Y la generación del dataset también es reproducible: dos corridas del generador
producen CSV con **idénticas huellas MD5**
([`evidencia/02_generacion_dataset.txt`](evidencia/02_generacion_dataset.txt)).

---

## 5. Consultas

Catálogo completo en [`../queries/consultas_grafo.cypher`](../queries/consultas_grafo.cypher);
resultados reales en [`evidencia/07_consultas_grafo.txt`](evidencia/07_consultas_grafo.txt).

| # | Propósito | Saltos | Resultado obtenido |
|---|---|---|---|
| 4.1 | Plantel de una selección con dorsales | 1 | 24 jugadores de Uruguay, capitán incluido |
| 4.2 | Agenda de una fecha con sede y rivales | 2 | 2 partidos del 13/06 en Buenos Aires y Asunción |
| 4.3 | Rivales de Argentina y resultados | 2 | 3 cruces: derrota, empate, derrota |
| **4.4** | **Delanteros rivales enfrentados por Uruguay** | **3** | 8 selecciones con sus delanteros |
| **4.5** | **Tabla de goleadores con fases** | **4** | 6 goleadores con 3 goles cada uno |
| **4.6** | **Localía real (ciclo sobre el mismo nodo)** | **3** | España 4 partidos en casa y 4 victorias; los otros 3 anfitriones, 1 cada uno |
| 4.7 | Tabla de posiciones del Grupo A | 2 | España 9 pts, Uruguay 4, Paraguay 3, Argentina 1 |
| **4.8** | **Camino completo del campeón** | **2** | Los 8 partidos de Uruguay, de Asunción al Bernabéu |
| **4.9** | **Rivales de rivales (2.º grado)** | **4** | Francia y Brasil, a un cruce de España |
| 4.10 | Uso de las sedes | 2 | Camp Nou 11 partidos y 17 selecciones distintas |
| **4.11** | **Expulsiones con contexto** | **4** | Rojas con jugador, selección, minuto y ciudad |
| 4.12 | Búsqueda de jugador por índice de texto completo | 2 | Búsqueda difusa `Pérez~`: 10 coincidencias ordenadas por relevancia |
| 4.13 | Partidos con más goles (filtro + orden + paginación) | 2 | Países Bajos 5-3 Alemania encabeza con 8 goles |
| 4.14 | Subgrafo de la final para Neo4j Browser | 3 | Vista de grafo de la final |

Seis consultas recorren **dos o más relaciones consecutivas**, por encima del
mínimo de dos que exige el RF8.

Operaciones CRUD en [`../queries/crud.cypher`](../queries/crud.cypher)
(evidencia [`06_crud.txt`](evidencia/06_crud.txt)): alta de un amistoso con
sede y participaciones, lectura por patrón, actualización de propiedades,
etiquetas y relaciones, y eliminación acotada. **Todo lo que crea lleva la
etiqueta `:Prueba` y toda sentencia de borrado filtra por ella**: al terminar,
los conteos del torneo vuelven a 64/1.536/128/18/753 y las 256 participaciones,
como muestra la evidencia. Nunca se usa `MATCH (n) DETACH DELETE n`.

---

## 6. Integridad y rendimiento

### 6.1 Restricciones

8 restricciones de unicidad, una por identificador de entidad
([`modelo_grafo.md` §4.1](modelo_grafo.md#41-restricciones-de-unicidad-8)).
Cumplen dos funciones: impedir entidades duplicadas y **sostener la
idempotencia** de la carga, ya que cada `MERGE` opera sobre una propiedad con
restricción.

Las restricciones de existencia y de tipo no están disponibles en Neo4j
Community; se suplen con `MERGE` sobre la clave y con los controles explícitos
de `verificacion.cypher`.

### 6.2 Índices y su efecto medido

8 índices declarados (6 RANGE y 2 FULLTEXT), cada uno asociado a una consulta
concreta del catálogo. La evidencia
[`09_rendimiento_indices.txt`](evidencia/09_rendimiento_indices.txt) contiene
los planes de ejecución reales con `PROFILE`:

| Consulta | Operador del plan | Accesos a base de datos |
|---|---|---|
| Agenda por fecha (`p.fecha`, **con** índice) | `NodeIndexSeek` | **34** |
| Conteo por estado (`p.estado`, **sin** índice) | `NodeByLabelScan` | **257** |
| Seleccion por `seleccionId` (restricción de unicidad) | `NodeUniqueIndexSeek` | 62 |
| Top 10 del ranking (`e.ranking`) | `NodeIndexSeekByRange` | 21 |

El contraste entre las dos primeras filas es la justificación empírica de los
índices: el mismo tipo de filtro sobre la misma etiqueta cuesta **7,5 veces
más** sin índice, y la diferencia crece con el tamaño del torneo.

### 6.3 Recorridos frecuentes

Las consultas más habituales durante el torneo (agenda del día, ficha de un
partido, plantel de una selección) parten siempre de un nodo localizado por
índice y recorren de 1 a 3 relaciones. Ese es el patrón que Neo4j resuelve con
costo proporcional al vecindario: los 1.536 jugadores o los 753 eventos no
intervienen si no están en el camino.

---

## 7. Análisis relacional

Archivo: [`../queries/analisis_relacional.cypher`](../queries/analisis_relacional.cypher) ·
Evidencia: [`evidencia/08_analisis_relacional.txt`](evidencia/08_analisis_relacional.txt)

El objeto de análisis es la **red de rivalidades**: dos selecciones están
conectadas si compartieron al menos un partido. Esa red **no está almacenada**
—no existe ninguna relación `Seleccion→Seleccion`—: emerge del patrón
`(Seleccion)-[:PARTICIPA_EN]->(Partido)<-[:PARTICIPA_EN]-(Seleccion)`.

### 7.1 Camino más corto — grados de separación

**Objetivo:** medir la distancia competitiva entre dos selecciones que nunca se
enfrentaron y exhibir la cadena que las une.

**Resultado:** Uruguay y Nueva Zelanda, que no se cruzaron, están a **2 grados
de separación**: Uruguay enfrentó a Costa de Marfil en la semifinal
(`F2030-126`), y Costa de Marfil había enfrentado a Nueva Zelanda en cuartos
(`F2030-122`).

Generalizando desde el campeón: 8 selecciones a 1 grado de Uruguay (sus rivales
directos), 23 a 2 grados, 24 a 3 y 8 a 4. **Todo el torneo queda a cuatro
cruces o menos del campeón.**

**Interpretación:** es una medida de cuán "cerca" pasó cada selección del
recorrido del campeón, útil para contextualizar un resultado —un equipo
eliminado temprano puede estar a un solo cruce del campeón—. Ninguna colección
documental contiene ese dato: sólo aparece explorando la red, y sin saber de
antemano cuántos saltos hacen falta, que es justamente lo que `shortestPath()`
resuelve y un `find()` no.

### 7.2 Conectividad

**Grado en la red:** Alemania y Uruguay, ambos con 8 partidos, enfrentaron a
8 rivales distintos: son las selecciones con el recorrido más expuesto.

**Cruces entre confederaciones (5.2.1):** 32 enfrentamientos UEFA–UEFA, 15
CONMEBOL–UEFA, 14 CAF–CAF. Es una lectura estructural del torneo —cuán
"mundial" fue realmente el cruce de confederaciones— que ningún documento de
partido contiene por separado y que exige agrupar los 128 partidos por la
afiliación de **ambos** participantes.

### 7.3 Centralidad (Graph Data Science)

La red de rivalidades se proyecta en memoria con la agregación
`gds.graph.project` sobre el patrón de dos saltos: **64 nodos y 256 enlaces**.

**Intermediación (betweenness)** — por cuántos caminos mínimos entre pares de
selecciones pasa cada una:

| Selección | Intermediación | PJ |
|---|---|---|
| Uruguay | 876,97 | 8 |
| Costa de Marfil | 754,07 | 8 |
| Alemania | 686,35 | 8 |
| Suiza | 666,20 | 8 |

**Interpretación:** las cuatro selecciones que llegaron a semifinales dominan
el ranking, y no por casualidad. La eliminatoria va **fusionando ramas del
cuadro**: cada equipo que avanza se convierte en el único punto de contacto
entre grupos de selecciones que de otro modo quedarían incomunicadas. La
intermediación mide precisamente eso, y resulta ser un indicador estructural
del rendimiento deportivo: *avanzar en el torneo es volverse un puente de la
red*. Uruguay encabeza la lista por ser el campeón, es decir, el equipo que
conectó más ramas.

**PageRank** ordena de forma parecida (Alemania 1,71; Suiza 1,69; Uruguay 1,69;
Costa de Marfil 1,68) pero responde otra pregunta: mide el **prestigio
estructural**, es decir, haber enfrentado a rivales que a su vez enfrentaron a
muchos otros. Es una lectura de la exigencia acumulada del camino recorrido, y
explica por qué Suiza (ranking FIFA 20) puntúa por encima de España (ranking 3):
el camino importa más que el prestigio previo.

### 7.4 Detección de comunidades — validación estructural

Louvain sobre la misma proyección devuelve **9 comunidades** que se
corresponden con los grupos de la primera fase: tres grupos pequeños quedan
solos (`F`, `G`, `P`, 4 selecciones cada uno) y los demás aparecen fusionados de
a dos o tres (`A`+`B`+`C`, `D`+`E`, `H`+`I`, `J`+`K`, `L`+`M`, `N`+`O`).

**Interpretación:** el resultado es exactamente el esperado para un mundial y
funciona como **verificación independiente del modelo**. La fase de grupos
concentra los enfrentamientos (cada selección juega 3 partidos dentro de su
grupo), por lo que los grupos aparecen como comunidades densas; las
eliminatorias agregan los pocos enlaces que fusionan grupos vecinos. Que el
algoritmo recupere la estructura del torneo sin conocer la propiedad `grupo`
confirma que las relaciones cargadas tienen la topología correcta y no son
enlaces arbitrarios.

### 7.5 Por qué justifica el enfoque de grafos

Las cuatro secciones anteriores comparten un rasgo: **la respuesta no está en
ningún nodo ni en ninguna relación, sino en la forma del conjunto**. Un camino
mínimo, una medida de intermediación o una partición en comunidades son
propiedades emergentes de la red. Recuperar un documento aislado —por bien
indexado que esté— no puede producirlas.

---

## 8. Limitaciones conocidas

- **Datos sintéticos.** Los países, confederaciones y estadios son reales; los
  jugadores, entrenadores, resultados y eventos están generados con semilla fija
  (`Faker` en el Hito 4, Poisson ponderada por ranking en el Hito 5).
- **Integración no automatizada.** La consistencia con MongoDB es semántica y de
  identificadores, no por código: el enunciado lo admite expresamente. Hoy la
  garantiza el generador, que lee los JSON del Hito 4.
- **Neo4j Community.** Sin restricciones de existencia, de tipo ni de clave de
  nodo; se compensan con `MERGE` sobre la clave y los controles de
  `verificacion.cypher`.
- **`neo4j:latest`.** El módulo se validó el **11/09/2026** con Neo4j
  **2026.07.1 Community**, APOC 2026.07.1 y GDS 2026.07.0. Al ser una etiqueta
  móvil, una versión futura podría introducir un cambio incompatible; el README
  documenta la versión probada y su digest para poder reproducir el ambiente
  exacto.
- **Fuera de alcance por el enunciado:** API REST, interfaz web, caché, series
  temporales y monitoreo.
