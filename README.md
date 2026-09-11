\# BD\_Fixture2030



\*\*Grupo 12\*\* · Ingeniería de Datos II, viernes turno noche

Integrantes: Dayana Peñaloza · Franco Churba · Juan Bautista Mangoni



Trabajo Práctico Obligatorio: plataforma NoSQL para el Fixture del Mundial

2030, construida de forma incremental a lo largo de los hitos de la

materia. Cada hito agrega un modelo de base de datos distinto sobre una

misma información de base (selecciones, jugadores, partidos, eventos).



\## Módulos del repositorio



| Módulo | Hito | Tecnología | Contenido |

|---|---|---|---|

| \[`MongoDB/`](MongoDB) | Hito 4 | MongoDB (documental) | Equipos y jugadores: colecciones, validaciones, carga, consultas e índices. |

| \[`fixture2030-neo4j/`](fixture2030-neo4j) | Hito 5 | Neo4j (grafos) | Relaciones del fixture: planteles, partidos, sedes y eventos, con consultas de recorrido y análisis relacional. |



Cada carpeta es autocontenida: tiene su propio `docker-compose.yml`,

su propio README con instrucciones de instalación y ejecución, y su propia

evidencia de carga y consultas. No es necesario levantar un módulo para

probar el otro.



\## Trazabilidad entre módulos



Ambos módulos comparten los mismos identificadores de equipos y jugadores

(por ejemplo, `ARG` para Argentina y `ARG-10` para un jugador de esa

selección), generados a partir del mismo dataset base. Así, una selección

o un jugador cargado en MongoDB (Hito 4) se puede reconocer sin ambigüedad

en el grafo de Neo4j (Hito 5). El detalle de esa correspondencia está

documentado en \[`fixture2030-neo4j/docs/decisiones.md`](fixture2030-neo4j/docs/decisiones.md).



\## Cómo empezar



Entrá a la carpeta del módulo que te interese y seguí su README:



```bash

cd MongoDB \&\& cat README.md

\# o

cd fixture2030-neo4j \&\& cat README.md

