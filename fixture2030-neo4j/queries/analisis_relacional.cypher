// =============================================================================
// Hito 5 — Fixture 2030 | 5. ANÁLISIS RELACIONAL (camino, conectividad y
//                            centralidad)
//
// Propósito (RF9): obtener información que NO es evidente desde una tabla ni
// desde una colección documental, porque no depende del contenido de un
// registro sino de la FORMA de la red de enfrentamientos del torneo.
//
// Objeto de análisis: la RED DE RIVALIDADES. Dos selecciones están conectadas
// si compartieron al menos un partido. Esa red no está almacenada: emerge del
// patrón (Seleccion)-[:PARTICIPA_EN]->(Partido)<-[:PARTICIPA_EN]-(Seleccion).
//
// La interpretación completa de cada resultado está en docs/decisiones.md,
// sección "Análisis relacional".
//
// Ejecución:
//   docker compose exec neo4j cypher-shell -u neo4j -p <pass> -f /queries/analisis_relacional.cypher
// =============================================================================


// =============================================================================
// 5.1 CAMINO MÁS CORTO — grados de separación entre dos selecciones
//
// Objetivo: medir a qué "distancia competitiva" quedaron dos selecciones que
// nunca se enfrentaron, y por qué cadena de partidos se conectan.
//
// Pregunta: ¿cuál es la cadena más corta de enfrentamientos que une a Uruguay
//           con Nueva Zelanda?
//
// shortestPath() es un algoritmo nativo de Cypher: explora la red en anchura y
// devuelve el recorrido mínimo. Una consulta equivalente en el módulo
// documental exigiría iterar la colección de partidos ronda por ronda desde la
// aplicación, sin saber de antemano cuántas iteraciones harían falta.
// =============================================================================

MATCH (origen:Seleccion {seleccionId: 'URU'}), (destino:Seleccion {seleccionId: 'NZL'})
MATCH camino = shortestPath( (origen)-[:PARTICIPA_EN*..12]-(destino) )
RETURN [n IN nodes(camino) WHERE n:Seleccion   | n.pais]       AS cadenaDeSelecciones,
       [n IN nodes(camino) WHERE n:Partido  | n.partidoId]  AS partidosIntermedios,
       (length(camino) / 2)                                 AS gradosDeSeparacion;


// 5.1.1 El mismo análisis, generalizado: ¿a qué distancia quedó el campeón de
// todas las demás selecciones? Muestra cuán "cerca" estuvo el resto del torneo
// del equipo que lo ganó.
MATCH (campeon:Seleccion)-[r:PARTICIPA_EN]->(:Partido)-[:CORRESPONDE_A]->(:Fase {codigo: 'FINAL'})
WHERE r.resultado IN ['victoria', 'victoria_penales']
WITH campeon
MATCH (otro:Seleccion)
WHERE otro <> campeon
MATCH camino = shortestPath( (campeon)-[:PARTICIPA_EN*..12]-(otro) )
WITH campeon, (length(camino) / 2) AS grados, count(*) AS seleccionesEnBloque
RETURN campeon.pais       AS campeon,
       grados             AS gradosDeSeparacion,
       seleccionesEnBloque AS cantidadDeSelecciones
ORDER BY gradosDeSeparacion;


// =============================================================================
// 5.2 CONECTIVIDAD — grado de cada nodo en la red de rivalidades
//
// Objetivo: identificar qué selecciones tuvieron el recorrido más "expuesto",
// es decir, contra cuántos adversarios DISTINTOS debieron competir.
//
// Es una medida de centralidad de grado calculada con Cypher puro, sin
// depender de ningún plugin.
// =============================================================================

MATCH (e:Seleccion)-[:PARTICIPA_EN]->(p:Partido)<-[:PARTICIPA_EN]-(rival:Seleccion)
WITH e, count(DISTINCT rival) AS rivalesDistintos, count(DISTINCT p) AS partidosJugados
MATCH (e)-[:AFILIADO_A]->(c:Confederacion)
RETURN e.pais          AS seleccion,
       c.codigo        AS confederacion,
       e.ranking       AS rankingFifa,
       partidosJugados AS pj,
       rivalesDistintos AS gradoEnLaRed
ORDER BY gradoEnLaRed DESC, rankingFifa
LIMIT 12;


// 5.2.1 Conectividad entre confederaciones: ¿qué tan "mundial" fue el torneo?
// Cuenta los cruces efectivos entre cada par de confederaciones. Responde una
// pregunta estructural que ningún documento de partido contiene por separado.
MATCH (a:Seleccion)-[:PARTICIPA_EN]->(p:Partido)<-[:PARTICIPA_EN]-(b:Seleccion)
WHERE elementId(a) < elementId(b)
MATCH (a)-[:AFILIADO_A]->(ca:Confederacion)
MATCH (b)-[:AFILIADO_A]->(cb:Confederacion)
WITH CASE WHEN ca.codigo <= cb.codigo THEN ca.codigo ELSE cb.codigo END AS conf1,
     CASE WHEN ca.codigo <= cb.codigo THEN cb.codigo ELSE ca.codigo END AS conf2,
     count(DISTINCT p) AS cruces
