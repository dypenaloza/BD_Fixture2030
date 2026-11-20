# Defensa por base de datos — los 10 puntos de la sección 6.4

Cada sección responde, para una base, los 10 puntos que el enunciado
exige poder explicar. Las citas de archivo/línea apuntan a dónde está
documentado cada dato real (así cualquiera puede verificarlo rápido
antes de la defensa). Donde el proyecto **no documenta** algo
explícitamente, se dice "no encontrado" en vez de inventar una
respuesta — es preferible decir "no lo medimos" en la defensa que
afirmar algo que no se puede sostener si preguntan (RNF8, RNF17).

Al final hay una sección "Huecos documentales conocidos": úsenla para
no ser tomados por sorpresa si la FIFA pregunta justo por ahí.

---

## 1. MongoDB — Selecciones y Jugadores

1. **Tipo de dato**: documentos BSON/JSON con validación de esquema
   (`$jsonSchema`). — `MongoDB/scripts/setup_validations.py:17-148`
2. **Consultas que motivaron la elección**: recuperación por `_id`,
   filtros/proyección/orden/paginación, agregación, inserción/actualización
   sobre **Equipos** y **Jugadores** como entidades aisladas (sin
   necesidad de atravesar relaciones). El contraste real está en
   `Neo4j/docs/decisiones.md:5-24`: el modelo documental "resuelve bien
   preguntas sobre una entidad aislada" pero no las que cruzan varias
   entidades — por eso Neo4j se sumó después, no porque Mongo "fallara".
3. **Modelo**: dos colecciones con validador estricto
   (`validationLevel: "strict"`). — `setup_validations.py:17-157`
4. **Estructura real**: colección `selecciones` (`_id` = código FIFA de
   3 letras, `confederacion`, `grupo`, `ranking`, `anfitrion`) y
   `jugadores` (`_id` = `EQUIPO-DORSAL` ej. `ARG-10`, `equipoId` referencia
   a `selecciones._id`, `posicion`, `dorsal`). Índices: `idx_grupo`,
   `idx_confederacion`, `idx_equipoId`, `idx_equipoId_posicion`,
   `idx_apellido`. — `setup_validations.py:17-187`
5. **Carga/recuperación**: `scripts/load_data.py` usa `bulk_write` con
   `UpdateOne(upsert=True)` sobre el `_id` natural — **idempotente**
   (repetirlo no duplica). Carga real: 64 selecciones + 1.536 jugadores.
   Evidencia de dos corridas idénticas: `MongoDB/evidencia/03_carga_datos.txt`.
6. **Partición/réplica**: **no implementado**. Un solo contenedor, un
   volumen nombrado, sin sharding ni mención de estrategia futura. —
   `MongoDB/README.md:29-56`
7. **Consistencia**: no documentada explícitamente (ni "eventual" ni
   "fuerte", ni write/read concern). **No encontrado**.
8. **Ante una falla**: no hay comportamiento de runtime documentado
   (sin timeout/reconexión descritos a nivel de API en este módulo). El
   único dato real es el timeout de conexión del driver:
   `serverSelectionTimeoutMS=5000` (5s). — `scripts/db.py:26`. (El
   comportamiento real ante 503 de la API del Hito 10 sí está probado
   — ver `API_REST/docs/contratos_y_errores.md`.)
9. **Trade-off reconocido**: dataset sintético (Faker, semilla fija);
   sin API REST ni UI en este módulo (llegó en el Hito 10); credenciales
   hardcodeadas válidas solo para desarrollo local. — `MongoDB/README.md:155-166`
10. **Evidencia real**: `MongoDB/evidencia/01..09_*.txt`, en particular
    `03_carga_datos.txt` (idempotencia) y `08_persistencia_stop_restart.txt`
    (persistencia tras `stop`/`start`).

---

## 2. Neo4j — Relaciones entre selecciones, partidos y eventos

1. **Tipo de dato**: grafo (nodos + relaciones con propiedades).
2. **Consultas que motivaron la elección**: preguntas que atraviesan
   varias entidades a la vez — ¿en qué estadios juega una selección y
   cuándo?, ¿qué eventos ocurrieron en los partidos de una selección?,
   camino más corto entre dos selecciones, qué sedes concentran más
   partidos. — `Neo4j/docs/decisiones.md:5-24`
