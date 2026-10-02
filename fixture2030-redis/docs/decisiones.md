# Análisis y decisiones de diseño — Caché de Usuarios y Sesiones (Hito 7)

**Grupo 12** · Ingeniería de Datos II · Hito 7
Integrantes: Dayana Peñaloza · Franco Churba · Juan Bautista Mangoni.

Este documento cubre los apartados de la sección 8 de los requisitos
técnicos que no quedan ya resueltos en los otros documentos de `docs/`:
problema de concurrencia, concurrencia implementada, datos cargados,
propósito de cada script, pruebas/evidencia y coherencia con el resto del
TPO — además de la tabla de decisiones con alternativas consideradas.
Patrones de acceso, modelo clave-valor, ciclo de vida e invalidación, y
memoria/escalabilidad están en sus propios archivos (ver índice en el
[`README.md`](../README.md)).

---

## 1. Problema de concurrencia

El Fixture 2030 espera millones de usuarios consultando partidos,
equipos y resultados en simultáneo (Hito 1), y la plataforma necesita
mantener estado de sesión por cada uno sin que la validación de cada
request se convierta en el cuello de botella del sistema. Dos
necesidades concretas motivan este módulo:

1. **Lecturas repetidas masivas sobre un dato que casi no cambia en el
   corto plazo** (el resultado de un partido): si cada consulta fuera
   directo a Neo4j, miles de usuarios mirando el mismo partido generarían
   la misma consulta una y otra vez sobre la fuente de verdad.
2. **Escrituras concurrentes sobre un mismo contador/ranking** (votos de
   figura del partido, visitas): si la aplicación leyera el valor actual,
   lo incrementara en código y lo volviera a guardar, dos escrituras que
   llegan casi al mismo tiempo pueden pisarse y perder un incremento.

Redis resuelve ambos problemas con mecanismos nativos: TTL + caché para
(1), comandos atómicos (`INCR`, `ZINCRBY`) para (2) — sin necesitar
bloqueos explícitos en la aplicación.

## 2. Concurrencia (RF8) — qué se implementó y qué riesgo evita

Ver `scripts/concurrencia.redis` y la evidencia en
[`docs/evidencia/04_concurrencia_y_ranking.txt`](evidencia/04_concurrencia_y_ranking.txt).

- **Contador de visitas** (`INCR`/`INCRBY`): riesgo evitado es la
  clásica condición de carrera "leer-modificar-escribir" (dos clientes
  leen el mismo valor, cada uno lo incrementa en su copia local, el
  segundo `SET` pisa el incremento del primero). `INCR` se ejecuta como
  una única operación en el servidor: no hay ventana en la que dos
  clientes puedan leer el mismo valor de partida.
- **Encuesta de figura del partido** (`ZINCRBY`): mismo riesgo, sobre una
  estructura más rica. Se evaluó la alternativa de leer el Sorted Set
  completo, incrementar un valor en la aplicación y reescribirlo con
  `ZADD` — se descartó por la misma razón que un `GET`+`SET` manual: dos
  votos simultáneos podrían perder uno. `ZINCRBY` suma directamente sobre
  el score en el servidor.
- **Evidencia de que no se pierden actualizaciones:** en la corrida
  registrada, `ZSCORE encuesta:P-A-1:figura "ARG-10"` pasó de `66` (valor
  precargado) a `69` después de tres `ZINCRBY ... 1 "ARG-10"` —
  exactamente +3, sin faltar ni sobrar ningún voto.

No se usó `MULTI`/`EXEC` porque ninguna de las dos operaciones necesita
agrupar varios comandos como una unidad: tanto `INCR` como `ZINCRBY` ya
son atómicos por sí solos. `MULTI`/`EXEC` sería necesario si, por
ejemplo, hubiera que incrementar el contador de visitas *y* renovar el
TTL de la sesión como una sola unidad — no es el caso de ninguna
operación de este módulo.

## 3. Datos cargados (RF11)

Generados por `scripts/generar_datos.py` con semilla fija (`SEED = 2030`,
la misma de los Hitos 4/5/6) hacia un único archivo de comandos
reproducible, `scripts/carga_muestra.redis`:

- **200 sesiones** (`sesion:U#####`), usando una muestra del mismo
  espacio de `usuario_id` que ya generó Cassandra en el Hito 6
  (`U00001`-`U50000`). De esas 200, **10 se cargan con TTL de 5 segundos**
  a propósito, para poder demostrar la expiración real sin esperar los
  30 minutos de producción durante una práctica de 90 minutos (RNF8 del
  TPO general: el trabajo práctico debe completarse en el tiempo de
  clase).
- **6 partidos en caché** (`cache:partido:*`), tomados del fixture real
  cargado en Neo4j (Hito 5, rama `main`): tres de fase de grupos
  (`P-A-1`, `P-A-3`, `P-E-4`) y tres de instancias eliminatorias
  (`P-QF-2`, `P-R16-3`, `P-R32-6`), para cubrir tanto partidos múltiples
  por fecha como cruces únicos.
