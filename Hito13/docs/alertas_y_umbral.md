# Alertas y umbrales — Hito 13

Definidas en `prometheus/reglas-o-alertas.yml`, cargadas por Prometheus
(`rule_files`). Las cuatro fueron ejercitadas en la práctica (ver
`docs/limitaciones_y_evidencia.md` y `evidencia/prueba_de_falla.*`).

## 1. `APIErrorRateAlta`

- **Métrica**: `sum(rate(fixture2030_http_requests_total{estado=~"5.."}[5m])) by (fuente)`
- **Condición**: `> 0`
- **Duración mínima**: 1 minuto (`for: 1m`)
- **Severidad**: warning
- **Componente afectado**: la fuente (base) que etiqueta la serie.
- **Impacto posible en el Fixture**: los consumidores de ese endpoint
  reciben errores en vez de datos (selecciones, eventos, comentarios,
  sesiones, estadísticas o detalle de partido, según la fuente).
- **Acción de investigación/recuperación**: revisar el log de la API
  por `request_id` para esa fuente (middleware ya lo registra), y
  correlacionar con la disponibilidad de esa dependencia en el panel
  "Disponibilidad".
- **Por qué el umbral es razonable**: este sistema tiene 6 endpoints de
  solo lectura y volumen bajo (no es un sistema de alto tráfico con una
  tasa de error "de fondo" esperable). Cualquier error 5xx sostenido
  por más de 1 minuto ya indica que una dependencia dejó de responder,
  no una falla transitoria de un único request. El umbral está en la
  **duración** (1m), no en la magnitud de la tasa.

## 2. `APILatenciaP95Alta`

- **Métrica**: `histogram_quantile(0.95, sum(rate(fixture2030_http_request_duration_seconds_bucket[5m])) by (le, fuente))`
- **Condición**: `> 0.5` (500 ms)
- **Duración mínima**: 2 minutos
- **Severidad**: warning
- **Componente afectado**: la fuente con latencia elevada.
- **Impacto posible**: la API tarda en responder; en un escenario real
  de carga (Hito 12) esto degrada la experiencia del consumidor.
- **Acción**: revisar si la base correspondiente está bajo carga,
  reiniciando con el panel de latencia por fuente para aislar cuál.
- **Por qué el umbral es razonable**: las pruebas de carga del Hito 12
  midieron P95 de referencia de ~31 ms en el flujo de selecciones (ver
  `Hito12/docs/refuerzo_pruebas.md`, pareja oficial). 500 ms es más de
  15 veces ese valor base: suficientemente alto para no disparar por
  jitter normal de un entorno de laboratorio, pero capturando una
  degradación real.

## 3. `DependenciaTCPInalcanzable`

- **Métrica**: `probe_success{job="blackbox_tcp"}`
- **Condición**: `== 0`
- **Duración mínima**: 30 segundos
- **Severidad**: critical
- **Componente afectado**: Neo4j, Cassandra, InfluxDB o IRIS (según la
  etiqueta `componente`).
- **Impacto posible**: todo endpoint que dependa de esa fuente
  empezará a devolver 503 (igual que el patrón ya documentado para
  Redis en el Hito 11).
- **Acción**: confirmar si el contenedor está corriendo
  (`docker ps`) y si el puerto está publicado correctamente; no asumir
  que "el contenedor está iniciado" implica "el puerto acepta
  conexiones" (ver Hito 11, nota 7 del material de clase).
- **Por qué el umbral es razonable**: 30 segundos es mayor a 3
  intervalos de scraping (10s cada uno), suficiente para descartar un
  único scrape fallido transitorio sin demorar demasiado la detección
  de una caída real.

## 4. `BaseInalcanzableDesdeSuExporter`

- **Métrica**: `redis_up == 0 or mongodb_up == 0`
- **Condición**: igualdad a 0 en cualquiera de las dos.
- **Duración mínima**: 30 segundos
- **Severidad**: critical
- **Componente afectado**: Redis o MongoDB.
- **Impacto posible**: igual al de `DependenciaTCPInalcanzable` pero
  para las dos fuentes con exporter dedicado.
- **Acción**: la misma que la anterior.
- **Por qué el umbral es razonable**: mismo razonamiento de 30s. Esta
  alerta reemplazó a una primera versión que usaba `up{job=~"redis|mongodb"}==0`,
  la cual **no detectó una caída real de Redis durante la prueba
  controlada** (el proceso del exporter seguía respondiendo al scrape
  aunque no podía hablar con Redis). Se corrigió usando la métrica
  propia de cada exporter (`redis_up`/`mongodb_up`), que sí refleja la
  conectividad real con la base. Este hallazgo está documentado en
  detalle en `docs/limitaciones_y_evidencia.md`.