3. **Modelo**: 5 etiquetas de nodo (`Seleccion`, `Jugador`, `Partido`,
   `Estadio`, `Evento`) y 5 tipos de relación (`PERTENECE_A`,
   `PARTICIPA_EN`, `SE_JUEGA_EN`, `OCURRE_EN`, `PROTAGONIZADO_POR`). —
   `Neo4j/docs/modelo_grafo.md:7-45`
4. **Estructura real**: `Partido.partidoId` con formato real
   `"P-A-1"` (grupo A, partido 1), `"P-R16-3"`, `"P-FIN-1"`.
   `Evento.eventoId` tipo `"EV0001"`. Restricciones de unicidad sobre
   los 5 IDs; índices en `Seleccion.pais`, `Jugador.posicion`,
   `Partido.fecha`, `Estadio.pais` — deliberadamente **sin** indexar
   `Partido.fase` ni `Evento.tipo` por baja cardinalidad. Volumen real
   cargado: 64 Selección · 1536 Jugador · 16 Estadio · 128 Partido (96
   grupos + 32 eliminatorias) · 591 Evento. — `modelo_grafo.md:9-123`
5. **Carga/recuperación**: `generar_fixture.py` con semilla fija
   (`SEED = 2030`) — determinístico y repetible con `MERGE` (no
   duplica). — `decisiones.md:114-164`
6. **Partición/réplica**: **no implementado** (instancia única). Sin
   mención de Neo4j Fabric ni sharding, ni como plan futuro. **No
   encontrado**.
7. **Consistencia**: no se declara un nivel formal; lo más cercano es
   la garantía de idempotencia de `MERGE` + restricciones de unicidad
   (integridad, no un modelo de consistencia transaccional declarado).
8. **Ante una falla**: no documentado a nivel de runtime en este
   módulo. (Si lo preguntan: el comportamiento real demostrado está en
   el Hito 11 — la API devuelve 503 `NEO4J_UNAVAILABLE` con
   reconexión automática del pool al volver la base, ver
   `Requisitos_técnicos/docs/arquitectura_y_adaptadores.md`.)
9. **Trade-off reconocido**: se usa la etiqueta `neo4j:latest` (móvil,
   validada en una fecha concreta); el fixture es simulado, no un
   Mundial real; se descartó modelar `Confederacion`/`Grupo`/`Fase`
   como nodos por baja cardinalidad sin ganancia de consulta. —
   `README.md:182-195`, `decisiones.md:48-56`
10. **Evidencia real**: `Neo4j/evidencias/evidencia_carga_idempotente.txt`,
    `evidencia_constraints_indices.txt`, `evidencia_multisalto.txt`,
    `evidencia_subgrafo_completo.txt`.

---

## 3. Cassandra — Comentarios masivos

1. **Tipo de dato**: columnar ancho (wide-column), orientado a
   consulta.
2. **Consultas que motivaron la elección**: alto volumen de escritura
   concurrente durante partidos en vivo. Documentado **antes** de
   diseñar el esquema (query-driven design): últimos comentarios de un
   partido, comentarios en ventana temporal, historial de un usuario
   sin `ALLOW FILTERING`. — `Cassandra/docs/patrones_de_acceso.md:1-32`
3. **Modelo**: keyspace `fixture2030`, dos tablas denormalizadas por
   patrón de acceso: `comentarios_por_partido` y `comentarios_por_usuario`.
4. **Estructura real**: `comentarios_por_partido` con
   `PRIMARY KEY (("partido_id","bucket_temporal"), creado_en, comentario_id)`,
   `CLUSTERING ORDER BY (creado_en DESC)`. `comentarios_por_usuario`
   con la misma idea pero `bucket_temporal` mensual. IDs reales:
   `"M001"`, `"U001"`. — `modelo_tabular.md:5-49`
5. **Carga/recuperación**: `generar_comentarios.py` (semilla fija)
   generó **1.050.000 comentarios** sobre 100 partidos y 50.000
   usuarios, cargados vía `COPY FROM`. No hay declaración explícita de
   idempotencia para este paso masivo (a diferencia de Mongo/Neo4j).
