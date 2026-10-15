# Casos de uso — API REST Fixture 2030

## 1. Objetivo

Desarrollar una API REST que permita consultar información del Fixture Mundial 2030 almacenada en seis tecnologías NoSQL.

La aplicación utilizará rutas HTTP, servicios y adaptadores independientes para acceder a cada fuente, respetando sus modelos de datos y patrones de acceso.

## 2. Casos de uso

### CU01 — Consultar una selección

- Consumidor: aplicación Fixture 2030.
- Fuente: MongoDB.
- Base: fixture2030.
- Colección: selecciones.
- Método: GET.
- Endpoint: /selecciones/{id}.
- Entrada: identificador de la selección.
- Respuesta: información de la selección en formato JSON.
- Operación: lectura documental por identificador.
- Recurso inexistente: HTTP 404.
- MongoDB no disponible: HTTP 503.
- Éxito: HTTP 200 con la selección solicitada.

### CU02 — Consultar eventos de un partido

- Consumidor: aplicación Fixture 2030.
- Fuente: Neo4j.
- Método: GET.
- Endpoint: /partidos/{partidoId}/eventos.
- Entrada: identificador del partido.
- Respuesta: eventos asociados, incluyendo tipo, minuto y descripción.
- Operación: recorrido de la relación OCURRE_EN mediante Cypher parametrizado.
- Partido inexistente: HTTP 404.
- Partido existente sin eventos: HTTP 200 con lista vacía.
- Neo4j no disponible: HTTP 503.
- Éxito: HTTP 200 con los eventos encontrados.

### CU03 — Consultar comentarios de un partido

- Consumidor: aplicación Fixture 2030.
- Fuente: Cassandra.
- Keyspace: fixture2030.
- Tabla: comentarios_por_partido.
- Método: GET.
- Endpoint: /partidos/{partidoId}/comentarios.
- Entrada: partidoId, bucket_temporal y limit.
- Respuesta: comentarios correspondientes a la partición solicitada.
- Operación: consulta CQL utilizando la clave de partición compuesta.
- Partición sin comentarios: HTTP 200 con lista vacía.
- Entrada inválida: HTTP 400.
- Cassandra no disponible: HTTP 503.
- Éxito: HTTP 200 con comentarios limitados y ordenados según el modelo.

### CU04 — Consultar una sesión

- Consumidor: aplicación Fixture 2030.
- Fuente: Redis.
- Método: GET.
- Endpoint: /sesiones/{id}.
- Entrada: identificador de sesión.
- Respuesta: información permitida de una sesión activa.
- Operación: lectura de una clave Redis mediante su estructura correspondiente.
- Sesión inexistente o expirada: HTTP 404.
- Redis no disponible: HTTP 503.
- Éxito: HTTP 200 con información de la sesión.

### CU05 — Consultar estadísticas temporales

- Consumidor: aplicación Fixture 2030.
- Fuente: InfluxDB 3 Core.
- Método: GET.
- Endpoint: /partidos/{partidoId}/estadisticas.
- Entrada: identificador del partido, fecha desde y fecha hasta.
- Respuesta: estadísticas registradas durante el intervalo solicitado.
- Operación: consulta SQL acotada por partido y rango temporal.
- Intervalo inválido: HTTP 400.
- Intervalo sin observaciones: HTTP 200 con lista vacía.
- InfluxDB no disponible: HTTP 503.
- Éxito: HTTP 200 con las estadísticas encontradas.

### CU06 — Consultar el detalle de un partido

- Consumidor: aplicación Fixture 2030.
- Fuente: InterSystems IRIS.
- Método: GET.
- Endpoint: /partidos/{id}/detalle.
- Entrada: identificador de la entidad persistente.
- Respuesta: información del partido obtenida del modelo de objetos.
- Operación: consulta de un objeto persistente mediante el adaptador IRIS.
- Entidad inexistente: HTTP 404.
- IRIS no disponible: HTTP 503.
- Éxito: HTTP 200 con el detalle solicitado.

## 3. Arquitectura

La aplicación utilizará la siguiente arquitectura:

Cliente HTTP
    |
Router
    |
Servicio
    |
Adaptador específico
    |
Base NoSQL

Responsabilidades:

- Router: recibe las solicitudes HTTP y valida sus parámetros.
- Servicio: ejecuta las reglas del caso de uso.
- Adaptador: establece la conexión y ejecuta las consultas específicas.
- Base NoSQL: almacena y recupera la información.

## 4. Validaciones y errores

La API utilizará respuestas HTTP consistentes:

- 200: operación de lectura exitosa.
- 400: entrada inválida.
- 404: recurso inexistente.
- 409: conflicto, cuando corresponda.
- 500: error interno inesperado.
- 503: dependencia no disponible.

Los errores tendrán un formato JSON común con los campos code y message.

La API no expondrá contraseñas, tokens ni información interna de las bases de datos.

## 5. Consideraciones técnicas

- MongoDB utilizará la colección real selecciones.
- Neo4j utilizará Cypher parametrizado y la relación OCURRE_EN.
- Cassandra respetará la clave de partición (partido_id, bucket_temporal).
- Redis contemplará la ausencia y expiración de claves.
- InfluxDB utilizará intervalos temporales acotados.
- IRIS accederá a los objetos persistentes del modelo desarrollado anteriormente.
- Las conexiones se configurarán mediante variables de entorno.
- Las consultas que puedan devolver múltiples registros tendrán límites.

## 6. Alcance inicial

Los seis endpoints propuestos serán de lectura.

Los identificadores y campos específicos de Redis, InfluxDB e IRIS se confirmarán contra los modelos reales antes de implementar sus adaptadores.

Los casos de uso documentados representan el diseño previsto, no endpoints ya implementados.

Las operaciones de escritura podrán incorporarse si el caso de uso lo requiere, documentando su comportamiento ante solicitudes repetidas.