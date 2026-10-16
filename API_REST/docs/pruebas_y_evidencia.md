# Pruebas y evidencias — Hito 10

## 1. Objetivo

Verificar el funcionamiento de la API REST integrada del Fixture Mundial 2030, comprobando su conectividad con las seis bases NoSQL, las validaciones de entrada, el manejo de errores y la trazabilidad de las solicitudes.

## 2. Entorno de pruebas

- Sistema operativo: Windows.
- Contenedores: Docker Desktop.
- Aplicación: Python 3.11 y FastAPI.
- Servidor HTTP: Uvicorn.
- URL local: http://127.0.0.1:8000.
- Herramientas: Swagger UI, PowerShell y cURL.

## 3. Pruebas de integración

Se implementó el script tests/pruebas_integracion.ps1.

El script ejecuta solicitudes HTTP contra los seis módulos de la API y compara las respuestas con los códigos esperados.

Fuentes verificadas:

- MongoDB: consulta documental de selecciones.
- Neo4j: consulta parametrizada de eventos relacionados con partidos.
- Cassandra: consulta por clave de partición compuesta.
- Redis: lectura de sesiones Hash con TTL.
- InfluxDB: consulta SQL de estadísticas temporales.
- IRIS: consulta de objetos persistentes mediante su proyección SQL.

## 4. Validaciones

La API verifica los parámetros antes de ejecutar operaciones sobre las bases de datos.

Se contemplan:

- Identificadores inválidos.
- Recursos inexistentes.
- Sesiones ausentes o expiradas.
- Límites de resultados incorrectos.
- Intervalos temporales inválidos.
- Dependencias no disponibles.

## 5. Manejo de errores

Los principales códigos HTTP utilizados son:

- 200: consulta exitosa.
- 400: solicitud inválida.
- 404: recurso inexistente.
- 500: error interno inesperado.
- 502: respuesta inválida de una dependencia, cuando corresponda.
- 503: dependencia no disponible.

Los errores utilizan una estructura JSON consistente con los campos code y message.

## 6. Prueba de dependencia caída

Se realiza una prueba controlada deteniendo temporalmente Redis.

Mientras Redis está detenido, la API debe responder HTTP 503.

Posteriormente se reinicia el contenedor y se verifica su disponibilidad mediante PING.

Esta prueba permite diferenciar la ausencia de una sesión de una falla de conexión con Redis.

## 7. Observabilidad

La aplicación incorpora un middleware que registra:

- Identificador de solicitud.
- Método HTTP.
- Ruta solicitada.
- Fuente de datos.
- Código HTTP.
- Duración en milisegundos.

Las respuestas incluyen los encabezados X-Request-ID y X-Response-Time-ms.

No se registran contraseñas, tokens ni cuerpos sensibles.

## 8. Idempotencia

Los endpoints implementados son de lectura mediante GET.

Repetir una solicitud no debería modificar los datos almacenados ni generar registros duplicados.

Sin embargo, el resultado de una consulta puede cambiar si los datos se actualizan o si una sesión Redis expira por TTL.

Las sesiones temporales utilizadas para las pruebas se crean mediante comandos de preparación del laboratorio, no mediante los endpoints de lectura de la API.

## 9. Limitaciones

Las pruebas se realizan sobre un entorno local de laboratorio.

Los resultados obtenidos no representan necesariamente el comportamiento de la API bajo grandes volúmenes de usuarios concurrentes.

La latencia puede variar según los recursos disponibles en la notebook, el estado de Docker y la cantidad de datos almacenados.

## 10. Resultados

Completar después de ejecutar las pruebas:

- Fecha: 16/10/2026
- Cantidad de pruebas: 12
- Pruebas exitosas: 12
- Pruebas fallidas: 0
- Dependencia detenida: Redis
- Resultado de la prueba de disponibilidad: Exitoso. Al detener Redis temporalmente, la API respondió HTTP 503 Service Unavailable con el código REDIS_UNAVAILABLE. La respuesta tardó 2061,82 ms. Posteriormente se reinició el contenedor y se verificó su funcionamiento mediante PONG.
- Observaciones: Se ejecutaron 12 pruebas de integración, todas exitosas. Los seis módulos devolvieron los códigos HTTP esperados (200, 400 y 404). Además, se verificó el manejo de una dependencia caída mediante HTTP 503, la generación de X-Request-ID y el registro del tiempo de respuesta.

## 11. Evidencias

Las capturas se almacenan en docs/evidencia/.

Cada evidencia debe mostrar una respuesta real de la aplicación y su código HTTP correspondiente.

## 12. Bug encontrado y corregido tras estas pruebas

Después de esta primera ronda de pruebas se detectó que el router de
Neo4j (`app/routes/partidos.py`) validaba `partido_id` con el mismo
regex que Cassandra (`[A-Za-z][0-9]{3}`, ej. "M001"), que **no
matchea** el formato real de los IDs de Neo4j (`P-<grupo|fase>-<numero>`,
ej. "P-A-1"). El dato usado en la prueba 3 ("Neo4j - Eventos de
partido", `/partidos/P001/eventos`) corresponde a un nodo de prueba
manual (`P001`) que el script oficial de carga
(`Neo4j/scripts/generar_fixture.py`) elimina al final del proceso; con
los datos reales cargados por ese script, ningún `partidoId` real
pasa la validación anterior y el endpoint devuelve 400 siempre.

Se corrigió separando la validación en `validar_partido_neo4j()`
(regex `P-[A-Za-z0-9]{1,4}-[0-9]{1,2}`) y `validar_partido_cassandra()`
(regex original), cada una aplicada a su ruta. Verificado en vivo
contra un `partidoId` real tras la corrección:

```
GET /partidos/P-A-1/eventos -> 200
{"partidoId":"P-A-1","cantidad":4,"eventos":[...]}
```

## 13. Suite de tests automatizados (pytest)

Además del script `tests/pruebas_integracion.ps1` (Windows/PowerShell),
se agregó una suite multiplataforma con `pytest`:

- `tests/unit/test_validaciones.py`: 33 tests de las funciones de
  validación por expresión regular/parsing (`validar_partido_neo4j`,
  `validar_partido_cassandra`, `validar_limite`, `validar_fecha`), sin
  necesidad de ninguna base levantada.
- `tests/integration/test_endpoints.py`: 18 tests end-to-end contra
  los seis endpoints de una instancia real de la API (se saltean
  automáticamente si la API no responde en `API_BASE_URL`), incluyendo
  el caso de partición/intervalo válido sin datos (200 con lista
  vacía) y la verificación de `X-Request-ID` en toda respuesta.

Correr ambas con `bash scripts/ejecutar_pruebas.sh`, o por separado con
`pytest tests/unit/ -v` y `pytest tests/integration/ -v`.