6. **Partición/réplica**: clave de partición real
   `(partido_id, bucket_temporal)` — ventana de **5 minutos** para
   evitar hotspots en partidos populares; `(usuario_id, bucket_temporal)`
   con ventana **mensual** para el historial de usuario. Réplica:
   `SimpleStrategy`, `replication_factor: 1` (nodo único de
   laboratorio), **documentado explícitamente como a futuro**:
   "en un despliegue productivo multirregional se usaría
   `NetworkTopologyStrategy` con factor de replicación por datacenter". —
   `decisiones_de_particionamiento.md:1-22`, `README.md:85-86,202`
7. **Consistencia**: no se declara un nivel `CONSISTENCY` CQL
   explícito. **No encontrado** (y con RF=1 en este entorno, la
   discusión de consistencia entre réplicas no aplica todavía).
8. **Ante una falla**: no documentado a nivel de runtime en este
   módulo; sí se documenta que los `DELETE` generan tombstones que
   "impactan temporalmente la latencia hasta la compactación". —
   `README.md:205`. (Comportamiento de la API ante Cassandra caída:
   503 `CASSANDRA_UNAVAILABLE`, ver Hito 10/11.)
9. **Trade-off reconocido**: nodo único, no simula tolerancia a fallas
   de clúster multirregional; la velocidad de escritura medida depende
   del hardware local, "no es una cota general del motor".
10. **Evidencia real** (benchmark real, Cassandra 5.0.9, 25/09/2026):
    `comentarios_por_partido` 1.050.000 filas en 43,9s (23.906 filas/s);
    `comentarios_por_usuario` 1.050.000 filas en 35,0s (30.006 filas/s)
    — ambas superan el objetivo de referencia de 10.000 escrituras/s. —
    `Cassandra/docs/rendimiento.md:1-29`

---

## 4. Redis — Sesiones, caché y contadores

1. **Tipo de dato**: clave-valor (Hash, String, Sorted Set) — estado
   transitorio/caché, **nunca fuente de verdad**.
2. **Consultas que motivaron la elección**: lecturas repetidas
   masivas sobre un dato que casi no cambia en el corto plazo
   (resultado de partido, evitar que miles de usuarios golpeen Neo4j
   con la misma consulta) y escrituras concurrentes atómicas sobre un
   contador/ranking (votos a figura del partido). Se evaluó y
   **descartó explícitamente** cachear fichas de equipo/jugador
   (cambian poco, ya resueltas en un único acceso por `_id`). —
   `Redis/docs/decisiones.md:17-36,179`
3. **Modelo**: 4 estructuras con namespace `dominio:id[:subdominio]`.
4. **Estructura real**: `sesion:{usuarioId}` (Hash, TTL 1800s),
   `cache:partido:{partidoId}` (String JSON, TTL 45s, fuente de verdad
   = Neo4j), `contador:partido:{partidoId}:visitas` (String, `INCR`,
   sin TTL), `encuesta:{partidoId}:figura` (Sorted Set, `ZINCRBY`, sin
   TTL). IDs reutilizados de otros módulos (`U#####`, `P-A-1`,
   `EQUIPO-DORSAL`). — `Redis/docs/modelo_clave_valor.md:1-61`
5. **Carga/recuperación**: `generar_datos.py` (semilla fija) → 200
   sesiones, 6 partidos en caché, 6 contadores, 6 encuestas. Claves
   determinísticas (`HSET`/`SET`/`ZADD`): repetir la carga no duplica.
6. **Partición/réplica**: **no implementado** (nodo único, sin
   Sentinel ni Cluster). **Documentado explícitamente a futuro**:
   Primary + réplicas con Sentinel para failover, Redis Cluster con
   hash tags (`cache:partido:{P-A-1}`) para forzar claves relacionadas
   al mismo slot. — `Redis/docs/memoria_y_escalabilidad.md:84-101`
7. **Consistencia**: Redis se usa deliberadamente para estado
   transitorio, nunca como fuente de verdad — "este módulo no
   introduce una exigencia de consistencia fuerte" (citando un
   análisis CAP de un hito anterior no incluido en este repo). —
   `decisiones.md:165`
