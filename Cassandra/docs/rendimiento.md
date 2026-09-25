Rendimiento

Fecha de ejecución: 25/09/2026

Versión de Cassandra: 5.0.9
Versión de cqlsh: 6.2.0

Ambiente de prueba:
- Cassandra ejecutado localmente con Docker Compose.
- Nodo único de laboratorio.
- Imagen utilizada: cassandra:latest.

Carga masiva

Se generaron 1.050.000 comentarios sintéticos reproducibles y se cargaron en dos tablas:

1. comentarios_por_partido
- Filas cargadas: 1.050.000
- Tiempo total: 43.922 segundos
- Tasa promedio: 23.906 filas/s

2. comentarios_por_usuario
- Filas cargadas: 1.050.000
- Tiempo total: 34.993 segundos
- Tasa promedio: 30.006 filas/s

Resultado

Las dos cargas superaron el objetivo de referencia de 10.000 escrituras por segundo indicado en el Hito 6.

Limitaciones

La prueba se realizó en un único nodo local, por lo que no representa el comportamiento de un clúster productivo con múltiples nodos, réplicas, red o datacenters.

La tasa obtenida depende del hardware disponible, Docker, el proceso COPY de cqlsh y la carga existente en el equipo durante la prueba.