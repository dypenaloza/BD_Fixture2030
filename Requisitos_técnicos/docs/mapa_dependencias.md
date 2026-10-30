# Mapa de dependencias — Hito 11

## 1. Objetivo

Documentar las dependencias NoSQL de la API REST del Fixture Mundial 2030, identificando sus configuraciones, protocolos y mecanismos de conexión.

Este mapa permite preparar las pruebas de conectividad y diagnosticar posibles fallas.

## 2. Arquitectura

La API REST está desarrollada con FastAPI y utiliza una arquitectura por capas:

Cliente HTTP → Router → Servicio → Adaptador → Base NoSQL

Cada base de datos posee un adaptador independiente, responsable de utilizar su driver y ejecutar las consultas correspondientes.

Las seis bases se ejecutan en contenedores Docker independientes.

Según la configuración del proyecto, la API puede ejecutarse localmente en Windows y acceder a los puertos publicados mediante 127.0.0.1.

## 3. Dependencias

| Producto  | Host local | Puerto | Contexto    | Protocolo   |
| --------- | ---------- | ------ | ----------- | ----------- |
| MongoDB   | 127.0.0.1  | 27017  | fixture2030 | MongoDB     |
| Neo4j     | 127.0.0.1  | 7687   | neo4j       | Bolt        |
| Cassandra | 127.0.0.1  | 9042   | fixture2030 | CQL         |
| Redis     | 127.0.0.1  | 6379   | Base 0      | RESP        |
| InfluxDB  | 127.0.0.1  | 8181   | fixture2030 | HTTP        |
| IRIS      | 127.0.0.1  | 1972   | USER        | IRIS DB-API |

Los valores corresponden a la configuración documentada de la API. Las pruebas posteriores verificarán su funcionamiento.

## 4. Módulos y operaciones

**MongoDB**

* Módulo: selecciones.
* Colección: selecciones.
* Driver: pymongo.
* Operación: consultar una selección por código.
* Endpoint: GET /selecciones/ARG.

**Neo4j**

* Módulo: grafos de partidos y eventos.
* Driver: neo4j.
* Operación: consultar eventos relacionados con un partido.
* Endpoint: GET /partidos/P-A-1/eventos.

**Cassandra**

* Módulo: comentarios.
* Tabla: comentarios_por_partido.
* Driver: cassandra-driver.
* Operación: consultar comentarios por partido y bucket temporal.
* Endpoint: GET /partidos/M001/comentarios?bucket_temporal=20:00-20:05&limit=5

**Redis**

* Módulo: sesiones.
* Estructura: Hash con TTL.
* Driver: redis-py.
* Operación: recuperar una sesión activa.
* Endpoint: GET /sesiones/U27961.

**InfluxDB**

* Módulo: estadísticas temporales.
* Tabla: estadisticas.
* Cliente: requests mediante HTTP.
* Operación: consultar estadísticas dentro de un intervalo temporal.
* Endpoint: GET /partidos/M001/estadisticas, incluyendo equipo_id, desde y hasta.

**IRIS**

* Módulo: persistencia de partidos y eventos.
* Clases: Fixture.Partido y Fixture.Evento.
* Driver: intersystems-irispython.
* Operación: consultar los detalles de un partido.
* Endpoint: GET /partidos/M004/detalle.

## 5. Autenticación

Las credenciales se gestionan mediante variables de entorno.

* MongoDB: usuario y contraseña.
* Neo4j: usuario y contraseña.
* Cassandra: configuración de conexión del driver.
* Redis: URL de conexión.
* InfluxDB: token almacenado localmente.
* IRIS: usuario, contraseña y namespace.

No se documentan valores sensibles.

## 6. Puertos adicionales

* Neo4j Browser: 7474.
* IRIS Management Portal: 52873 desde Windows, correspondiente al puerto interno 52773.

Estos puertos permiten acceder a las interfaces de administración, pero no sustituyen la evaluación de los protocolos utilizados por la API.

## 7. Estado inicial

Durante el diagnóstico inicial se verificó que los seis contenedores Docker estaban iniciados.

Sin embargo, este resultado solamente confirma el estado de los procesos y la publicación de sus puertos.

Quedan pendientes las verificaciones TCP, autenticación, operaciones nativas y consultas mediante la API.

El estado de conectividad de cada dependencia se registrará en la matriz de resultados del Hito 11.
