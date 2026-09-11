// =============================================================================
// Hito 5 — Fixture 2030 | 1. ESTRUCTURA: restricciones de unicidad e índices
//
// Propósito (RF10, RNF4): declarar las claves del subgrafo antes de cargar.
// Las restricciones de unicidad son la base de la idempotencia: cada MERGE de
// queries/carga.cypher se hace sobre una propiedad con restricción, por lo que
// una segunda corrida encuentra el nodo existente en lugar de duplicarlo.
//
// Todas las sentencias usan IF NOT EXISTS, así que este archivo puede
// ejecutarse cuantas veces sea necesario sin error.
//
// Ejecución:
//   docker compose exec neo4j cypher-shell -u neo4j -p <pass> -f /queries/estructura.cypher
// =============================================================================


// -----------------------------------------------------------------------------
// 1.1 Restricciones de unicidad — identificadores de entidad
//
// Los identificadores de Seleccion y Jugador son los MISMOS del Hito 4 (RF5):
//   seleccionId  = equipos.json._id     -> "ARG"
//   jugadorId = jugadores.json._id   -> "ARG-10"
// Declararlos únicos acá garantiza que el módulo de grafos no pueda
// representar dos veces la misma entidad del módulo documental.
// -----------------------------------------------------------------------------

CREATE CONSTRAINT equipo_id_unico IF NOT EXISTS
FOR (e:Seleccion) REQUIRE e.seleccionId IS UNIQUE;

CREATE CONSTRAINT jugador_id_unico IF NOT EXISTS
FOR (j:Jugador) REQUIRE j.jugadorId IS UNIQUE;

CREATE CONSTRAINT partido_id_unico IF NOT EXISTS
FOR (p:Partido) REQUIRE p.partidoId IS UNIQUE;

CREATE CONSTRAINT sede_id_unico IF NOT EXISTS
FOR (s:Estadio) REQUIRE s.estadioId IS UNIQUE;

CREATE CONSTRAINT evento_id_unico IF NOT EXISTS
FOR (v:Evento) REQUIRE v.eventoId IS UNIQUE;


// -----------------------------------------------------------------------------
// 1.2 Restricciones de unicidad — nodos de clasificación
//
// Confederación, Grupo y Fase son catálogos cerrados: 6, 16 y 7 nodos
// respectivamente. La unicidad de su código evita que la carga genere, por
// ejemplo, dos nodos "UEFA" al procesar los 64 equipos.
// -----------------------------------------------------------------------------

CREATE CONSTRAINT confederacion_codigo_unico IF NOT EXISTS
FOR (c:Confederacion) REQUIRE c.codigo IS UNIQUE;

CREATE CONSTRAINT grupo_codigo_unico IF NOT EXISTS
FOR (g:Grupo) REQUIRE g.codigo IS UNIQUE;

CREATE CONSTRAINT fase_codigo_unico IF NOT EXISTS
FOR (f:Fase) REQUIRE f.codigo IS UNIQUE;


// -----------------------------------------------------------------------------
// 1.3 Índices para los patrones de recuperación más frecuentes
//
// Una restricción de unicidad ya crea su propio índice, por lo que acá sólo se
// declaran índices sobre propiedades NO clave que aparecen en filtros y
// ordenamientos habituales durante el torneo. Cada uno responde a una consulta
// concreta de queries/consultas_grafo.cypher:
//
//   partido_fecha        -> "¿qué se juega hoy?" (agenda diaria del fixture)
//   partido_fecha_hora   -> grilla de programación ordenada por día y horario
//   equipo_ranking       -> rankings y top-N de selecciones
//   evento_tipo          -> tabla de goleadores y de tarjetas
//   jugador_posicion     -> planteles filtrados por puesto
//   fase_orden           -> recorrido del torneo en orden cronológico de fases
// -----------------------------------------------------------------------------

CREATE INDEX partido_fecha IF NOT EXISTS
FOR (p:Partido) ON (p.fecha);

CREATE INDEX partido_fecha_hora IF NOT EXISTS
FOR (p:Partido) ON (p.fecha, p.hora);

CREATE INDEX equipo_ranking IF NOT EXISTS
FOR (e:Seleccion) ON (e.ranking);

CREATE INDEX evento_tipo IF NOT EXISTS
FOR (v:Evento) ON (v.tipo);

CREATE INDEX jugador_posicion IF NOT EXISTS
FOR (j:Jugador) ON (j.posicion);

CREATE INDEX fase_orden IF NOT EXISTS
FOR (f:Fase) ON (f.orden);


// -----------------------------------------------------------------------------
// 1.4 Índice de texto completo — búsqueda de jugadores y selecciones
//
// Durante el torneo la búsqueda por nombre es una consulta de alta frecuencia y
// tolerante a errores de tipeo. Un índice de texto completo la resuelve sin
// recorrer los 1.536 nodos :Jugador, algo que un índice de rango no permite
// porque las búsquedas son por subcadena o aproximación, no por prefijo exacto.
// -----------------------------------------------------------------------------

CREATE FULLTEXT INDEX jugadores_por_nombre IF NOT EXISTS
FOR (j:Jugador) ON EACH [j.nombre, j.apellido, j.club];

CREATE FULLTEXT INDEX equipos_por_nombre IF NOT EXISTS
FOR (e:Seleccion) ON EACH [e.pais, e.nombre];


// -----------------------------------------------------------------------------
// 1.5 Verificación de lo declarado
//
// Nota sobre Neo4j Community: las restricciones de EXISTENCIA (IS NOT NULL),
// de TIPO y de CLAVE DE NODO son exclusivas de la edición Enterprise. En este
// ambiente se compensan de dos maneras:
//   a) la carga hace MERGE sobre la clave, por lo que un nodo nunca se crea sin
//      identificador;
//   b) queries/verificacion.cypher comprueba explícitamente que no existan
//      nodos sin clave ni relaciones con cardinalidad inesperada.
// -----------------------------------------------------------------------------

SHOW CONSTRAINTS YIELD name, type, labelsOrTypes, properties
RETURN name, type, labelsOrTypes, properties
ORDER BY name;

SHOW INDEXES YIELD name, type, labelsOrTypes, properties
RETURN name, type, labelsOrTypes, properties
ORDER BY name;
