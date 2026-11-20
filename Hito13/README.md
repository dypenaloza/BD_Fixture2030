# Hito 13 — Monitoreo y Defensa Final del Fixture 2030

Capa de observabilidad (Prometheus + Grafana) sobre la API integrada
del Hito 10 y las 6 bases NoSQL, más la preparación de la defensa
técnica grupal.

## 1. Requisitos

- Las 6 bases del Fixture 2030 levantadas (ver cada módulo:
  `MongoDB/`, `Neo4j/`, `Cassandra/`, `Redis/`, `InfluxDB/`, `IRIS/`),
  con sus datos de carga.
- La API del Hito 10 (`API_REST/`) corriendo en el **host** (no
  containerizada), con `.env` configurado — ver
  `API_REST/docs/conectividad_y_configuracion.md`. Requiere también
  `prometheus-client` (agregado a `API_REST/requirements.txt`).
- Docker y Docker Compose, para el stack de monitoreo de este hito.
- En Linux, Docker Engine ≥ 20.10 (soporte de `host-gateway` para
  `extra_hosts`, usado para que los contenedores de monitoreo alcancen
  a la API y a las bases publicadas en el host).

## 2. Variables de entorno / configuración sin secretos

Este hito no usa `.env` propio: toda la configuración está en
`docker-compose.yml` y `prometheus.yml` con valores por defecto no
sensibles. La única credencial es la de Grafana
(`GF_SECURITY_ADMIN_PASSWORD` en `docker-compose.yml`), pensada para
un laboratorio local, no para producción — cambiarla si se expone la
instancia fuera del entorno de laboratorio.

## 3. Orden de ejecución

```bash
# 1. Levantar las 6 bases y la API del Hito 10 (en terminales/pasos aparte)

# 2. Levantar Prometheus, Grafana y los exporters
chmod +x scripts/*.sh scripts/*.py
./scripts/iniciar_monitoreo.sh

# 3. Verificar que todos los targets respondan "up"
python3 scripts/verificar_targets.py

# 4. Abrir Grafana: http://localhost:3000 (admin / ver docker-compose.yml)
#    El dashboard "Fixture 2030 — Observabilidad (Hito 13)" ya esta
#    provisionado automaticamente.

# 5. (Opcional) Repetir la prueba de falla controlada
./scripts/ejecutar_prueba_controlada.sh

# 6. Al terminar
./scripts/limpiar_entorno.sh            # conserva el historial de metricas
./scripts/limpiar_entorno.sh --volumenes # tambien lo borra
```

## 4. Qué incluye

```
docker-compose.yml          Prometheus, Grafana, redis_exporter,
                             mongodb_exporter, blackbox_exporter
prometheus.yml              Scrape configs (API + 2 exporters + 4 TCP)
prometheus/reglas-o-alertas.yml   4 alertas (ver docs/alertas_y_umbral.md)
blackbox/blackbox.yml       Modulo TCP para Neo4j/Cassandra/InfluxDB/IRIS
grafana/                    Datasource y dashboard provisionados
docs/                       Inventario, metricas/PromQL, alertas,
                             decisiones de arquitectura, limitaciones
evidencia/                  Capturas y logs de la demostracion real
                             (estado sano, falla controlada, recuperacion)
scripts/                    Inicio, verificacion, prueba controlada, limpieza
```

La carpeta `defensa/` (guion de 20 minutos, guía de demo ante la FIFA)
es el siguiente paso de este hito y todavía no está armada — requiere
que el equipo decida cómo presentar, no solo la parte de monitoreo.

## 5. Qué mide el dashboard (resumen, ver `docs/` para el detalle)

- **Disponibilidad** de las 6 bases + la API, distinguiendo qué es una
  métrica real del exporter (Mongo/Redis) de qué es solo un connect
  TCP (Neo4j/Cassandra/InfluxDB/IRIS).
- **Latencia P50/P95**, **volumen** y **errores 5xx** de la API, por
  fuente (base de datos).
- Una comparación explícita entre dos bases (Mongo vs Redis).
- Métricas de infraestructura de Redis y MongoDB (vía sus exporters).

## 6. Prueba de falla ya ejecutada

Ver `evidencia/prueba_de_falla.md` para el detalle completo (condición
inicial, cambio aplicado, respuesta observada, recuperación, datos
conservados) de la prueba sobre Redis, con capturas reales del
dashboard y de la página de alertas de Prometheus antes/durante/después.

## 7. Limitaciones

Ver `docs/limitaciones_y_evidencia.md` — incluye el hallazgo de que
"el exporter respondiendo" no es lo mismo que "la base disponible",
encontrado durante la propia prueba de falla de este hito.