- **6 contadores de visitas** y **6 encuestas de figura** (uno por cada
  uno de esos mismos 6 partidos), con entre 3 y 4 candidatos cada una
  (jugadores con formato `EQUIPO-DORSAL` del Hito 4).

**Alcance y escala:** el enunciado pide una muestra "acorde al hardware
disponible" (RF12/sección 5.5), no un volumen de producción — a
diferencia de Mongo/Neo4j/Cassandra, que sí piden decenas o cientos de
miles de registros. 200 sesiones y 6 partidos son suficientes para
demostrar los seis flujos pedidos (sesión, caché, actualización,
expiración, invalidación, operación concurrente) sin que la carga de
datos consuma el tiempo de práctica.

## 4. Operaciones Redis — propósito de cada script

| Script | RF que cubre | Qué demuestra |
|---|---|---|
| `scripts/generar_datos.py` | RF11 | Genera `carga_muestra.redis` de forma reproducible (no se conecta a Redis). |
| `scripts/inicializacion.redis` | RF1 | Verifica que el servidor responde y que la configuración de memoria es la esperada, sin tocar datos. |
| `scripts/carga_muestra.redis` | RF11 | Carga sesiones, caché, contadores y encuestas (idempotente: ver sección 6). |
| `scripts/sesiones.redis` | RF3, RF4, RF5, RF7 | Ciclo completo de una sesión: crear, leer, renovar, expirar, cerrar, consultar una inexistente. |
| `scripts/cache.redis` | RF6, RF7 | Cache-Aside completo: hit, miss, invalidación explícita por cambio en la fuente de verdad. |
| `scripts/concurrencia.redis` | RF8, RF9 | Atomicidad de `INCR`/`ZINCRBY` y ranking con `ZREVRANGE`. |
| `scripts/metricas.redis` | RF12, RF13 | `INFO memory`/`INFO stats`, `DBSIZE`, inspección seguro con `SCAN`. |
| `scripts/ejecutar.sh` | RNF3, RNF9 | Wrapper que filtra comentarios antes de pasarle un archivo a `redis-cli` (ver nota técnica abajo). |

### Nota técnica: por qué existe `scripts/ejecutar.sh`

A diferencia de `cypher-shell -f` (Neo4j) o `cqlsh -f` (Cassandra),
`redis-cli` **no interpreta comentarios `#`** cuando lee comandos desde
`stdin`: los trata como un comando desconocido y falla
(`ERR unknown command '#'`, confirmado al ejecutar un script sin filtrar).
Para poder mantener los `.redis` comentados y legibles (RNF9) sin que eso
rompa la ejecución automática, `ejecutar.sh` filtra las líneas de
comentario y las vacías antes de pasarle el archivo a `redis-cli`. Es la
misma necesidad que resolvieron `scripts/cargar.sh` en Neo4j o el uso de
`cqlsh -f` en Cassandra, adaptada a una limitación real y puntual de
`redis-cli`.

## 5. Pruebas y evidencia (RF12, RF13)

Todo lo que sigue está capturado con salida real de consola en
[`docs/evidencia/`](evidencia/) (no son valores inventados):

| Archivo | Contenido |
|---|---|
| `01_ambiente.txt` | `PING`, `INFO server` (versión y fecha de Redis), `CONFIG GET maxmemory*`. |
| `02_sesiones.txt` | TTL de una sesión recién creada (`5`) y su expiración real tras una espera efectiva de 6 segundos — no simulada. |
| `03_cache.txt` | Cache hit, cache miss seguido de carga, e invalidación explícita antes de que venza el TTL. |
| `04_concurrencia_y_ranking.txt` | `INCR`/`INCRBY` del contador de visitas y `ZINCRBY` + `ZREVRANGE WITHSCORES` de la encuesta de figura. |
| `05_metricas.txt` | `INFO memory`, `INFO stats` (`expired_keys`, `evicted_keys`, `keyspace_hits/misses`), `DBSIZE`, `SCAN`. |
| `06_persistencia.txt` | `DBSIZE` antes y después de `docker compose stop` + `start`, y listado de `~/docker/data/redis` mostrando `dump.rdb` y el directorio de AOF. |

**Método y entorno (RNF10):** todas las mediciones se corrieron contra el
contenedor `fixture2030-redis` levantado con este mismo
`docker-compose.yml`, en la notebook de desarrollo del grupo, el
2026-10-02. La versión de Redis observada en `01_ambiente.txt`
(`INFO server` → `redis_version`) queda registrada ahí mismo, como exige
usar la etiqueta `latest` (RNF1): si una corrida futura muestra una
versión distinta, se debe anotar junto a la evidencia nueva.

**Limitaciones del laboratorio local:** un solo nodo, sin tráfico real
concurrente de múltiples clientes (los votos "simultáneos" de
`concurrencia.redis` se ejecutan secuencialmente desde un único
`redis-cli`, no desde procesos distintos en paralelo) y con un volumen de
datos muy por debajo de cualquier escenario de producción. La atomicidad
demostrada es una propiedad del comando en el servidor (garantizada por
Redis independientemente de cuántos clientes la usen), no una medición de
throughput bajo carga real — por eso no se reportan cifras de
operaciones por segundo para este módulo (el enunciado pide no declarar
tasas sin método, entorno y resultado observado, y acá el método no
incluye carga concurrente real).