8. **Ante una falla**: **comportamiento real documentado y
   verificado**: si Redis no tiene la clave o no está disponible, "la
   aplicación cae a Neo4j — la caché es prescindible y reconstruible
   por definición". Ante memoria llena con `noeviction`: las
   escrituras nuevas fallan con error en vez de evictar silenciosamente.
   Esto es además el escenario que se probó en vivo en el Hito 11 y en
   el Hito 13 (ver `evidencia/prueba_de_falla.md`): 503 en 14ms,
   reconexión automática al volver, sin pérdida de datos.
9. **Trade-off reconocido**: sin autenticación (solo laboratorio);
   concurrencia demostrada pero no medida bajo clientes paralelos
   reales (comandos secuenciales desde un único `redis-cli`); políticas
   `volatile-*`/`allkeys-*` evaluadas y descartadas porque no protegen
   selectivamente a las sesiones.
10. **Evidencia real**: `Redis/docs/evidencia/02_sesiones.txt` (TTL
    expirando en vivo), `04_concurrencia_y_ranking.txt` (`INCR`/`ZINCRBY`
    verificado exacto), `06_persistencia.txt`; más
    `Hito13/evidencia/prueba_de_falla.md` (caída/recuperación real con
    métricas).

---

## 5. InfluxDB 3 Core — Estadísticas temporales

1. **Tipo de dato**: series temporales multidimensionales
   (tags/fields/timestamp).
2. **Consultas que motivaron la elección**: estadísticas que
   evolucionan en el tiempo durante los partidos (posesión, pases,
   tiros): evolución de un equipo en un intervalo, comparación entre
   los dos equipos de un partido, resumen agregado del intervalo. —
   `InfluxDB/docs/patrones_de_acceso.md:1-105`
3. **Modelo**: un measurement (`estadisticas`) con tags
   `partido_id`/`equipo_id` y fields `posesion_pct`/`pases`/`tiros`.
4. **Estructura real**: `pases` se agrega con `MAX(pases) - MIN(pases)`
   por ser **contador acumulado** (no se puede sumar directamente);
   `tiros` se agrega con `SUM` por ser incrementos nuevos en cada
   observación; `posesion_pct` con `AVG`. Cardinalidad estimada: ~254
   series (127 partidos × 2 equipos). Retención configurada: 30 días.
   — `InfluxDB/docs/modelo_multidimensional.md:44-80`
5. **Carga/recuperación**: Line Protocol vía `influxdb3 write`. No hay
   declaración explícita de idempotencia (a diferencia de Mongo/Neo4j/Redis).
   Token de admin guardado fuera del repo (`.influxdb3-token`, en `.gitignore`).
6. **Partición/réplica**: **no implementado** (contenedor único). El
   objetivo de diseño es 10M+ puntos; la prueba real ejecutada fue de
   **10.000 puntos** — explícitamente **no extrapolado**: "una prueba
   sobre mayor volumen deberá volver a medir tiempos, recursos y
   resultados reales". — `InfluxDB/docs/cardinalidad_y_escalabilidad.md:59-89`
7. **Consistencia**: no documentada explícitamente. **No encontrado**.
8. **Ante una falla**: no documentado como comportamiento de runtime en
   este módulo (solo "problemas conocidos" operativos: PowerShell,
   variable `HOME`, Line Protocol con `\r`). El comportamiento real de
   la API ante InfluxDB caído/con token inválido sí está probado en el
   Hito 10/11: 503/502 según el caso.
9. **Trade-off reconocido**: la prueba real "no representa un entorno
   productivo; no demuestra rendimiento con 10M+ puntos; no mide
   comportamiento bajo múltiples productores simultáneos"; `pases` no
   puede sumarse directamente (limitación semántica reconocida).
10. **Evidencia real**: benchmark real (InfluxDB 3 Core 3.12.0,
    06/10/2026): 10.000 puntos cargados en 1,07s (≈31.174 líneas/s). —
    `InfluxDB/docs/cardinalidad_y_escalabilidad.md:90-144`

---

## 6. IRIS — Entidades complejas (Partido/Evento con objetos)

1. **Tipo de dato**: objetos persistentes con proyección multimodelo a
   SQL (InterSystems IRIS).
