// =============================================================================
// Hito 5 — Fixture 2030 | 4. CONSULTAS con patrones de grafo
//
// Propósito (RF8): responder preguntas reales del torneo recorriendo
// relaciones. Cada consulta indica su PREGUNTA, su PATRÓN y cuántos SALTOS
// recorre. Las marcadas con [MULTISALTO] atraviesan dos o más relaciones
// consecutivas; hay seis, por encima del mínimo de dos que pide el RF8.
//
// Ejecución completa:
//   docker compose exec neo4j cypher-shell -u neo4j -p <pass> -f /queries/consultas_grafo.cypher
// o bien copiar cada bloque en Neo4j Browser para ver el resultado como grafo.
// =============================================================================


// -----------------------------------------------------------------------------
// 4.1 Plantel de una selección                                   [1 salto]
//
// Pregunta: ¿quiénes integran el plantel de Uruguay y con qué dorsal?
// Patrón:   (Jugador)-[:PERTENECE_A]->(Seleccion)
//
// Una sola relación desde cada jugador hacia su selección. El dorsal y la
// capitanía son propiedades del nodo, como en el documento del Hito 4.
// -----------------------------------------------------------------------------
MATCH (j:Jugador)-[:PERTENECE_A]->(e:Seleccion {seleccionId: 'URU'})
RETURN j.dorsal         AS dorsal,
       j.nombreCompleto AS jugador,
       j.posicion       AS posicion,
       j.club           AS club,
       j.capitan        AS capitan
ORDER BY dorsal;


// -----------------------------------------------------------------------------
// 4.2 Agenda de una jornada                                      [2 saltos]
//
// Pregunta: ¿qué se juega el 13/06/2030, dónde y entre quiénes?
// Patrón:   (Seleccion)-[:PARTICIPA_EN]->(Partido)-[:SE_JUEGA_EN]->(Estadio)
//
// Es la consulta más frecuente durante el torneo y la que justifica el índice
// partido_fecha declarado en estructura.cypher.
// -----------------------------------------------------------------------------
MATCH (p:Partido {fecha: date('2030-06-13')})-[:SE_JUEGA_EN]->(s:Estadio)
MATCH (local:Seleccion)-[:PARTICIPA_EN {rol: 'local'}]->(p)
MATCH (visitante:Seleccion)-[:PARTICIPA_EN {rol: 'visitante'}]->(p)
RETURN p.partidoId  AS partido,
       p.hora       AS hora,
       local.pais   AS local,
       p.golesLocal + '-' + p.golesVisitante AS marcador,
       visitante.pais AS visitante,
       s.nombre     AS sede,
       s.ciudad     AS ciudad
ORDER BY hora;


// -----------------------------------------------------------------------------
// 4.3 Rivales de una selección a lo largo del torneo             [2 saltos]
//
// Pregunta: ¿contra quién jugó Argentina y con qué resultado?
// Patrón:   (Seleccion)-[:PARTICIPA_EN]->(Partido)<-[:PARTICIPA_EN]-(Seleccion)
//
// Este patrón —dos relaciones que convergen en el mismo nodo intermedio— es
// exactamente lo que una colección documental de partidos no resuelve sin
// recorrer todos los documentos: acá se sale de Argentina y se llega al rival
// atravesando el partido que los vincula.
// -----------------------------------------------------------------------------
MATCH (arg:Seleccion {seleccionId: 'ARG'})-[ra:PARTICIPA_EN]->(p:Partido)<-[rr:PARTICIPA_EN]-(rival:Seleccion)
MATCH (p)-[:CORRESPONDE_A]->(f:Fase)
RETURN p.fecha      AS fecha,
       f.nombre     AS fase,
       rival.pais   AS rival,
       ra.goles + '-' + rr.goles AS marcador,
       ra.resultado AS resultado
ORDER BY fecha;


// -----------------------------------------------------------------------------
// 4.4 [MULTISALTO] Jugadores a los que se enfrentó una selección [3 saltos]
//
// Pregunta: ¿qué delanteros rivales enfrentó Uruguay en el torneo?
// Patrón:   (Seleccion)-[:PARTICIPA_EN]->(Partido)<-[:PARTICIPA_EN]-(Seleccion)
//                                                <-[:PERTENECE_A]-(Jugador)
//
// Tres relaciones consecutivas para una pregunta que en el módulo documental
// exigiría unir la colección de partidos con la de jugadores por código de
// equipo, del lado de la aplicación.
// -----------------------------------------------------------------------------
MATCH (uru:Seleccion {seleccionId: 'URU'})-[:PARTICIPA_EN]->(p:Partido)
      <-[:PARTICIPA_EN]-(rival:Seleccion)<-[:PERTENECE_A]-(j:Jugador)