## 6. Coherencia con el TPO

| Decisión de este hito | Se apoya en |
|---|---|
| Formato de `usuario_id` (`U#####`) | Mismo espacio de IDs que `usuario_id` en Cassandra (Hito 6). |
| Formato de `partido_id` | Mismo `Partido.partidoId` cargado en Neo4j (Hito 5). |
| Formato de `jugador_id` en la encuesta | Mismo `_id` de `jugadores` en MongoDB (Hito 4). |
| Redis como estado transitorio, no fuente de verdad | Hito 2 (matriz de decisión): Sesiones y Sistema de puntos se asignaron a clave-valor por acceso directo por clave, nunca como el lugar donde vive el dato de negocio. |
| Prioridad de disponibilidad sobre consistencia fuerte para sesiones/caché | Hito 3 (análisis CAP): Sesiones y Usuarios se ubicaron en el bloque de disponibilidad con consistencia eventual — este módulo no introduce una exigencia de consistencia fuerte que contradiga esa decisión. |

Redis no reemplaza a ningún módulo anterior: no se migró ningún dato de
equipos, jugadores, partidos ni comentarios a Redis. Lo único que entra a
este módulo es estado que no existía en ningún otro lugar (sesiones) o
una copia temporal y descartable de un dato que sí tiene una fuente de
verdad externa (resultado de partido).

---

## 7. Tabla de decisiones

| Decisión | Alternativas consideradas | Elección | Justificación | Impacto esperado |
|---|---|---|---|---|
| **Qué cachear (RF6)** | (a) Ficha de equipo/jugador (MongoDB). (b) Resultado de un partido (Neo4j). (c) Ranking histórico de goleadores. | (b) Resultado de partido | Es el dato con mayor relación lecturas/escrituras del Fixture: millones de usuarios lo leen, cambia pocas veces por partido. (a) casi no cambia y ya se resuelve en un único acceso por `_id`; cachearlo no ahorra nada significativo. | Reduce la carga de lectura sobre Neo4j durante un partido en vivo sin arriesgar mostrar datos muy desactualizados (TTL de 45s + invalidación explícita). |
| **Operación concurrente (RF8/RF9)** | (a) Dos features separadas: un contador simple + un ranking aparte sin relación. (b) Encuesta de figura con Sorted Set, que resuelve concurrencia y ranking a la vez. | (b) Encuesta con `ZINCRBY`/`ZREVRANGE` | Una sola estructura cubre RF8 (atomicidad) y RF9 (ranking) sin duplicar lógica ni justificar dos features separadas. Se agregó además el contador de visitas (`INCR`) como ejemplo mínimo previo, de menor complejidad. | Un voto nunca se pierde por concurrencia, y el Top-N se obtiene con una sola operación de servidor, sin ordenar en el cliente. |
| **Duración de sesión (RF4)** | (a) Un valor arbitrario propio (ej. 15 min). (b) 30 minutos, igual al ejemplo de la Clase 8. | (b) 30 minutos | Mismo orden de magnitud que la duración real de un partido con interrupciones; además permite justificar el valor citando el material de la materia en vez de un número sin respaldo. | Un usuario que deja de interactuar por más de media hora pierde la sesión; se acepta como comportamiento esperado para un "fan navegando durante un partido". |
| **Política de memoria (RF10)** | (a) `allkeys-lru`. (b) `volatile-lru`/`volatile-ttl`. (c) `noeviction`. | (c) `noeviction` + `maxmemory 100mb` | (a) y (b) podrían evictar una sesión activa bajo presión de memoria porque las sesiones también tienen TTL (ver `docs/memoria_y_escalabilidad.md`). `noeviction` nunca borra una clave por sorpresa; el costo (rechazar escrituras nuevas al llegar al límite) es visible y manejable por la aplicación. | Cero pérdidas silenciosas de sesión por memoria; confirmado en la evidencia (`evicted_keys:0`). |
| **Estructura de la encuesta (RF9)** | (a) Hash `jugador_id -> votos` con `HINCRBY`. (b) Sorted Set con `ZINCRBY`. | (b) Sorted Set | Un Hash es atómico para incrementar pero no mantiene orden: el ranking requeriría traer todos los valores al cliente y ordenarlos ahí. Un Sorted Set devuelve el Top-N ya ordenado desde el servidor. | `ZREVRANGE ... WITHSCORES` responde el ranking en una sola operación, sin procesamiento adicional en el cliente. |
| **Identificadores** | (a) IDs nuevos propios de este módulo (ej. UUID). (b) Reutilizar los formatos ya definidos en Hitos 4/5/6. | (b) Reutilizar formatos existentes | Evita una tabla de traducción entre módulos y permite cruzar un dato de Redis con su fuente de verdad sin ambigüedad (mismo criterio que RF5 del Hito 5). | Un `jugador_id` de la encuesta (`ARG-10`) es directamente el `_id` a buscar en MongoDB; un `partido_id` de la caché es directamente el `partidoId` a buscar en Neo4j. |
