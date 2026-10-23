# Matriz de conectividad — Hito 11

## 1. Cómo leer esta matriz

Los estados posibles son los definidos en el Hito 11 (RNF9):

- **up**: la prueba configurada para esa capa terminó correctamente.
- **down**: se intentó la prueba y falló.
- **degraded**: el servicio funciona con una dependencia afectada (se usa para el estado observado *durante* la prueba de fallo controlado, no como estado final).
- **unknown**: no se pudo evaluar o no se dispone de información suficiente.
- **not_configured**: el módulo no está preparado en este entorno (no aplica a ninguna de las seis fuentes: las seis están integradas en el Hito 10).

Un estado **up** en esta tabla significa "la prueba concreta que se describe funcionó en el momento indicado" (RNF17, honestidad experimental). No es una garantía de disponibilidad permanente ni de rendimiento — eso se evalúa en el Hito 12.

## 2. Entorno de la corrida

- Fecha/hora: 2026-10-23T17:15:55Z (ver `docs/evidencias/03_evaluacion_completa.txt`, corrida completa).
- Commit/rama: `hito11` (API del Hito 10 ya consolidada en `main`/`Day`).
- Entorno: API ejecutándose directamente en el host (no containerizada), bases en contenedores Docker Desktop, acceso por `127.0.0.1` y puertos publicados (ver `docs/topologia_y_entornos.md`).
- Script: `scripts/evaluar_conectividad_fixture2030.sh` (modo `all`).

## 3. Matriz

| Producto | Host:Puerto | Cliente usado | Contexto | Prueba ejecutada | Resultado | Latencia | Diagnóstico |
|---|---|---|---|---|---|---|---|
| MongoDB | 127.0.0.1:27017 | pymongo (vía `chequeo_nativo_python.py`, `mongosh` no instalado) | db `fixture2030` | auth contra `admin` + `ping` + `GET /selecciones/ARG` | **up** | API: 18 ms | Sin hallazgos. |
| Neo4j | 127.0.0.1:7687 (Bolt) / 7474 (Browser) | driver `neo4j` (vía fallback Python, `cypher-shell` no instalado) + Browser HTTP | database `neo4j` | `RETURN 1` + Browser HTTP 200 + `GET /partidos/P-A-1/eventos` | **up** | API: 34 ms | Sin hallazgos. |
| Cassandra | 127.0.0.1:9042 | `cassandra-driver` (vía fallback Python, `cqlsh` no instalado) | keyspace `fixture2030` | `SELECT ... LIMIT 1` sobre `comentarios_por_partido` + `GET /partidos/M001/comentarios` | **up** | API: 21 ms | Sin hallazgos. |
| Redis | 127.0.0.1:6379 | `redis-cli` | base 0 | `PING` + `GET /sesiones/U27961` | **up** | API: 20 ms | Ver `docs/evidencias/04_fallo_controlado_redis.txt`: se verificó también el ciclo caída→503→recuperación→200 sin reiniciar la API. |
| InfluxDB | 127.0.0.1:8181 | `curl` (health) + consulta SQL real vía API | database `fixture2030` | `GET /health` + `GET /partidos/M001/estadisticas` | **up** | API: 29 ms | `/health` sin token responde 401 (el servicio exige autenticación incluso para el endpoint de salud); la consulta real con token vía la API funciona. No es una falla, es una característica de InfluxDB 3 Core — ver `docs/diagnostico_fallas.md` ítem 2. |
| IRIS | 127.0.0.1:1972 (Superserver) / 52773 (Portal) | `curl` (portal) + TCP (Superserver) + DB-API real vía API | namespace `USER` | TCP al Superserver + `GET /partidos/M004/detalle` | **up** | API: 36 ms | El portal responde 404 en la ruta raíz `/` (hay que apuntar a `/csp/sys/UtilHome.csp`); el servicio está arriba y la consulta real por DB-API funciona. Ver `docs/diagnostico_fallas.md` ítem 3. |

## 4. Casos de borde verificados por la API (RF18)

| Caso | Endpoint | Resultado esperado | Resultado observado |
|---|---|---|---|
| Error de validación | `GET /selecciones/1234` | 400 | **400** ✓ |
| ID de otra fuente (bug real del Hito 10, ya corregido) | `GET /partidos/M001/eventos` | 400 | **400** ✓ |
| Respuesta vacía válida (no es "caído") | `GET /partidos/M001/comentarios?bucket_temporal=00:00-00:05` | 200, lista vacía | **200**, `comentarios: []` ✓ |
| Recurso inexistente | `GET /partidos/Z999/detalle` | 404 | **404** ✓ |
| Dependencia caída (fallo controlado) | `GET /sesiones/U27961` con Redis detenido | 503 | **503** ✓ (ver evidencia 04) |

## 5. Resumen de la corrida completa

Total: 24 pruebas | OK: 22 | WARN: 2 (InfluxDB health sin token, IRIS portal ruta raíz — ambos explicados arriba, no son fallas) | FAIL: 0 | SKIP: 0.

Evidencia completa: `docs/evidencias/03_evaluacion_completa.txt`.
