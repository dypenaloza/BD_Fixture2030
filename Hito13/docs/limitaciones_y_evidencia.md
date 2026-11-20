# Limitaciones y evidencia — Hito 13

## 1. Qué se midió directamente vs. qué es una señal indirecta (RNF3)

| Dato | Clasificación |
|---|---|
| `fixture2030_http_requests_total`, `fixture2030_http_request_duration_seconds` | Medido directamente (instrumentación propia en `app/main.py`) |
| `redis_up`, `redis_connected_clients`, `redis_memory_used_bytes` | Medido directamente por el exporter dedicado |
| `mongodb_up`, `mongodb_ss_connections` | Medido directamente por el exporter dedicado |
| `probe_success` (Neo4j/Cassandra/InfluxDB/IRIS) | Señal indirecta: solo dice "hay un socket TCP que acepta conexión", no mide nada interno del motor |
| CPU/memoria de contenedores | **No medido** — no se incorporó `cAdvisor` ni equivalente (ver `inventario_de_componentes.md`) |
| Health/readiness/diagnóstico consolidado por dependencia | **Propuesto, no implementado** en el código de la API (ver `API_REST/docs/health_readiness.md` del Hito 11, que ya documentaba esta misma propuesta) |

## 2. Hallazgo central de este hito: "exporter arriba" ≠ "base disponible"

Durante la prueba de falla controlada (`evidencia/prueba_de_falla.md`)
se encontró que el target de Prometheus para el exporter de Redis
permaneció en `up` incluso con Redis completamente caído, porque el
*proceso del exporter* seguía respondiendo al scrape — solo la métrica
propia `redis_up` (que el exporter calcula intentando conectarse a la
base) reflejó la caída real.

Esto es la misma idea de la Clase 12 y del Hito 11 ("un contenedor
activo no equivale a una dependencia disponible"), pero un nivel más
abajo: acá ni siquiera "el exporter respondiendo" equivale a "la base
disponible". Se corrigió la alerta correspondiente
(`BaseInalcanzableDesdeSuExporter`, antes `ExporterSinResponder`) y se
documentó en `docs/alertas_y_umbral.md` #4 para que quede explícito
por qué importa la distinción.

## 3. Otras limitaciones conocidas

- **Volumen de tráfico**: las métricas de volumen/latencia reflejan el
  tráfico generado manualmente durante la demostración del monitoreo
  (decenas de requests), no una prueba de carga como la del Hito 12.
  No se puede afirmar nada sobre comportamiento bajo miles de
  requests/segundo a partir de esta evidencia.
- **Retención de Prometheus**: se usó la retención por defecto de la
  imagen (15 días), sin configuración adicional — suficiente para la
  duración del laboratorio, no pensada para producción.
- **Un solo escenario de falla ejercitado**: se detuvo Redis como caso
  representativo (RNF13 permite evaluar por producto sin exigir que
  todas las dependencias fallen a la vez). El mismo patrón aplicaría a
  cualquier otra fuente con exporter dedicado (MongoDB) o blackbox
  (Neo4j/Cassandra/InfluxDB/IRIS, que ya se comprueban en Hito 11,
  `docs/evidencias/04_fallo_controlado_redis.txt` ahí también fue
  Redis — queda como trabajo futuro variar la dependencia).
- **Sin autenticación en `/metrics`**: el endpoint de métricas de la
  API no requiere token (RNF6: no expone secretos, solo contadores
  agregados, pero en un entorno real conviene restringirlo a la red
  interna de Prometheus).
- **Sin exporter JMX para Cassandra ni plugin de métricas para Neo4j
  Community**: ambos requerirían agentes adicionales no incorporados
  en este laboratorio por motivos de tiempo (ver `inventario_de_componentes.md`).
- **`host.docker.internal` puede resolver a una ruta IPv6 inalcanzable**:
  en algunos hosts Docker Desktop (Windows con WSL2 entre ellos), el
  `tcp_connect` del blackbox exporter resolvía `host.docker.internal` a
  una dirección IPv6 sin salida desde el contenedor ("network is
  unreachable"), marcando como caídas las 4 fuentes sin exporter
  dedicado (Neo4j/Cassandra/InfluxDB/IRIS) aunque estuvieran arriba y
  respondiendo por IPv4. Se corrigió fijando
  `preferred_ip_protocol: ip4` en `blackbox/blackbox.yml`. Encontrado
  al levantar el entorno completo en una máquina distinta a la
  original, no durante el desarrollo original del Hito 13 — queda
  anotado por si vuelve a aparecer en otro entorno.

## 4. Trazabilidad de la evidencia (RNF2/RNF18)

Todas las capturas de `evidencia/` fueron tomadas en la misma sesión,
commit `7fcae442d4695990745709130678b62564e707aa` de `main`, entre las
23:45 y las 23:52 (UTC) del día de la ejecución. El detalle completo
con cada timestamp está en `evidencia/prueba_de_falla.md`.
