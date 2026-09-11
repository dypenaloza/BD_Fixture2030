// =============================================================================
// Hito 5 — Fixture 2030 | 2. CARGA idempotente del subgrafo
//
// Propósito (RF6, RNF4): cargar el dataset completo del torneo leyendo los CSV
// de import/ generados por import/generar_dataset.py.
//
// IDEMPOTENCIA — la propiedad central de este archivo:
//   * Todo nodo se crea con MERGE sobre su identificador único (declarado en
//     estructura.cypher). Si el nodo ya existe, MERGE lo encuentra y sólo se
//     reescriben sus propiedades con SET.
//   * Toda relación se crea con MERGE sobre el patrón completo, nunca con
//     CREATE. MERGE de una relación entre dos nodos ya vinculados no genera
//     una segunda relación paralela.
//   * Por lo tanto: ejecutar este archivo N veces deja exactamente el mismo
//     subgrafo que ejecutarlo una vez. La evidencia está en
//     docs/evidencia/03_carga_idempotente.txt, que compara los conteos de
//     nodos y relaciones de dos corridas consecutivas.
//
// REQUISITO PREVIO: ejecutar primero queries/estructura.cypher.
//
// Ejecución:
//   docker compose exec neo4j cypher-shell -u neo4j -p <pass> -f /queries/carga.cypher
//
// Los CSV se leen con file:/// porque ./import está montado en el contenedor
// sobre /var/lib/neo4j/import (ver docker-compose.yml). No se batchea con
// CALL { } IN TRANSACTIONS porque el archivo más grande tiene 1.536 filas y
// entra sin problema en una sola transacción.
// =============================================================================


// -----------------------------------------------------------------------------
// 2.1 Catálogos: confederaciones, grupos y fases
//
// Son nodos de clasificación con pocos elementos. Se modelan como nodos, y no
// como propiedades de texto del equipo o del partido, para poder agrupar y
// recorrer por ellos (ver docs/decisiones.md, decisión D2).
// -----------------------------------------------------------------------------

LOAD CSV WITH HEADERS FROM 'file:///confederaciones.csv' AS row
MERGE (c:Confederacion {codigo: row.codigo})
SET c.nombre = row.nombre;

LOAD CSV WITH HEADERS FROM 'file:///grupos.csv' AS row
MERGE (g:Grupo {codigo: row.codigo});

LOAD CSV WITH HEADERS FROM 'file:///fases.csv' AS row
MERGE (f:Fase {codigo: row.codigo})
SET f.nombre = row.nombre,
    f.orden  = toInteger(row.orden);


// -----------------------------------------------------------------------------
// 2.2 Equipos (64 selecciones)
//
// seleccionId es el _id del Hito 4 (código FIFA de 3 letras). La confederación y
// el grupo se convierten en relaciones hacia los catálogos ya creados.
// -----------------------------------------------------------------------------

LOAD CSV WITH HEADERS FROM 'file:///selecciones.csv' AS row
MERGE (e:Seleccion {seleccionId: row.seleccionId})
SET e.pais       = row.pais,
    e.nombre     = row.nombre,
    e.ranking    = toInteger(row.ranking),
    e.entrenador = row.entrenador,
    e.escudo     = row.escudo,
    e.anfitrion  = toBoolean(row.anfitrion)
WITH e, row
MATCH (c:Confederacion {codigo: row.confederacion})
MERGE (e)-[:AFILIADO_A]->(c)
WITH e, row
MATCH (g:Grupo {codigo: row.grupo})
MERGE (e)-[:INTEGRA]->(g);


// -----------------------------------------------------------------------------
// 2.3 Jugadores (1.536) y su pertenencia al plantel
//
// jugadorId es el _id del Hito 4 ("ARG-10"). El dorsal y la condición de
// capitán se guardan como propiedades del NODO, igual que en el documento del
// jugador del Hito 4, para que la misma entidad se describa con los mismos
// campos en los dos módulos (ver docs/decisiones.md, decisión D3).
// -----------------------------------------------------------------------------

LOAD CSV WITH HEADERS FROM 'file:///jugadores.csv' AS row
MERGE (j:Jugador {jugadorId: row.jugadorId})
SET j.nombre          = row.nombre,
    j.apellido        = row.apellido,
    j.nombreCompleto  = row.nombre + ' ' + row.apellido,
    j.posicion        = row.posicion,
    j.fechaNacimiento = date(row.fechaNacimiento),
    j.altura          = toInteger(row.altura),
    j.peso            = toFloat(row.peso),
    j.club            = row.club,
    j.dorsal          = toInteger(row.dorsal),
    j.capitan         = toBoolean(row.capitan)
WITH j, row
MATCH (e:Seleccion {seleccionId: row.seleccionId})
MERGE (j)-[:PERTENECE_A]->(e);