WHERE j.posicion = 'Delantero'
RETURN rival.pais       AS rival,
       count(DISTINCT p) AS partidosCruzados,
       collect(DISTINCT j.nombreCompleto)[0..3] AS algunosDelanteros
ORDER BY rival;


// -----------------------------------------------------------------------------
// 4.5 [MULTISALTO] Tabla de goleadores del torneo                [4 saltos]
//
// Pregunta: ¿quiénes son los máximos goleadores, de qué selección y en qué
//           fases convirtieron?
// Patrón:   (Evento)-[:PROTAGONIZADO_POR]->(Jugador)-[:PERTENECE_A]->(Seleccion)
//           (Evento)-[:OCURRE_EN]->(Partido)-[:CORRESPONDE_A]->(Fase)
//
// Cuatro relaciones consecutivas partiendo del evento. El índice evento_tipo
// acota el recorrido a los nodos de gol antes de empezar a navegar.
// -----------------------------------------------------------------------------
MATCH (v:Evento)-[:PROTAGONIZADO_POR]->(j:Jugador)-[:PERTENECE_A]->(e:Seleccion)
WHERE v.tipo IN ['gol', 'penal_convertido']
MATCH (v)-[:OCURRE_EN]->(p:Partido)-[:CORRESPONDE_A]->(f:Fase)
RETURN j.nombreCompleto AS goleador,
       e.pais           AS seleccion,
       j.posicion       AS posicion,
       count(v)         AS goles,
       collect(DISTINCT f.nombre) AS fases
ORDER BY goles DESC, goleador
LIMIT 15;


// -----------------------------------------------------------------------------
// 4.6 [MULTISALTO] Localía real: jugar en un estadio del propio país [3 saltos]
//
// Pregunta: ¿qué selecciones anfitrionas jugaron efectivamente en un estadio
//           de su propio país, y con qué rendimiento?
// Patrón:   (Seleccion)-[:PARTICIPA_EN]->(Partido)-[:SE_JUEGA_EN]->(Estadio)
//                                                -[:EN_PAIS_DE]->(Seleccion)
//
// El recorrido vuelve al MISMO nodo del que partió (e = anfitrion). Esa
// condición —cerrar un ciclo de tres relaciones sobre un nodo— es el tipo de
// pregunta que motiva usar un grafo: no depende de comparar campos sueltos
// sino de la forma del recorrido.
// -----------------------------------------------------------------------------
MATCH (e:Seleccion)-[r:PARTICIPA_EN]->(p:Partido)-[:SE_JUEGA_EN]->(s:Estadio)-[:EN_PAIS_DE]->(anfitrion:Seleccion)
WHERE e = anfitrion
RETURN e.pais            AS seleccion,
       count(p)          AS partidosEnCasa,
       collect(s.nombre) AS estadios,
       sum(r.goles)      AS golesConvertidos,
       collect(r.resultado) AS resultados
ORDER BY partidosEnCasa DESC, seleccion;


// -----------------------------------------------------------------------------
// 4.7 Tabla de posiciones de un grupo                            [2 saltos]
//
// Pregunta: ¿cómo terminó el Grupo A de la fase de grupos?
// Patrón:   (Seleccion)-[:INTEGRA]->(Grupo) + (Seleccion)-[:PARTICIPA_EN]->(Partido)
//
// Los puntos no están almacenados: se derivan del resultado guardado en cada
// relación :PARTICIPA_EN. Un solo lugar de verdad, sin datos redundantes que
// puedan quedar desactualizados.
// -----------------------------------------------------------------------------
MATCH (e:Seleccion)-[:INTEGRA]->(g:Grupo {codigo: 'A'})
MATCH (e)-[r:PARTICIPA_EN]->(p:Partido)-[:CORRESPONDE_A]->(:Fase {codigo: 'GRUPOS'})
RETURN e.pais AS seleccion,
       count(p) AS pj,
       sum(CASE r.resultado WHEN 'victoria' THEN 1 ELSE 0 END) AS pg,
       sum(CASE r.resultado WHEN 'empate'   THEN 1 ELSE 0 END) AS pe,
       sum(CASE r.resultado WHEN 'derrota'  THEN 1 ELSE 0 END) AS pp,
       sum(r.goles) AS gf,
       sum(r.golesRecibidos) AS gc,
       sum(r.goles) - sum(r.golesRecibidos) AS dg,
       sum(CASE r.resultado WHEN 'victoria' THEN 3
                            WHEN 'empate'   THEN 1
                            ELSE 0 END) AS puntos
