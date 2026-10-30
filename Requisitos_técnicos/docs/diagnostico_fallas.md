# Diagnóstico de fallas — Hito 11

Cada hallazgo sigue el formato pedido por RNF10: hipótesis, prueba
realizada, resultado y siguiente paso. Los tres primeros son bugs
reales encontrados **por el propio procedimiento de evaluación**
(exactamente el objetivo del hito: encontrar problemas reales, no
simularlos).

## 1. Puerto incorrecto en `IRIS_PORTAL_URL`

- **Síntoma**: `./scripts/evaluar_conectividad_fixture2030.sh` reportaba
  `[FAIL] IRIS portal HTTP` de forma consistente.
- **Hipótesis inicial**: el portal de IRIS no está publicado o el
  servicio no responde.
- **Prueba siguiente**: `docker port fixture2030-iris`, que mostró
  `52773/tcp -> 0.0.0.0:52773`. El script tenía como default
  `IRIS_PORTAL_URL=http://localhost:52873` (**52873**, no 52773: un
  typo de un dígito).
- **Resultado**: con el puerto correcto (52773), el portal responde
  (ver ítem 3 — responde 404 en `/`, pero eso es un problema distinto,
  de ruta, no de puerto).
- **Siguiente paso / corrección aplicada**: se corrigió el default en
  `scripts/evaluar_conectividad_fixture2030.sh` (línea `IRIS_PORTAL_URL`
  y el ejemplo de uso en `--help`) de `52873` a `52773`.

## 2. `check_tcp` para IRIS Superserver se saltaba innecesariamente

- **Síntoma**: `[SKIP] IRIS Superserver ... nc no está instalado`, aun
  en un entorno con `bash` disponible.
- **Hipótesis inicial**: la máquina realmente no puede probar el
  puerto 1972 sin `nc`.
- **Prueba siguiente**: revisar `check_tcp()` en el script — ya tiene
  un fallback a `bash -c "</dev/tcp/$host/$port"` cuando `nc` no está
  instalado. El problema era que `native_iris()` solo llamaba a
  `check_tcp` **dentro de un `if have nc`**, duplicando una condición
  que la propia función ya resuelve, y saltando el fallback de bash
  sin necesidad.
- **Resultado**: quitando esa condición redundante, el puerto 1972 se
  prueba igual (vía `/dev/tcp` de bash) sin requerir `nc`.
- **Siguiente paso / corrección aplicada**: se simplificó
  `native_iris()` para llamar a `check_tcp` directamente.

## 3. InfluxDB `/health` devuelve 401; IRIS portal devuelve 404 en `/`

- **Síntoma**: ambos aparecen como `[WARN]` en la corrida completa, no
  `[OK]`.
- **Hipótesis inicial**: ambos servicios podrían estar mal configurados
  o caídos.
- **Prueba siguiente**:
  - InfluxDB: `curl -i http://127.0.0.1:8181/health` sin token → 401.
    InfluxDB 3 Core exige autenticación incluso en su endpoint de
    salud en esta configuración; no es un fallo del servicio.
  - IRIS: `curl -I http://127.0.0.1:52773/` → 404, pero
    `curl -I http://127.0.0.1:52773/csp/sys/UtilHome.csp` → 200. El
    portal responde; la ruta raíz simplemente no tiene contenido.
- **Resultado**: ambos servicios están arriba. El `WARN` es correcto
  (RNF9: distinguir "no probado"/"caído" de "alcanzable con matices"),
  no debe interpretarse como una falla real — y se confirma con la
  consulta real de cada producto a través de la API (`GET
  /partidos/M001/estadisticas` y `GET /partidos/M004/detalle`, ambos
  200 con datos reales).
- **Siguiente paso**: ninguna corrección de código necesaria; queda
  documentado para que no se interprete como una regresión en una
  futura corrida.

## 4. Bug de origen del Hito 10 (contexto, no descubierto en este hito)

Para contexto: el bug de validación de `partidoId` en Neo4j
(`app/routes/partidos.py` usaba el regex de Cassandra para Neo4j) fue
encontrado y corregido durante el Hito 10 (ver
`API_REST/docs/pruebas_y_evidencia.md`, sección 12). Se reutiliza acá
como caso de prueba de regresión (`docs/evidencias/03_evaluacion_completa.txt`,
bloque "3b"): confirma que `/partidos/M001/eventos` sigue devolviendo
400 por formato inválido (correcto — M001 es un ID de Cassandra, no de
Neo4j) y que `/partidos/P-A-1/eventos` devuelve 200 con datos reales.

## 5. Tabla síntoma → hipótesis (material de referencia de la Clase 12)

Para los síntomas que no se dieron en esta corrida pero que el
procedimiento está preparado para diagnosticar:

| Síntoma | Hipótesis inicial | Prueba siguiente |
|---|---|---|
| `Connection refused` / TCP FAIL | No hay listener en el puerto | Revisar contenedor, puerto publicado y Compose |
| Timeout en capa TCP | Red bloqueada o proceso sin responder | Probar desde el mismo entorno que la API; reducir timeout |
| `Authentication failed` en cliente nativo | Credenciales o mecanismo equivocado | Verificar variables de entorno sin imprimir secretos |
| `Database/keyspace/namespace not found` | Contexto equivocado | Listar contextos con el cliente nativo |
| API devuelve 503 | El adaptador no puede usar la dependencia | Cruzar logs (request ID) con la prueba nativa equivalente |
| API devuelve 200 con lista vacía | Puede ser una lectura válida sin datos, no una falla | Confirmar con cliente nativo que el contexto/partición existe |
