# Contratos y errores — API REST Fixture 2030

## 1. Formato de error comun

Toda respuesta de error (sin importar la fuente ni el código HTTP) usa
el mismo cuerpo JSON:

```json
{ "code": "ALGO_ERROR", "message": "Descripcion legible para el consumidor" }
```

Nunca se expone el stacktrace, el driver, ni detalles de conexion
(host, usuario, etc.) de la base en la respuesta.

## 2. Endpoints, parametros y codigos

### GET /selecciones/{codigo} — MongoDB

- `codigo`: 3 letras (`[A-Za-z]{3}`), ej. `ARG`.
- 200: selección encontrada.
- 400 `VALIDATION_ERROR`: código con formato inválido.
- 404 `SELECCION_NOT_FOUND`: código válido pero inexistente.
- 503 `DATABASE_UNAVAILABLE`: MongoDB no disponible.

### GET /partidos/{partido_id}/eventos — Neo4j

- `partido_id`: `P-<grupo|fase>-<numero>` (ej. `P-A-1`, `P-R32-6`).
- `limit` (query, opcional, default `20`): entero 1–50.
- 200: `{ partidoId, cantidad, eventos[] }`. Partido existente sin eventos → 200 con `eventos: []`.
- 400 `VALIDATION_ERROR`: `partido_id` o `limit` inválido.
- 404 `PARTIDO_NOT_FOUND`: `partido_id` con formato válido pero inexistente en Neo4j.
- 503 `NEO4J_UNAVAILABLE`: Neo4j no disponible.

### GET /partidos/{partido_id}/comentarios — Cassandra

- `partido_id`: `[A-Za-z][0-9]{3}` (ej. `M001`). **Nota:** mismo formato
  que IRIS pero son identificadores de fuentes distintas, no
  intercambiables.
- `bucket_temporal` (query, **obligatorio**): identifica la partición temporal (ej. `20:00-20:05`), máx. 40 caracteres.
- `limit` (query, opcional, default `20`): entero 1–50.
- 200: `{ partidoId, bucketTemporal, cantidad, comentarios[] }`. Partición sin comentarios → 200 con `comentarios: []`.
- 400 `VALIDATION_ERROR`: `partido_id`, `bucket_temporal` o `limit` inválido/ausente.
- 503 `CASSANDRA_UNAVAILABLE`: Cassandra no disponible.

### GET /sesiones/{usuario_id} — Redis

- `usuario_id`: `U[0-9]{5}` (ej. `U27961`).
- 200: datos de la sesión activa (incluye `ttlSegundos`).
- 400 `VALIDATION_ERROR`: identificador con formato inválido.
- 404 `SESSION_NOT_FOUND`: sesión inexistente o expirada (TTL vencido).
- 503 `REDIS_UNAVAILABLE`: Redis no disponible.

### GET /partidos/{partido_id}/estadisticas — InfluxDB 3

- `partido_id`: `[A-Z][0-9]{3}` (ej. `M001`).
- `equipo_id` (query, **obligatorio**): 3 letras (ej. `ARG`).
- `desde`, `hasta` (query, **obligatorios**): ISO-8601 con zona horaria; `hasta` debe ser posterior a `desde`; el intervalo no puede superar 24 horas.
- `limit` (query, opcional, default `20`): entero 1–100.
- 200: `{ partidoId, equipoId, cantidad, estadisticas[] }`.
- 400 `VALIDATION_ERROR`: cualquier parámetro faltante o con formato/rango inválido (incluye `equipo_id` ausente, intervalo invertido o mayor a 24h).
- 502 `INVALID_DEPENDENCY_RESPONSE`: InfluxDB respondió pero con un payload que el adaptador no pudo interpretar.
- 503 `INFLUX_UNAVAILABLE`: InfluxDB no disponible o no se pudo consultar (error de red/timeout).

### GET /partidos/{codigo}/detalle — IRIS

- `codigo`: `[A-Z][0-9]{3}` (ej. `M004`).
- 200: `{ id, codigo, estado, cantidadEventos, eventos[] }`, eventos ordenados por `minuto` ascendente.
- 400 `VALIDATION_ERROR`: código con formato inválido.
- 404 `PARTIDO_NOT_FOUND`: código con formato válido pero inexistente en IRIS.
- 500 `INTERNAL_ERROR`: la conexión a IRIS funcionaba pero la consulta falló (error de la proyección SQL, no de disponibilidad).
- 503 `IRIS_UNAVAILABLE`: IRIS no disponible (ver `docs/arquitectura_y_adaptadores.md` sección 4 — no requiere recuperación manual, al abrir una conexión nueva por consulta).

## 3. Reglas transversales

- La validación de formato ocurre **siempre antes** de tocar la base
  (RNF3/RF10): un parámetro inválido nunca genera una consulta real.
- Todos los identificadores de ruta se normalizan a mayúsculas antes
  de validar y consultar.
- Todos los endpoints son `GET` de solo lectura: son naturalmente
  idempotentes (repetir la misma llamada no cambia estado) y no
  requieren lógica de reintento del lado del servidor.
- Toda respuesta incluye los headers `X-Request-ID` y
  `X-Response-Time-ms` (ver `app/main.py`), útiles para correlacionar
  un error puntual con la línea de log del servidor y medir latencia.
- Cualquier excepción no capturada por un router es atrapada por el
  middleware HTTP y convertida en `500 {"code": "INTERNAL_ERROR", ...}`,
  nunca una excepción cruda.
