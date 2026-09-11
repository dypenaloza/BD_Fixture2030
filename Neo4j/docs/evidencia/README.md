# Evidencia técnica — Hito 5 (RF11)

Salidas **reales** de cada paso del módulo, capturadas contra el ambiente local
descrito en el [README](../../README.md).

Todos los archivos `.txt` de esta carpeta se regeneran con un solo comando:

```bash
./scripts/generar_evidencia.sh
```

Ambiente de captura: **11/09/2026**, Neo4j **2026.07.1 Community** sobre
`neo4j:latest`, APOC 2026.07.1, GDS 2026.07.0, Docker 29.7.2.

---

## Índice

| Archivo | Contenido | Requisitos |
|---|---|---|
| [`01_ambiente_docker.txt`](01_ambiente_docker.txt) | Imagen `neo4j:latest`, contenedor activo, versión y edición del servidor, plugins, volúmenes nombrados, puertos y respuesta HTTP 200 de Neo4j Browser | RF1, RNF1, RNF2 |
| [`02_generacion_dataset.txt`](02_generacion_dataset.txt) | Dos corridas del generador con **huellas MD5 idénticas** | RF6, RNF3 |
| [`03_estructura_restricciones_indices.txt`](03_estructura_restricciones_indices.txt) | 8 restricciones de unicidad y 16 índices activos | RF10 |
| [`04_carga_idempotente.txt`](04_carga_idempotente.txt) | Dos corridas de `carga.cypher`: **2.528 nodos y 3.700 relaciones en ambas**, sin relaciones paralelas | RF6, RNF4 |
| [`05_verificacion_coherencia.txt`](05_verificacion_coherencia.txt) | Conteos, cardinalidades, coherencia de marcadores y trazabilidad con el Hito 4 | RNF6, RNF7 |
| [`06_crud.txt`](06_crud.txt) | Alta, lectura, actualización y borrado acotado; el subgrafo del torneo queda intacto | RF7 |
| [`07_consultas_grafo.txt`](07_consultas_grafo.txt) | Las 14 consultas del catálogo con sus resultados | RF8 |
| [`08_analisis_relacional.txt`](08_analisis_relacional.txt) | Camino mínimo, conectividad, betweenness, PageRank y Louvain | RF9 |
| [`09_rendimiento_indices.txt`](09_rendimiento_indices.txt) | Planes `PROFILE`: `NodeIndexSeek` (34 accesos) frente a `NodeByLabelScan` (257) | RF10 |
| [`10_persistencia_reinicio.txt`](10_persistencia_reinicio.txt) | `stop` + `start`: los 2.528 nodos y las 8 restricciones sobreviven | RNF2 |

---

## Capturas de Neo4j Browser

Evidencia visual del subgrafo, aportada por el equipo desde
<http://localhost:7474>. Las 13 capturas corresponden a consultas de
[`../../queries/consultas.cypher`](../../queries/consultas.cypher) y se
verificaron contra el subgrafo final: las etiquetas (`:Seleccion`, `:Jugador`,
`:Partido`, `:Estadio`, `:Evento`), los identificadores y los valores que
muestran coinciden con los datos cargados.

### Planteles y jugadores

| Captura | Consulta |
|---|---|
| [`consulta_plantel_argentina.png`](consulta_plantel_argentina.png) | Plantel completo de una selección |
| [`consulta_delanteros_argentina.png`](consulta_delanteros_argentina.png) | Plantel filtrado por posición |
| [`consulta_capitanes.png`](consulta_capitanes.png) | Los 64 capitanes y su selección |
| [`consulta_companeros_seleccion.png`](consulta_companeros_seleccion.png) | Compañeros de plantel de un jugador |
| [`consulta_cantidad_jugadores_por_seleccion.png`](consulta_cantidad_jugadores_por_seleccion.png) | 24 jugadores por selección |
| [`consulta_jugadores_por_posicion.png`](consulta_jugadores_por_posicion.png) | Jugadores por posición en el torneo |
| [`consulta_posiciones_por_seleccion.png`](consulta_posiciones_por_seleccion.png) | Posiciones dentro de cada selección |
| [`consulta_promedios_por_posicion.png`](consulta_promedios_por_posicion.png) | Altura y peso promedio por posición |
| [`relaciones_jugadores_selecciones.png`](relaciones_jugadores_selecciones.png) | Vista de grafo: jugadores y selecciones |

### Fixture, estadios y eventos

| Captura | Consulta |
|---|---|
| [`partido_selecciones_estadio.png`](partido_selecciones_estadio.png) | Partido con sus dos selecciones y su estadio |
| [`partido_estadio.png`](partido_estadio.png) | Programación de un partido en su estadio |
| [`evento_partido.png`](evento_partido.png) | Evento deportivo vinculado a su partido |
| [`carga_1.png`](carga_1.png) | Resultado de la carga en el Browser |

### Capturas recomendadas para completar

Estas dos vistas todavía no están capturadas y aportarían el modelo completo de
un vistazo. Se toman desde Neo4j Browser y se guardan en esta carpeta:

**`browser_esquema.png`** — el esquema inferido por Neo4j, que debe mostrar las
8 etiquetas y los 9 tipos de relación del diagrama de
[`../modelo_grafo.md`](../modelo_grafo.md):

```cypher
CALL db.schema.visualization()
```

**`browser_final.png`** — el subgrafo de la final, donde se ven los dos ciclos
del modelo en una sola imagen (consulta 4.14):

```cypher
MATCH (p:Partido)-[:CORRESPONDE_A]->(:Fase {codigo: 'FINAL'})
MATCH camino1 = (e:Seleccion)-[:PARTICIPA_EN]->(p)-[:SE_JUEGA_EN]->(:Estadio)
MATCH camino2 = (v:Evento)-[:OCURRE_EN]->(p)
MATCH camino3 = (v)-[:PROTAGONIZADO_POR]->(:Jugador)-[:PERTENECE_A]->(e)
RETURN camino1, camino2, camino3
```
