# Inventario de componentes monitoreados — Hito 13

Regla seguida en todo este inventario (sección 5.1 del enunciado): una
base **no** se declara monitoreada solo porque aparece en el diagrama
de arquitectura. Cada fila de esta tabla tiene una métrica, un
exporter, un endpoint o una consulta real que la respalda —
verificable en `evidencia/`.

| Componente | Modelo de datos | Función en el Fixture | Puerto/endpoint | Mecanismo de monitoreo | Métricas seleccionadas | Riesgo que se observa | Limitación |
|---|---|---|---|---|---|---|---|
| API FastAPI (Hito 10) | — (orquesta las 6 bases) | Punto de entrada único de la plataforma | `127.0.0.1:8000/metrics` | Instrumentación manual con `prometheus_client` en `app/main.py`, reutilizando la misma clasificación "fuente" que ya usaba el logging | `fixture2030_http_requests_total`, `fixture2030_http_request_duration_seconds` (contador y, histograma, por `fuente`/`ruta`/`metodo`/`estado`) | Latencia alta o errores 5xx en cualquiera de los 6 flujos | Son métricas de aplicación (RF4), no miden CPU/memoria del proceso de la API en sí (ver limitaciones) |
| MongoDB | Documental | Selecciones y jugadores | `127.0.0.1:27017` | `mongodb_exporter` (percona, imagen `0.42`), apuntando al puerto publicado en el host | `mongodb_up` (conexión real), `mongodb_ss_connections` (activas/disponibles) | Conexión rota entre la API y Mongo | El exporter usa `--collect-all`; no se filtraron métricas, puede haber ruido de colecciones de sistema |
| Redis | Clave-valor (Hash + TTL) | Sesiones de usuario | `127.0.0.1:6379` | `redis_exporter` (oliver006, imagen `v1.65.0`) | `redis_up` (conexión real), `redis_connected_clients`, `redis_memory_used_bytes` | Caída de Redis, saturación de memoria | Igual que Mongo: `redis_up` es distinto del `up` genérico de Prometheus — ver `docs/limitaciones_y_evidencia.md`, hallazgo de la prueba de falla |
| Neo4j | Grafo | Relaciones partido↔evento↔jugador | `127.0.0.1:7687` (Bolt) | `blackbox_exporter`, módulo `tcp_connect` | `probe_success` | Puerto Bolt inalcanzable | **Solo disponibilidad TCP**, no hay métrica interna del motor (Neo4j Community no expone Prometheus nativamente sin plugins adicionales no usados en este laboratorio) |
| Cassandra | Columnar ancho | Comentarios por partido | `127.0.0.1:9042` (CQL) | `blackbox_exporter`, módulo `tcp_connect` | `probe_success` | Puerto CQL inalcanzable | Igual que Neo4j: solo TCP, no hay JMX exporter instalado en este laboratorio |
| InfluxDB 3 Core | Series temporales | Estadísticas de partido | `127.0.0.1:8181` (HTTP) | `blackbox_exporter`, módulo `tcp_connect` | `probe_success` | Puerto HTTP inalcanzable | No se usó un módulo HTTP porque `/health` exige token y devuelve 401 sin él (ver Hito 11): un 401 con el módulo `http_2xx` se hubiera visto como "caído" sin estarlo, así que se eligió TCP por honestidad del dato |
| InterSystems IRIS | Objetos/relacional | Entidades complejas (Partido/Evento) | `127.0.0.1:1972` (Superserver) | `blackbox_exporter`, módulo `tcp_connect` | `probe_success` | Puerto Superserver inalcanzable | Mismo caso: IRIS Community no expone métricas Prometheus nativas en este laboratorio |

## Qué NO está monitoreado, explícitamente

- CPU/memoria de los contenedores (no se incorporó `cAdvisor` ni
  equivalente): se prioriza la observabilidad de **comportamiento**
  (disponibilidad, latencia, volumen, errores) pedida por RF6 sobre
  métricas de infraestructura genéricas, dado el tiempo disponible del
  hito.
- CPU/memoria del propio proceso de la API.
- Métricas internas de consulta de Neo4j, Cassandra, InfluxDB e IRIS
  (requerirían JMX exporter, plugins o agentes adicionales no
  incorporados en este laboratorio — documentado arriba por fila).