2. **Consultas/motivación**: representar entidades complejas con
   herencia, relaciones bidireccionales y validación propia sin ORM
   externo, demostrando que lo cargado como objetos también es
   consultable por SQL. **No hay, dentro de este módulo, una
   comparación explícita "por qué IRIS y no otra base"** (a diferencia
   de Neo4j/Cassandra/Redis, que sí documentan esa comparación).
3. **Modelo**: clases `%Persistent` con herencia simple
   (`Fixture.Persona` → `Fixture.Jugador`/`Fixture.Arbitro`) y relación
   padre-hijo (`Fixture.Partido` ↔ `Fixture.Evento`, `Cardinality
   children/parent`, `Inverse` bidireccional).
4. **Estructura real**: `Fixture.Partido.Codigo` (único, índice
   `idxCodigo`), `Fixture.Evento.Partido` (índice `idxPartido` del lado
   hijo, para traer Eventos de un Partido sin recorrer todo).
5. **Carga/recuperación**: `Fixture.CargaInicial.Ejecutar()` crea un
   Partido con código **fijo `M004`**. **Explícitamente NO
   idempotente**: "ejecutarlo nuevamente sin limpiar los datos provoca
   una colisión con el índice único". — `IRIS/README.md:279,482`
6. **Partición/réplica**: **no implementado**, sin mención a futuro.
   **No encontrado**.
7. **Consistencia**: no se declara un nivel formal, pero sí
   **atomicidad real y verificada**: un Partido con sus Eventos se
   guarda con un único `%Save()` del padre; si un Evento hijo es
   inválido, el Partido padre tampoco queda guardado. — `README.md:342-347`
8. **Ante una falla**: el módulo documenta **rechazo ante datos
   inválidos** (no indisponibilidad): propiedad `[Required]` faltante,
   código duplicado (índice único), transición de estado inválida
   (`CambiarEstado()` devuelve 0). El comportamiento real ante **IRIS
   caído** se probó en el Hito 10/11: 503 `IRIS_UNAVAILABLE`, con una
   particularidad real encontrada — el adaptador abre una conexión
   nueva por consulta (no un pool), evitando el problema de "socket
   cacheado que queda inválido" que si tendría con el patrón usado en
   las otras 5 bases. Ver `Hito13/docs/arquitectura` (Hito 11) y
   `API_REST/docs/arquitectura_y_adaptadores.md`.
9. **Trade-off reconocido**: la validación de estados puede saltearse
   si algo escribe `Estado` directamente sin pasar por
   `CambiarEstado()`; la carga inicial no es idempotente; no hay
   política de inmutabilidad para los Eventos; "no se realizaron
   pruebas de carga de gran volumen".
10. **Evidencia real**: `IRIS/evidencias/01..09_*` (persistencia,
    navegación, validación de `Required`, validación de transición de
    estado, integridad referencial, carga inicial), incluyendo
    `09_pruebas_hito9.txt` con los 9 bloques de pruebas documentados.

---

## Huecos documentales conocidos (decirlos de frente si preguntan)

- **MongoDB**: el propio README cita dos documentos de decisiones
  (`Grupo_12_Hito_4_Decisiones_Documentales_Fixture2030.md`,
  `docs/DISENO_DOCUMENTAL.md`) que **no existen en el repo actual**.
  Si preguntan "¿por qué Mongo y no otra base documental?", la
  respuesta honesta es: la justificación detallada se perdió/no se
  commiteó; lo que sí se puede defender es el modelo y las
  validaciones realmente implementadas.
- **IRIS**: no tiene una carpeta `docs/` de justificación comparada
  con otras bases (las otras 4 sí la tienen).
- **Ningún módulo** declara explícitamente un nivel de consistencia
  (eventual/fuerte) dentro de su propia carpeta. Redis es el que más
  se acerca, citando un análisis CAP de un hito anterior que no está
  en estas 6 carpetas.
- **Ningún módulo** documenta reconexión automática o códigos de error
  de runtime a nivel de su propia carpeta — eso se resolvió recién en
  el Hito 10/11 a nivel de la API integrada (`API_REST/docs/`,
  `Requisitos_técnicos/docs/`), no en cada módulo por separado. Si
  preguntan "¿qué pasa si esta base se cae?", la respuesta real está
  en los hitos de la API, no en el módulo original de cada base.