// -----------------------------------------------------------------------------
// 2.4 Estadios (18 estadios)
//
// La relación :EN_PAIS_DE conecta cada sede con la selección de su país
// anfitrión, aprovechando que paisId es el mismo código FIFA que seleccionId.
// Es la relación que habilita preguntas como "¿qué selección jugó de local
// real, en un estadio de su propio país?" (consulta 4.6).
// -----------------------------------------------------------------------------

LOAD CSV WITH HEADERS FROM 'file:///estadios.csv' AS row
MERGE (s:Estadio {estadioId: row.estadioId})
SET s.nombre     = row.nombre,
    s.ciudad     = row.ciudad,
    s.capacidad  = toInteger(row.capacidad)
WITH s, row
MATCH (e:Seleccion {seleccionId: row.paisId})
MERGE (s)-[:EN_PAIS_DE]->(e);


// -----------------------------------------------------------------------------
// 2.5 Partidos (128: 96 de grupos + 32 de eliminatorias)
//
// La fecha se guarda como tipo date() —no como texto— para poder ordenar,
// comparar y filtrar por rango. Las propiedades de penales sólo existen en los
// partidos definidos por esa vía: asignar null con SET elimina la propiedad,
// por lo que los demás partidos no la tienen (y la operación sigue siendo
// idempotente).
// -----------------------------------------------------------------------------

LOAD CSV WITH HEADERS FROM 'file:///partidos.csv' AS row
MERGE (p:Partido {partidoId: row.partidoId})
SET p.fecha            = date(row.fecha),
    p.hora             = row.hora,
    p.jornada          = CASE row.jornada WHEN '' THEN null ELSE toInteger(row.jornada) END,
    p.estado           = row.estado,
    p.golesLocal       = toInteger(row.golesLocal),
    p.golesVisitante   = toInteger(row.golesVisitante),
    p.definidoPor      = row.definidoPor,
    p.penalesLocal     = CASE row.penalesLocal WHEN '' THEN null ELSE toInteger(row.penalesLocal) END,
    p.penalesVisitante = CASE row.penalesVisitante WHEN '' THEN null ELSE toInteger(row.penalesVisitante) END
WITH p, row
MATCH (s:Estadio {estadioId: row.estadioId})
MERGE (p)-[:SE_JUEGA_EN]->(s)
WITH p, row
MATCH (f:Fase {codigo: row.fase})
MERGE (p)-[:CORRESPONDE_A]->(f);


// -----------------------------------------------------------------------------
// 2.6 Participaciones: qué equipos disputaron cada partido
//
// Exactamente 2 relaciones :PARTICIPA_EN por partido (una por equipo). El rol
// (local / visitante), los goles y el resultado son propiedades de la
// RELACIÓN, porque describen la actuación de ese equipo en ese partido y no
// del equipo ni del partido por separado (docs/decisiones.md, decisión D4).
// -----------------------------------------------------------------------------

LOAD CSV WITH HEADERS FROM 'file:///participaciones.csv' AS row
MATCH (e:Seleccion  {seleccionId: row.seleccionId})
MATCH (p:Partido {partidoId: row.partidoId})
MERGE (e)-[r:PARTICIPA_EN]->(p)
SET r.rol            = row.rol,
    r.goles          = toInteger(row.goles),
    r.golesRecibidos = toInteger(row.golesRecibidos),
    r.resultado      = row.resultado;


// -----------------------------------------------------------------------------
// 2.7 Eventos deportivos (goles y tarjetas)
//
// Cada evento es un nodo propio —no una propiedad del partido— porque tiene
// dos vínculos independientes: el partido en el que ocurre y el jugador que lo
// protagoniza. Esa doble relación es justamente lo que permite ir del gol al
// jugador y del jugador a su selección en un solo recorrido.
// -----------------------------------------------------------------------------

LOAD CSV WITH HEADERS FROM 'file:///eventos.csv' AS row
MERGE (v:Evento {eventoId: row.eventoId})
SET v.tipo    = row.tipo,
    v.minuto  = toInteger(row.minuto),
    v.detalle = row.detalle
WITH v, row
MATCH (p:Partido {partidoId: row.partidoId})
MERGE (v)-[:OCURRE_EN]->(p)
WITH v, row
MATCH (j:Jugador {jugadorId: row.jugadorId})
MERGE (v)-[:PROTAGONIZADO_POR]->(j);


// -----------------------------------------------------------------------------
// 2.8 Resumen de la carga
//
// Estos conteos son los que deben permanecer IDÉNTICOS al volver a ejecutar
// este archivo (prueba de idempotencia, RNF4).
// -----------------------------------------------------------------------------

MATCH (n)
RETURN labels(n)[0] AS etiqueta, count(*) AS nodos
ORDER BY etiqueta;

MATCH ()-[r]->()
RETURN type(r) AS relacion, count(*) AS relaciones
ORDER BY relacion;