ORDER BY puntos DESC, dg DESC, gf DESC;


// -----------------------------------------------------------------------------
// 4.8 [MULTISALTO] El camino del campeón                         [2 saltos]
//
// Pregunta: ¿qué recorrido hizo el campeón desde su debut hasta la final?
// Patrón:   (Seleccion)-[:PARTICIPA_EN]->(Partido)-[:CORRESPONDE_A]->(Fase)
//                    (Partido)-[:SE_JUEGA_EN]->(Estadio)
//
// El campeón no está marcado con ninguna propiedad: se lo identifica como el
// ganador del partido de la fase FINAL y desde ahí se reconstruye su camino.
// -----------------------------------------------------------------------------
MATCH (campeon:Seleccion)-[rf:PARTICIPA_EN]->(:Partido)-[:CORRESPONDE_A]->(:Fase {codigo: 'FINAL'})
WHERE rf.resultado IN ['victoria', 'victoria_penales']
WITH campeon
MATCH (campeon)-[r:PARTICIPA_EN]->(p:Partido)-[:CORRESPONDE_A]->(f:Fase)
MATCH (p)-[:SE_JUEGA_EN]->(s:Estadio)
MATCH (p)<-[rr:PARTICIPA_EN]-(rival:Seleccion)
WHERE rival <> campeon
RETURN f.orden       AS etapa,
       f.nombre      AS fase,
       p.fecha       AS fecha,
       campeon.pais  AS campeon,
       rival.pais    AS rival,
       r.goles + '-' + rr.goles AS marcador,
       r.resultado   AS resultado,
       s.nombre      AS sede
ORDER BY fecha;


// -----------------------------------------------------------------------------
// 4.9 [MULTISALTO] Rivales de los rivales: el 2.º grado          [4 saltos]
//
// Pregunta: ¿con qué selecciones NO se cruzó España pero sí sus rivales
//           directos? (adversarios potenciales a un cruce de distancia)
// Patrón:   (Seleccion)-[:PARTICIPA_EN]->(Partido)<-[:PARTICIPA_EN]-(rival)
//                   -[:PARTICIPA_EN]->(Partido)<-[:PARTICIPA_EN]-(indirecto)
//
// Es el equivalente futbolístico de "amigos de amigos": el caso clásico donde
// una base de grafos se impone a una consulta tabular o documental, porque el
// costo depende del vecindario recorrido y no del tamaño total de la base.
// El NOT ... EXISTS excluye a los que España ya enfrentó.
// -----------------------------------------------------------------------------
MATCH (esp:Seleccion {seleccionId: 'ESP'})-[:PARTICIPA_EN]->(:Partido)<-[:PARTICIPA_EN]-(rival:Seleccion)
MATCH (rival)-[:PARTICIPA_EN]->(:Partido)<-[:PARTICIPA_EN]-(indirecto:Seleccion)
WHERE indirecto <> esp
  AND NOT EXISTS {
        (esp)-[:PARTICIPA_EN]->(:Partido)<-[:PARTICIPA_EN]-(indirecto)
      }
RETURN indirecto.pais AS seleccionASegundoGrado,
       indirecto.ranking AS ranking,
       count(DISTINCT rival) AS rivalesEnComun,
       collect(DISTINCT rival.pais)[0..4] AS atravesDe
ORDER BY rivalesEnComun DESC, ranking
LIMIT 12;


// -----------------------------------------------------------------------------
// 4.10 Uso de las sedes                                          [2 saltos]
//
// Pregunta: ¿qué estadios concentraron más partidos y qué selecciones pasaron
//           por cada uno?
// Patrón:   (Estadio)<-[:SE_JUEGA_EN]-(Partido)<-[:PARTICIPA_EN]-(Seleccion)
// -----------------------------------------------------------------------------
MATCH (s:Estadio)<-[:SE_JUEGA_EN]-(p:Partido)<-[:PARTICIPA_EN]-(e:Seleccion)
RETURN s.nombre     AS sede,
       s.ciudad     AS ciudad,
       s.capacidad  AS capacidad,
       count(DISTINCT p) AS partidos,
       count(DISTINCT e) AS seleccionesDistintas