RETURN conf1, conf2, cruces,
       CASE WHEN conf1 = conf2 THEN 'intra-confederación'
            ELSE 'inter-confederación' END AS tipo
ORDER BY cruces DESC;


// =============================================================================
// 5.3 CENTRALIDAD CON GDS — quién sostuvo la estructura del torneo
//
// Objetivo: identificar las selecciones que actúan como PUENTE de la red de
// rivalidades, es decir, aquellas por las que pasa la mayor cantidad de
// caminos más cortos entre todas las demás.
//
// Para usar Graph Data Science hay que proyectar primero un grafo en memoria.
// La red de rivalidades no existe como relación almacenada, así que se la
// proyecta con una agregación de Cypher sobre el patrón de dos saltos: el
// resultado es un grafo Seleccion-Seleccion no dirigido (la rivalidad es simétrica).
// =============================================================================

// 5.3.0 Limpieza defensiva: descarta la proyección si quedó de una corrida
// anterior, para que este archivo sea reejecutable.
CALL gds.graph.exists('rivalidades') YIELD exists
WITH exists WHERE exists
CALL gds.graph.drop('rivalidades') YIELD graphName
RETURN 'Proyeccion anterior eliminada: ' + graphName AS limpieza;

// 5.3.1 Proyección de la red de rivalidades (64 nodos, un enlace por cruce).
// elementId(a) < elementId(b) evita proyectar dos veces el mismo enfrentamiento.
MATCH (a:Seleccion)-[:PARTICIPA_EN]->(p:Partido)<-[:PARTICIPA_EN]-(b:Seleccion)
WHERE elementId(a) < elementId(b)
WITH gds.graph.project(
       'rivalidades', a, b, {},
       {undirectedRelationshipTypes: ['*']}
     ) AS g
RETURN g.graphName        AS proyeccion,
       g.nodeCount        AS selecciones,
       g.relationshipCount AS enlacesDeRivalidad;

// 5.3.2 Centralidad de intermediación (betweenness).
//
// Mide por cuántos caminos más cortos entre pares de selecciones pasa cada
// una. Un valor alto indica una selección que CONECTA zonas del torneo que de
// otro modo quedarían separadas: típicamente, equipos que avanzaron mucho en
// la eliminatoria y fueron enlazando llaves de distintas ramas del cuadro.
//
// Interpretación esperada: las selecciones que llegaron a semifinales dominan
// el ranking, porque la eliminatoria fusiona progresivamente las ramas del
// cuadro y ellas son el punto de unión.
CALL gds.betweenness.stream('rivalidades')
YIELD nodeId, score
WITH gds.util.asNode(nodeId) AS e, score
MATCH (e)-[:AFILIADO_A]->(c:Confederacion)
OPTIONAL MATCH (e)-[:PARTICIPA_EN]->(p:Partido)
RETURN e.pais       AS seleccion,
       c.codigo     AS confederacion,
       count(p)     AS partidosJugados,
       round(score, 2) AS intermediacion
ORDER BY intermediacion DESC
LIMIT 12;

// 5.3.3 PageRank sobre la misma red.
//
// Mientras betweenness mide "puente", PageRank mide "prestigio estructural":
// puntúa alto a la selección que enfrentó a rivales que, a su vez, enfrentaron
// a muchos otros. Es la lectura de la exigencia acumulada del camino recorrido.
CALL gds.pageRank.stream('rivalidades')
YIELD nodeId, score
WITH gds.util.asNode(nodeId) AS e, score
RETURN e.pais    AS seleccion,
       e.ranking AS rankingFifa,
       round(score, 4) AS pageRank
ORDER BY pageRank DESC
LIMIT 12;

// 5.3.4 Detección de comunidades (Louvain).
//
// Verificación estructural: si el modelo y la carga son coherentes, las
// comunidades detectadas deben parecerse a los grupos de la primera fase,
// porque la fase de grupos es la que concentra los enfrentamientos. El
// resultado permite comprobar que el subgrafo cargado tiene la topología
// esperada de un mundial, y no un conjunto de enlaces arbitrarios.
CALL gds.louvain.stream('rivalidades')
YIELD nodeId, communityId
WITH gds.util.asNode(nodeId) AS e, communityId
MATCH (e)-[:INTEGRA]->(g:Grupo)
WITH communityId,
     count(*) AS selecciones,
     collect(DISTINCT g.codigo) AS gruposDeOrigen,
     collect(e.pais)[0..5] AS ejemplos
RETURN communityId AS comunidad,
       selecciones,
       gruposDeOrigen,
       size(gruposDeOrigen) AS cantidadDeGruposMezclados,
       ejemplos
ORDER BY selecciones DESC, comunidad;

// 5.3.5 Liberación de la proyección en memoria.
CALL gds.graph.drop('rivalidades') YIELD graphName
RETURN 'Proyeccion liberada: ' + graphName AS limpieza;
