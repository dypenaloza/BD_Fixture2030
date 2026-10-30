# Hito 11 — Evaluación de la conectividad a los productos del Fixture 2030

Procedimiento reproducible para evaluar que la API integrada del
Hito 10 realmente puede localizar, alcanzar, autenticar y usar cada
una de las 6 bases NoSQL — no solo que sus contenedores estén
iniciados.

## 1. Requisitos

- Las 6 bases del Hito 10 levantadas (Docker Desktop u otro runtime),
  con sus datos de carga de cada hito anterior.
- La API del Hito 10 (`API_REST/`) corriendo, con su propio `.env`
  configurado (ver `API_REST/docs/conectividad_y_configuracion.md`).
- Bash (Linux, macOS, WSL o Git Bash en Windows).
- `curl` (para las pruebas HTTP/API). Opcionales pero recomendados:
  `mongosh`, `cypher-shell`, `cqlsh`, `redis-cli`, `nc` — si no están
  instalados, el script usa automáticamente un chequeo equivalente en
  Python (`scripts/chequeo_nativo_python.py`) reutilizando los mismos
  drivers que ya requiere `API_REST/requirements.txt`, así que no hace
  falta instalar nada adicional para tener cobertura nativa real.

## 2. Variables de entorno

Ver `config/configuracion-ejemplo.env` para la lista completa con sus
defaults. Copiarlo y completar (sin commitear el resultado):

```bash
cp config/configuracion-ejemplo.env config/.env
# completar MONGO_PASSWORD, NEO4J_PASSWORD, etc.
set -a; source config/.env; set +a
```

`config/.env` está excluido por `config/.gitignore` y por el
`.gitignore` de esta carpeta: nunca se commitea con valores reales.

## 3. Orden de ejecución

```bash
chmod +x scripts/evaluar_conectividad_fixture2030.sh

# 1) Todas las pruebas (TCP + clientes nativos + API)
./scripts/evaluar_conectividad_fixture2030.sh

# Modos parciales, si se quiere evaluar una capa a la vez
# (la secuencia recomendada es de menor a mayor costo, ver sección 4):
./scripts/evaluar_conectividad_fixture2030.sh --tcp-only
./scripts/evaluar_conectividad_fixture2030.sh --native-only
./scripts/evaluar_conectividad_fixture2030.sh --api-only
```

La salida es texto plano; no imprime passwords ni tokens (RNF7), y se
puede redirigir a un archivo para guardarla como evidencia:

```bash
./scripts/evaluar_conectividad_fixture2030.sh > docs/evidencias/mi_corrida.txt
```

## 4. Qué evalúa el script, en orden

1. **TCP** — alcanzabilidad de los 6 puertos (`nc`, o `/dev/tcp` de
   bash si `nc` no está instalado).
2. **Clientes nativos / HTTP** — handshake real de cada protocolo
   (MongoDB, Bolt, CQL, RESP, HTTP de InfluxDB, Superserver/portal de
   IRIS), con el cliente nativo si está instalado o el equivalente en
   Python si no.
3. **API** — los 6 endpoints de negocio del Hito 10, con tiempo de
   respuesta y `request_id` (para cruzar con los logs de la API).
4. **Casos de borde de la API** — validación (400), recurso
   inexistente (404) y respuesta vacía válida (200 con lista vacía),
   para no confundir "sin datos" con "caído" (RF18).

No reemplaza la prueba por producto con una única llamada HTTP
genérica (RNF4): cada fuente se evalúa con su protocolo real.

## 5. Documentación

- `docs/mapa_dependencias.md` — qué conecta con qué, cómo y para qué.
- `docs/topologia_y_entornos.md` — dónde corre cada pieza y la
  diferencia entre `localhost` en la notebook y dentro de un contenedor.
- `docs/matriz_conectividad.md` — estado de cada dependencia con fecha,
  prueba, resultado y diagnóstico.
- `docs/diagnostico_fallas.md` — hallazgos reales encontrados con este
  procedimiento (hipótesis → prueba → resultado → corrección).
- `docs/health_readiness.md` — propuesta de liveness/readiness/health
  por dependencia para la API (no implementada en el Hito 10 actual).
- `docs/evidencias/` — salidas reales de las corridas, incluida la
  prueba de fallo controlado y recuperación de una dependencia.

## 6. Limitaciones conocidas

- Las pruebas se corrieron en un único entorno de laboratorio (host +
  Docker Desktop); no se evaluó el escenario de la API corriendo
  dentro de un contenedor con red Compose compartida (documentado
  como diferencia conceptual en `docs/topologia_y_entornos.md`, sección
  5, pero no ejecutado).
- El endpoint `/health` de InfluxDB exige autenticación en este
  entorno (401 sin token); no es una falla, ver `docs/diagnostico_fallas.md`.
- `/health`, `/ready` y el diagnóstico consolidado por dependencia son
  una propuesta documentada (`docs/health_readiness.md`), no código
  entregado en este hito.
- La prueba de fallo controlado (sección 5.7 del enunciado) se
  ejecutó sobre Redis como caso representativo; no se repitió para las
  6 fuentes (RNF13 permite evaluar por producto, por capa o completo
  sin exigir que todas las dependencias fallen a la vez).