ORDER BY partidos DESC, sede
LIMIT 20;


// -----------------------------------------------------------------------------
// 4.11 [MULTISALTO] Disciplina: expulsiones y su contexto        [4 saltos]
//
// Pregunta: ¿quién vio la roja, de qué selección, en qué partido y en qué sede?
// Patrón:   (Evento)-[:PROTAGONIZADO_POR]->(Jugador)-[:PERTENECE_A]->(Seleccion)
//           (Evento)-[:OCURRE_EN]->(Partido)-[:SE_JUEGA_EN]->(Estadio)
// -----------------------------------------------------------------------------
MATCH (v:Evento {tipo: 'tarjeta_roja'})-[:PROTAGONIZADO_POR]->(j:Jugador)-[:PERTENECE_A]->(e:Seleccion)
MATCH (v)-[:OCURRE_EN]->(p:Partido)-[:SE_JUEGA_EN]->(s:Estadio)
RETURN p.fecha          AS fecha,
       j.nombreCompleto AS jugador,
       j.posicion       AS posicion,
       e.pais           AS seleccion,
       v.minuto         AS minuto,
       p.partidoId      AS partido,
       s.ciudad         AS ciudad
ORDER BY fecha, minuto
LIMIT 20;


// -----------------------------------------------------------------------------
// 4.12 Búsqueda por nombre con índice de texto completo          [2 saltos]
//
// Pregunta: ¿dónde juega un futbolista del que sólo sabemos el apellido?
// Usa el índice jugadores_por_nombre en lugar de recorrer los 1.536 nodos.
// -----------------------------------------------------------------------------
CALL db.index.fulltext.queryNodes('jugadores_por_nombre', 'Pérez~')
YIELD node AS j, score
MATCH (j)-[:PERTENECE_A]->(e:Seleccion)
RETURN round(score, 3)  AS relevancia,
       j.nombreCompleto AS jugador,
       j.dorsal         AS dorsal,
       e.pais           AS seleccion,
       j.club           AS club
ORDER BY relevancia DESC, jugador
LIMIT 10;


// -----------------------------------------------------------------------------
// 4.13 Filtro, ordenamiento y paginación
//
// Pregunta: ¿cuáles son los partidos con más goles del torneo? (página 1)
// Muestra WHERE + ORDER BY + SKIP/LIMIT sobre un patrón de dos relaciones.
// -----------------------------------------------------------------------------
MATCH (local:Seleccion)-[:PARTICIPA_EN {rol: 'local'}]->(p:Partido)<-[:PARTICIPA_EN {rol: 'visitante'}]-(visitante:Seleccion)
WITH p, local, visitante, p.golesLocal + p.golesVisitante AS totalGoles
WHERE totalGoles >= 5
MATCH (p)-[:CORRESPONDE_A]->(f:Fase)
RETURN p.partidoId AS partido,
       p.fecha     AS fecha,
       f.nombre    AS fase,
       local.pais  AS local,
       p.golesLocal + '-' + p.golesVisitante AS marcador,
       visitante.pais AS visitante,
       totalGoles
ORDER BY totalGoles DESC, fecha
SKIP 0 LIMIT 10;


// -----------------------------------------------------------------------------
// 4.14 Vista de grafo para Neo4j Browser (evidencia visual, RF11)
//
// Subgrafo acotado alrededor de la final: los dos finalistas, sus capitanes,
// la sede y los goles. Pensado para la pestaña "Graph" del Browser.
// -----------------------------------------------------------------------------
MATCH (p:Partido)-[:CORRESPONDE_A]->(:Fase {codigo: 'FINAL'})
MATCH camino1 = (e:Seleccion)-[:PARTICIPA_EN]->(p)-[:SE_JUEGA_EN]->(:Estadio)
MATCH camino2 = (v:Evento)-[:OCURRE_EN]->(p)
MATCH camino3 = (v)-[:PROTAGONIZADO_POR]->(:Jugador)-[:PERTENECE_A]->(e)
RETURN camino1, camino2, camino3;
