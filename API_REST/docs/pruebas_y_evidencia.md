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