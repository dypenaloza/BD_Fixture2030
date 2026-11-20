# Guion de la defensa — 20 minutos (RF13, sección 6.2 del enunciado)

Esto es una **estructura sugerida**, no un libreto para leer. La
defensa es grupal: cada integrante debería poder tomar cualquiera de
estas partes, y cualquiera debería poder responder preguntas sobre
cualquier módulo (RNF12, sección 6 del enunciado: "todos los
integrantes deberán conocer el trabajo").

No ejecutar todos los scripts, todas las consultas y todas las
pantallas disponibles: elegir qué mostrar. El objetivo es demostrar
comprensión, no cobertura exhaustiva.

## Distribución del tiempo (orientativa)

| Minuto | Momento | Contenido | Quién podría llevarlo |
|---|---|---|---|
| 0:00–2:00 | Inicio | El problema de la FIFA, alcance del Fixture 2030, por qué una única base no alcanza | — |
| 2:00–6:00 | Arquitectura | Recorrido por los 6 módulos: qué dato vive en cada uno y por qué, capas Router→Servicio→Adaptador→Base | — |
| 6:00–12:00 | Decisiones | Justificación de modelos, patrones de acceso, particionamiento/réplica, consistencia (usar `docs/defensa_por_base.md`) | — |
| 12:00–16:00 | Operación | Demostración de 1-2 flujos completos desde la API (ver `demo.md`) | — |
| 16:00–18:30 | Evidencia | Grafana/Prometheus: disponibilidad, latencia, errores, prueba de falla controlada (Hito 13); resultados de carga (Hito 12) | — |
| 18:30–20:00 | Cierre | Por qué esta combinación es adecuada para el Fixture 2030, qué trade-offs se aceptaron, qué se mejoraría | — |

Completar la columna "Quién" antes de la defensa, para no improvisar
en el momento quién habla.

## 1. Inicio (≈2 min)

Puntos a cubrir:

- El Fixture Mundial 2030 necesita atender datos muy distintos entre
  sí: catálogos (selecciones/jugadores), relaciones (partidos↔eventos↔jugadores),
  comentarios de alto volumen en tiempo real, sesiones efímeras,
  series temporales de estadísticas, y entidades complejas con
  reglas propias (árbitros, incidencias). Cada uno tiene un patrón de
  acceso distinto.
- Decisión arquitectónica general: **polyglot persistence** — una base
  por tipo de dato/patrón de acceso, integradas detrás de una única
  API REST (Hito 10), en vez de forzar todo a un único motor.
- Esto no es "usar 6 tecnologías porque sí": cada una resuelve un
  problema que las otras resuelven peor o no resuelven (desarrollado
  en el punto 3).

## 2. Arquitectura (≈4 min)

```
Cliente HTTP (Swagger / Postman / curl)
        │
   API REST (FastAPI, Hito 10)
        │
┌───┬────┬─────┬─────┬────────┬──────┐
Mongo Neo4j Cassandra Redis InfluxDB IRIS
```

- Cada base tiene su propio adaptador (RNF1/RNF5 del Hito 10): el
  router valida, el servicio aplica reglas, el adaptador es el único
  lugar que conoce el driver nativo.
- Mostrar el mapa de dependencias real: `Requisitos_técnicos/docs/mapa_dependencias.md`
  (Hito 11) tiene host/puerto/contexto/driver por fuente.
- Mencionar observabilidad: desde el Hito 13, la API expone métricas
  Prometheus por fuente (`fixture2030_http_requests_total{fuente=...}`),
  lo que permite literalmente *ver* qué base atiende cada endpoint.

## 3. Decisiones (≈6 min) — lo más importante de la defensa

Usar la tabla de `docs/defensa_por_base.md` (una fila por base, con
los 10 puntos que pide la sección 6.4 del enunciado). No leerla
completa: elegir 2-3 bases para desarrollar en profundidad (ideal:
una con modelo claro tipo Mongo/Neo4j, y una con una decisión más
sutil tipo Cassandra/Redis) y las otras 3-4 mencionarlas más breve.

Preguntas que hay que poder responder sin mirar notas (sección 6.4 del
enunciado, ya cubiertas en `docs/defensa_por_base.md` por base):

- Por qué no conviene tratar todos los datos con una única estructura.
- Cómo se relacionan los módulos sin forzar una única base a resolver
  todo.
- Qué datos son operacionales y cuáles podrían proyectarse a una vista
  analítica.
- Dónde se usa caché (Redis) y cómo se invalida/expira (TTL).
- Cómo se evita que una consulta de alto volumen bloquee todo el
  sistema (límites/paginación en cada endpoint, ver
  `API_REST/docs/contratos_y_errores.md`).
- Qué parte de la escalabilidad fue medida (Hito 12) y qué parte es
  una proyección.
- Cómo se interpretan las métricas de Prometheus/Grafana (Hito 13).
- Qué decisión tomarían si una base queda temporalmente indisponible
  (ya demostrado en vivo: Hito 11 para Redis/IRIS, Hito 13 para Redis
  con evidencia en Grafana).

## 4. Operación (≈4 min)

Ver `demo.md` para el paso a paso concreto. Elegir **uno o dos** flujos
completos, no los seis. Sugerido: uno simple (MongoDB, lectura directa)
y uno que muestre una decisión interesante (Cassandra con partición
temporal, o Redis con TTL).

## 5. Evidencia (≈2:30 min)

- Abrir el dashboard de Grafana (`Hito13/`) y mostrar: disponibilidad
  de las 6 fuentes, el panel de comparación Mongo vs Redis, y repetir
  en vivo (si el tiempo alcanza) la prueba de falla sobre Redis
  (`Hito13/scripts/ejecutar_prueba_controlada.sh`) — si no alcanza el
  tiempo, mostrar directamente las capturas de `Hito13/evidencia/`.
- Mencionar los resultados de carga del Hito 12 (`Hito12/docs/refuerzo_pruebas.md`,
  pareja oficial de corridas) como la evidencia de qué SÍ se midió
  (P50/P95/P99 con y sin caché) vs. qué es una proyección (no se probó
  con miles de usuarios concurrentes).

## 6. Cierre (≈1:30 min)

Responder en voz alta la pregunta central del enunciado (sección 11):

> ¿Por qué esta combinación de modelos, estructuras, estrategias de
> distribución y mecanismos de observabilidad resulta adecuada para el
> Fixture Mundial 2030 bajo las condiciones planteadas?

Estructura sugerida de la respuesta:

1. Cada base resuelve un patrón de acceso real del Fixture (no una
   elección arbitraria) — repasar brevemente cuál resuelve cuál.
2. La integración vía una única API (Hito 10) evita que el consumidor
   tenga que conocer 6 protocolos distintos.
3. Qué trade-offs se aceptaron a sabiendas (ej: Cassandra sin JMX
   exporter, Neo4j Community sin métricas nativas — ver
   `Hito13/docs/limitaciones_y_evidencia.md`).
4. Qué se mejoraría con más tiempo (ej: health/readiness consolidado,
   propuesto pero no implementado — `API_REST/docs/health_readiness.md`;
   exporters dedicados para las 4 bases que hoy solo tienen chequeo
   TCP).
