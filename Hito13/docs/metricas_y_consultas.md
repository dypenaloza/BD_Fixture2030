# Métricas y consultas PromQL — Hito 13

## 1. Métricas expuestas

### De la API (medidas directamente, instrumentación manual en `app/main.py`)

- `fixture2030_http_requests_total{fuente, ruta, metodo, estado}` —
  contador. Incrementa 1 por cada request HTTP atendido (se excluye
  `/metrics` para no contaminar el propio scraping).
- `fixture2030_http_request_duration_seconds{fuente, ruta}` —
  histograma, en **segundos**. Buckets: 5, 10, 25, 50, 100, 250, 500,
  1000, 2500, 5000 ms.

La etiqueta `fuente` reutiliza la misma clasificación por ruta que ya
usaba el middleware de logging (RF7: permite agrupar por base de datos
sin tener que recordar qué ruta corresponde a cuál).

### De los exporters (medidas directamente, por el exporter)

- `redis_up`, `mongodb_up` — 1 si el exporter pudo conectarse a la
  base, 0 si no. **No confundir con el `up` genérico de Prometheus**
  (ese dice si el *proceso del exporter* respondió al scrape, no si la
  base está disponible — ver hallazgo en
  `docs/limitaciones_y_evidencia.md`).
- `redis_connected_clients`, `redis_memory_used_bytes`.
- `mongodb_ss_connections{conn_type="active"|"available"}`.

### Por TCP (señal liviana, no una métrica interna del producto)

- `probe_success{job="blackbox_tcp", componente}` — 1 si
  `blackbox_exporter` pudo abrir un socket TCP contra el puerto de
  Neo4j, Cassandra, InfluxDB o IRIS; 0 si no.

## 2. Consultas PromQL explicadas (RF8, mínimo dos)

### Consulta 1 — Latencia P95 por fuente

```promql
histogram_quantile(0.95, sum(rate(fixture2030_http_request_duration_seconds_bucket[5m])) by (le, fuente))
```

- **Qué mide**: el percentil 95 de la duración de los requests HTTP,
  calculado sobre una ventana móvil de 5 minutos, agrupado por fuente
  (base de datos detrás de cada endpoint).
- **Unidad**: segundos.
- **Período**: ventana móvil de 5 minutos (`rate(...[5m])`); el punto
  se recalcula cada intervalo de scraping (10s).
- **Por qué P95 y no el promedio**: el promedio esconde outliers; P95
  responde "¿qué tan lenta es la peor solicitud típica?", que es lo
  relevante para decidir si hay que investigar (ver Hito 12, donde
  esta misma métrica fue la que motivó declarar una pareja de corridas
  oficial).

### Consulta 2 — Tasa de errores 5xx por fuente

```promql
sum(rate(fixture2030_http_requests_total{estado=~"5.."}[5m])) by (fuente)
```

- **Qué mide**: cuántos errores 5xx por segundo devolvió la API,
  agrupado por fuente, en una ventana móvil de 5 minutos.
- **Unidad**: errores/segundo.
- **Período**: ventana móvil de 5 minutos.
- **Por qué importa**: en este sistema (6 endpoints de solo lectura,
  volumen bajo), **cualquier valor sostenido mayor a 0** ya es
  anómalo — no hay "tasa de error aceptable" definida de antemano,
  a diferencia de un sistema de alto tráfico. Ver `alertas_y_umbral.md` #1.

### Consulta 3 (bonus) — Disponibilidad real de Redis/MongoDB

```promql
redis_up == 0 or mongodb_up == 0
```

- **Qué mide**: si el exporter de Redis o MongoDB no pudo conectarse a
  su base (no si el exporter mismo dejó de responder).
- **Unidad**: booleano (0/1).
- **Período**: instantáneo, sin ventana (no es una `rate`).
- **Por qué se agregó**: surgió de la prueba de falla controlada (RF10):
  la primera versión de la alerta usaba `up{job=...}==0`, que **no
  detectó** la caída real de Redis porque el proceso del exporter
  seguía respondiendo al scrape. Ver `docs/limitaciones_y_evidencia.md`.

## 3. Relación con los objetivos del TPO (RF11)

| Métrica | Objetivo del TPO que ilumina |
|---|---|
| `fixture2030_http_requests_total` (rate) | Throughput / volumen de operaciones |
| `fixture2030_http_request_duration_seconds` | Latencia |
| `redis_up`, `mongodb_up`, `probe_success` | Disponibilidad |
| Errores 5xx por fuente | Tolerancia a fallos / recuperación (junto con la prueba de falla controlada) |
| `redis_connected_clients`, `mongodb_ss_connections` | Concurrencia observada contra cada base |

No se midió throughput "de carga" en el sentido del Hito 12 (usuarios
concurrentes simulados): estas métricas reflejan el tráfico real
generado durante la demostración del monitoreo, no una prueba de
estrés.
