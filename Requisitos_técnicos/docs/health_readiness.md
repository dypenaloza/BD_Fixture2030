# Health, readiness y diagnóstico por dependencia — Hito 11

## 1. Estado actual (Hito 10)

La API del Hito 10 **no tiene** endpoints `/health`, `/live` ni
`/ready` dedicados. Lo que sí tiene, y que ya cumple parte del
objetivo de este apartado, es que **cada uno de los 6 endpoints de
negocio ya informa el estado de su propia dependencia** en cada
respuesta (contrato documentado en `API_REST/docs/contratos_y_errores.md`):
un 503 con `{"code": "MONGO_UNAVAILABLE"}` (o el equivalente de cada
fuente) es, de hecho, un diagnóstico puntual de esa dependencia en ese
momento.

Lo que falta, y que esta sección **propone** (no implementa en este
hito, por estar fuera del alcance de `Requisitos_técnicos/`, que no
modifica el código ya entregado del Hito 10), es una vista consolidada
de las 6 dependencias sin tener que llamar a los 6 endpoints de
negocio por separado.

## 2. Propuesta: tres preguntas distintas

Siguiendo la distinción de la Clase 12:

### `GET /health/live` (liveness)

¿Está vivo el proceso de la API? Debe responder sin consultar ninguna
base — si el proceso Python/Uvicorn puede ejecutar código, ya es
`200 {"status": "up"}`. Un liveness que depende de las 6 bases nunca
cumpliría su propósito: no serviría para saber si hay que reiniciar el
proceso o si el problema es de una dependencia externa.

### `GET /health/ready` (readiness)

¿Puede la API recibir tráfico real? Acá sí conviene exigir algo, pero
sin consultar las 6 bases en cada request (RNF12 "Degradación": evitar
reintentos ilimitados y esperas indefinidas, y no convertir cada
request normal en una tormenta de conexiones — ver Clase 12, sección
"Health, readiness y liveness"). Propuesta concreta:

- Mantener en memoria el resultado de la última verificación por
  dependencia, con una frecuencia acotada (ej. cada 15-30 segundos, no
  en cada request).
- `/ready` responde `200` si ninguna dependencia **esencial** está
  `down`, y `503` si alguna esencial lo está. "Esencial" es una
  decisión de producto: para este TPO, ninguna fuente es estrictamente
  bloqueante para las demás (cada endpoint es independiente — RNF13
  Independencia), así que `/ready` podría responder `200` mientras al
  menos una fuente esté operativa, y dejar que cada endpoint de negocio
  siga informando su propio 503 si su fuente puntual falló.

### `GET /health/dependencies` (diagnóstico por dependencia)

Vista consolidada de las 6 fuentes, no sustituye un chequeo profundo
en cada request de negocio:

```json
{
  "service": "fixture2030-api",
  "status": "degraded",
  "dependencies": {
    "mongodb":   { "status": "up",      "latencyMs": 8 },
    "neo4j":     { "status": "up",      "latencyMs": 12 },
    "cassandra": { "status": "up",      "latencyMs": 16 },
    "redis":     { "status": "up",      "latencyMs": 4 },
    "influxdb":  { "status": "up",      "latencyMs": 29 },
    "iris":      { "status": "down",    "reason": "timeout" }
  }
}
```

`status` a nivel servicio es `up` si las 6 están `up`, `degraded` si
alguna falló pero el resto funciona, `down` solo si ninguna fuente
responde.

## 3. Frecuencia, timeout y costo (si se implementara)

- **Frecuencia de chequeo profundo**: no en cada request. Propuesta:
  cachear el resultado por dependencia 15-30 segundos; `/health/*` lee
  del caché salvo que esté vencido.
- **Timeout por dependencia**: 2-3 segundos (igual al que ya usan los
  adaptadores del Hito 10 — `serverSelectionTimeoutMS=3000` en Mongo,
  `connection_timeout=3` en Neo4j, etc.), para que una dependencia
  lenta no bloquee la respuesta de `/health/dependencies` por las
  otras 5.
- **Costo**: 6 operaciones mínimas (ping/lectura de 1 fila) como
  máximo cada 15-30 segundos, nunca por request de negocio.

## 4. Por qué se documenta como propuesta y no se implementa ahora

El Hito 10 ya está entregado y probado end-to-end (ver
`API_REST/docs/pruebas_y_evidencia.md`). Agregar estos tres endpoints
sería una extensión menor y no destructiva de esa API, pero está fuera
del alcance que este hito define para `Requisitos_técnicos/` (RF22:
"montar el procedimiento, los scripts, la documentación y la evidencia
del hito en un repositorio" — no modificar la API ya entregada). Si el
equipo decide incorporarlos, la implementación es directa: un router
nuevo (`app/routes/health.py`) que reutilice las funciones
`obtener_*`/`buscar_*` ya existentes de cada adaptador con un timeout
corto y un caché simple en memoria.
