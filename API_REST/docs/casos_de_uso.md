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
- Estructura: Hash.
- Nomenclatura de claves: sesion:{usuarioId}.
- TTL: 1.800 segundos (30 minutos).
- Método: GET.
- Endpoint: /sesiones/{usuarioId}.
- Entrada: identificador del usuario.
- Respuesta: información de la sesión activa, incluyendo usuario, rol, último acceso, partido seguido y TTL restante.
- Operación: lectura del Hash mediante HGETALL y consulta del tiempo de vida mediante TTL.
- Sesión inexistente o expirada: HTTP 404.
- Identificador inválido: HTTP 400.
- Redis no disponible: HTTP 503.
- Éxito: HTTP 200 con información de la sesión.
- Consideración: la consulta es de solo lectura y no renueva automáticamente el TTL. Las sesiones expiran según el tiempo configurado.


### CU05 — Consultar estadísticas temporales

- Consumidor: aplicación Fixture 2030.
- Fuente: InfluxDB 3 Core.
- Base de datos: fixture2030.
- Tabla: estadisticas.
- Método: GET.
- Endpoint: /partidos/{partidoId}/estadisticas.
- Entrada: identificador del partido, identificador del equipo, fecha desde, fecha hasta y límite de resultados.
- Respuesta: estadísticas temporales del partido, incluyendo timestamp, equipo, porcentaje de posesión, pases y tiros.
- Operación: consulta SQL parametrizada, filtrando por partido_id, equipo_id e intervalo temporal.
- Intervalo máximo permitido: 24 horas.
- Límite máximo: 100 observaciones por solicitud.
- Validación: comprobar el formato de las fechas, su orden cronológico y los límites antes de consultar.
- Intervalo inválido o parámetros incorrectos: HTTP 400.
- Intervalo sin observaciones: HTTP 200 con lista vacía.
- InfluxDB no disponible: HTTP 503.
- Respuesta inválida de la dependencia: HTTP 502.
- Éxito: HTTP 200 con las estadísticas encontradas.
- Consideración: el endpoint es de solo lectura y utiliza consultas SQL acotadas para evitar recuperar un volumen ilimitado de datos.

### CU06 — Consultar el detalle de un partido

- Consumidor: aplicación Fixture 2030.
- Fuente: InterSystems IRIS Community Edition.
- Namespace: USER.
- Modelo: objetos persistentes.
- Clase principal: Fixture.Partido.
- Clase relacionada: Fixture.Evento.
- Relación: padre-hijo entre Partido y Evento.
- Método: GET.
- Endpoint: /partidos/{codigo}/detalle.
- Entrada: código del partido, por ejemplo M004.
- Respuesta: identificador, código, estado y eventos relacionados.
- Operación: consulta SQL parametrizada sobre la proyección de las clases persistentes.
- Identificador inválido: HTTP 400.
- Partido inexistente: HTTP 404.
- IRIS no disponible: HTTP 503.
- Error interno de consulta: HTTP 500.
- Éxito: HTTP 200 con la información del partido.
- Consideración: el endpoint es de solo lectura y no modifica objetos persistentes.
- Conectividad: cliente Python de InterSystems mediante DB-API.
- Configuración: host, puerto, namespace y credenciales mediante variables de entorno.
- Seguridad: las credenciales no se incluyen en el código ni en GitHub.

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