# Arquitectura y adaptadores — API REST Fixture 2030

## 1. Capas

Cada endpoint atraviesa cuatro capas, siempre en el mismo orden:

```
Cliente HTTP
    |
Router (app/routes/*.py)        -> valida parametros, arma la respuesta HTTP
    |
Servicio (app/services/*.py)    -> aplica reglas propias del caso de uso
    |
Adaptador (app/adapters/*.py)   -> unico lugar que conoce el driver nativo
    |
Base NoSQL (una por adaptador)
```

RNF1/RNF5 (aislamiento por fuente): un adaptador solo sabe hablar con su
base. Ningun router ni servicio importa un driver nativo (pymongo,
neo4j, cassandra-driver, redis, requests, iris) directamente: siempre
pasan por su adaptador. Esto permite reemplazar o versionar una fuente
sin tocar las demas.

## 2. Un adaptador por fuente

| Fuente     | Adaptador                        | Driver                         | Conexion |
|------------|-----------------------------------|---------------------------------|----------|
| MongoDB    | `app/adapters/mongo_adapter.py`    | `pymongo`                       | Pool cacheado (`lru_cache`) |
| Neo4j      | `app/adapters/neo4j_adapter.py`    | `neo4j` (driver oficial)        | Pool cacheado (`lru_cache`) |
| Cassandra  | `app/adapters/cassandra_adapter.py`| `cassandra-driver`               | Pool cacheado (`lru_cache`) |
| Redis      | `app/adapters/redis_adapter.py`    | `redis-py`                      | Pool cacheado (`lru_cache`) |
| InfluxDB 3 | `app/adapters/influx_adapter.py`   | REST (`requests`) + SQL parametrizado | Sin estado: un POST HTTP por consulta |
| IRIS       | `app/adapters/iris_adapter.py`     | `intersystems-irispython` (DB-API) | Conexion nueva por consulta (ver seccion 4) |

Los adaptadores con pool (Mongo/Neo4j/Cassandra/Redis) exponen una
funcion `cerrar_*()` que `main.py` invoca desde el `lifespan` de
FastAPI al apagar la aplicacion, para no dejar conexiones abiertas.
IRIS e InfluxDB no necesitan esa funcion porque no mantienen estado
entre requests (ver seccion 4).

## 3. Patron de conexion: singleton cacheado (Mongo/Neo4j/Cassandra/Redis)

Estos cuatro adaptadores usan `functools.lru_cache(maxsize=1)` sobre su
funcion `obtener_conexion()`/`obtener_cliente()`/`obtener_driver()`:
la primera llamada crea la conexion/pool, las siguientes reutilizan el
mismo objeto cacheado. Evita abrir una conexion nueva por request. Si
la base se cae y se recupera, el propio pool del driver reconecta sus
sockets de forma transparente: el adaptador no necesita hacer nada
especial.

## 4. Por que IRIS es distinto: conexion nueva por request

`intersystems-irispython` no ofrece ese mismo pool en el modo DB-API
usado aca: una conexion abierta es un socket unico. Cachearla con
`lru_cache` (como las otras cuatro fuentes) expone un problema real: si
IRIS cae y vuelve a levantar, ese socket especifico queda invalido para
siempre, y todos los requests siguientes fallarian aunque la base ya
funcione — habria que detectar el error y descartar la conexion
cacheada a mano.

`app/adapters/iris_adapter.py` evita el problema de raiz: en vez de
cachear la conexion, `buscar_detalle_partido()` abre una conexion
nueva al entrar y la cierra en un `finally` al salir, para cada
consulta. No hay estado que pueda quedar invalido entre requests, asi
que no hace falta ninguna logica de reconexion manual. El costo es un
handshake TCP + autenticacion por consulta (aceptable para un endpoint
de lectura ocasional como este); el beneficio es simplicidad y
correccion ante caidas sin codigo adicional.

El adaptador expone dos excepciones propias para que el router nunca
dependa del tipo de excepcion interno del driver (`iris.dbapi.Error`):

- `IrisNoDisponible`: no se pudo conectar (credenciales faltantes,
  timeout, error de red) → el router responde 503.
- `IrisConsultaError`: la conexion funcionaba pero la consulta SQL
  falló → el router lo trata como error interno (500), distinto de
  "la base no está disponible".

InfluxDB tampoco mantiene conexion persistente: cada consulta es un
POST HTTP independiente a `/api/v3/query_sql`, asi que tampoco hay
estado que pueda quedar invalido entre requests.

## 5. Contrato de error uniforme (RNF13)

Todas las fuentes devuelven el mismo formato ante un error, sin
filtrar detalles internos de la base:

```json
{ "code": "ALGO_ERROR", "message": "Descripcion para el consumidor" }
```

Taxonomia HTTP usada por los seis endpoints:

- 400: parametro con formato invalido (detectado **antes** de tocar la base).
- 404: el recurso solicitado no existe en esa fuente.
- 500 (solo IRIS): la conexion a IRIS funcionaba pero la consulta falló.
- 502 (solo InfluxDB): la base respondio pero con un payload que el adaptador no pudo interpretar.
- 503: la base no esta disponible (conexion rechazada, timeout, error del driver).

Ver el detalle completo por endpoint en `docs/contratos_y_errores.md`.

## 6. Validacion antes de consultar (RNF3/RF10)

Cada router valida el formato de sus parametros por expresion regular
**antes** de invocar al servicio/adaptador. Dos IDs idénticos en forma
pero de fuentes distintas tienen formatos reales distintos y por lo
tanto validadores distintos:

- `Partido.partidoId` en Neo4j: `P-<grupo o fase>-<numero>` (ej. `P-A-1`, `P-R32-6`).
- `partido_id` en Cassandra: `[A-Za-z][0-9]{3}` (ej. `M001`).
- `Fixture.Partido.Codigo` en IRIS: `[A-Z][0-9]{3}` (ej. `M004`) — mismo *formato* que Cassandra, pero son identificadores de bases distintas, nunca intercambiables.
- `usuario_id` en Redis: `U[0-9]{5}` (ej. `U27961`).
- `equipo_id` en MongoDB/InfluxDB: 3 letras (ej. `ARG`).

**Bug real corregido en este hito:** el router de Neo4j (`app/routes/partidos.py`)
compartía un único `validar_partido()` con el de Cassandra, usando el
regex de Cassandra (`[A-Za-z][0-9]{3}`) para validar también los IDs
de Neo4j. Como los IDs reales de Neo4j tienen el formato `P-A-1`, ese
regex los rechazaba **siempre** con 400 — toda consulta real a
`/partidos/{partido_id}/eventos` fallaba. Se separó en
`validar_partido_neo4j()` y `validar_partido_cassandra()`, cada una
aplicada a su ruta. Verificado en vivo (ver
`docs/pruebas_y_evidencia.md`): antes del fix, `GET /partidos/P-A-1/eventos`
devolvía 400; después, 200 con los eventos reales del partido.

## 7. Logging y trazabilidad (RF18/RNF10)

El middleware HTTP registrado en `app/main.py` agrega, por cada
request: un `request_id` (UUID4) devuelto en el header `X-Request-ID`,
la duración en milisegundos (`X-Response-Time-ms`), y un log con
método, ruta, la fuente NoSQL involucrada (inferida por el patrón de
la ruta) y el código de estado. No loguea query params, bodies ni
headers, para no dejar identificadores de usuario/sesión en texto
plano en los logs (RNF7). Un error no manejado que escape de un router
se captura en el propio middleware y se convierte en una respuesta
JSON 500 consistente, en vez de propagar una excepción cruda.
