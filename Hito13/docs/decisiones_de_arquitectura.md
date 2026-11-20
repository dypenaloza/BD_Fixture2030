# Decisiones de arquitectura del monitoreo — Hito 13

Este documento justifica las decisiones propias de la capa de
observabilidad. Las decisiones de modelado de cada base de datos (por
qué Mongo/Neo4j/Cassandra/Redis/InfluxDB/IRIS) ya están justificadas en
los documentos de cada hito anterior y se resumen para la defensa en
`defensa/guion_de_20_minutos.md`.

## 1. Instrumentación manual de la API, no una librería de auto-instrumentación

**Decisión**: usar `prometheus_client` directamente en
`app/main.py`, reutilizando la clasificación `fuente` que ya existía
en el middleware de logging, en vez de `prometheus-fastapi-instrumentator`
u otra librería de instrumentación automática.

**Por qué**: la auto-instrumentación genera métricas por
ruta/método/status "de fábrica", pero no sabe qué ruta corresponde a
qué base de datos (RF7 pide poder distinguir el comportamiento entre
fuentes). Agregar esa etiqueta a mano, sobre el código que el equipo
ya escribió y entiende, es más defendible en la exposición que
explicar una librería externa cuyo comportamiento interno no se
escribió. El costo es mantenimiento manual si se agregan rutas nuevas;
el beneficio es cero dependencias nuevas de peso y control total sobre
qué se mide.

## 2. TCP (blackbox) para las 4 fuentes sin exporter, no HTTP

**Decisión**: para Neo4j, Cassandra, InfluxDB e IRIS se usa el módulo
`tcp_connect` de `blackbox_exporter`, no un módulo HTTP.

**Por qué**: en el Hito 11 ya se encontró que un chequeo HTTP genérico
produce falsos negativos para estas fuentes: InfluxDB `/health`
devuelve 401 sin token (servicio arriba, pero "parece caído" para un
chequeo HTTP ingenuo) e IRIS devuelve 404 en la ruta raíz del portal
(mismo problema). Un connect TCP es una señal más pobre (solo dice
"hay un listener"), pero es honesta: no finge medir algo que no mide,
y no genera falsas alarmas por motivos de autenticación o ruteo HTTP
que no tienen que ver con la disponibilidad real del servicio.

## 3. `host.docker.internal` en vez de unir redes Docker por nombre

**Decisión**: todos los targets de Prometheus (la API y las 4 fuentes
sin exporter) se definen contra `host.docker.internal:<puerto>`, y los
dos exporters (`redis_exporter`, `mongodb_exporter`) también se
conectan a sus bases vía `host.docker.internal`.

**Por qué**: cada módulo del TPO (MongoDB, Neo4j, Cassandra, Redis,
InfluxDB, IRIS) tiene su **propio** `docker-compose.yml` con su propia
red Docker privada (`mongodb-network`, `neo4j-network`, etc. — ver
cada carpeta). Hacer que el stack de monitoreo se una a las 6 redes a
la vez es frágil y depende de que esos nombres no cambien. Como las 6
bases ya publican su puerto al host (necesario para que la propia API
del Hito 10 se conecte por `127.0.0.1`), usar esa misma vía desde los
contenedores de monitoreo evita acoplarse a los nombres de red de cada
módulo. El costo es que `host.docker.internal` requiere
`extra_hosts: host-gateway` en Linux (en Docker Desktop de Mac/Windows
ya viene resuelto); está documentado en `README.md`.

## 4. Alertas con `for` corto (30s-2m), no umbrales de minutos

**Decisión**: todas las alertas usan `for` de 30 segundos a 2 minutos.

**Por qué**: este es un laboratorio de clase, no un sistema productivo
con SLOs de horas. El objetivo es que una falla provocada a propósito
durante una demostración de 20 minutos sea visible dentro de esa misma
demostración. En un entorno productivo real estos valores se
ajustarían según el SLO de cada dependencia (ver justificación
cuantitativa por alerta en `docs/alertas_y_umbral.md`).

## 5. Un solo dashboard, no uno por base

**Decisión**: un dashboard único con filas por tema (disponibilidad,
latencia/volumen/errores de la API, infraestructura), no seis
dashboards separados.

**Por qué**: RF7 pide explícitamente una vista que permita *comparar*
al menos dos bases — eso requiere tenerlas en el mismo panel, no en
paneles aislados. Mantiene además el RNF9 (legibilidad): el estado de
toda la plataforma se puede diagnosticar sin cambiar de pantalla.
