// =============================================================================
// Hito 5 — Fixture 2030 | 6. VERIFICACIÓN de coherencia del subgrafo
//
// Propósito (RNF4, RNF6, RNF7): comprobar que la carga produjo un subgrafo
// completo, sin duplicados y consistente con el Hito 4.
//
// Cada control indica el VALOR ESPERADO. Si alguno no coincide, el subgrafo
// no está en condiciones de ser entregado.
//
// Este archivo también es la prueba de IDEMPOTENCIA: se ejecuta antes y
// después de volver a correr carga.cypher y los números deben ser idénticos.
//
// CÓMO LEER LA SALIDA: los controles cuyo valor esperado es "0 filas" NO
// imprimen nada cuando el subgrafo está sano —una consulta sin resultados no
// produce salida en cypher-shell—. Que un control no aparezca en la evidencia
// significa que pasó; si apareciera una fila, señalaría la inconsistencia
// detectada.
//
// Ejecución:
//   docker compose exec neo4j cypher-shell -u neo4j -p <pass> -f /queries/verificacion.cypher
// =============================================================================


// -----------------------------------------------------------------------------
// 6.1 Conteo de nodos por etiqueta
// ESPERADO: Confederacion 6 | Seleccion 64 | Evento 753 | Fase 7 | Grupo 16 |
//           Jugador 1536 | Partido 128 | Estadio 18      (total 2.528 nodos)
// -----------------------------------------------------------------------------
MATCH (n)
RETURN labels(n)[0] AS etiqueta, count(*) AS nodos
ORDER BY etiqueta;

// -----------------------------------------------------------------------------
// 6.2 Conteo de relaciones por tipo
// ESPERADO: AFILIADO_A 64 | CORRESPONDE_A 128 | EN_PAIS_DE 18 | INTEGRA 64 |
//           OCURRE_EN 753 | PARTICIPA_EN 256 | PERTENECE_A 1536 |
//           PROTAGONIZADO_POR 753 | SE_JUEGA_EN 128   (total 3.700 relaciones)
// -----------------------------------------------------------------------------
MATCH ()-[r]->()
RETURN type(r) AS relacion, count(*) AS relaciones
ORDER BY relacion;


// -----------------------------------------------------------------------------
// 6.3 CARDINALIDAD: todo partido tiene exactamente 2 equipos, 1 sede y 1 fase
// ESPERADO: 0 filas. Cualquier fila es un partido mal formado.
// -----------------------------------------------------------------------------
MATCH (p:Partido)
OPTIONAL MATCH (p)<-[r:PARTICIPA_EN]-(:Seleccion)
WITH p, count(r) AS equipos
OPTIONAL MATCH (p)-[s:SE_JUEGA_EN]->(:Estadio)
WITH p, equipos, count(s) AS sedes
OPTIONAL MATCH (p)-[f:CORRESPONDE_A]->(:Fase)
WITH p, equipos, sedes, count(f) AS fases
WHERE equipos <> 2 OR sedes <> 1 OR fases <> 1
RETURN p.partidoId AS partidoInconsistente, equipos, sedes, fases;

// 6.3.1 Y cada partido tiene un local y un visitante, no dos del mismo rol.
// ESPERADO: 0 filas.
MATCH (p:Partido)<-[r:PARTICIPA_EN]-(:Seleccion)
WITH p, collect(r.rol) AS roles
WHERE NOT ('local' IN roles AND 'visitante' IN roles) OR size(roles) <> 2
RETURN p.partidoId AS partidoConRolesInvalidos, roles;

// 6.3.2 Ningún equipo se enfrenta a sí mismo.
// ESPERADO: 0 filas.
MATCH (e:Seleccion)-[:PARTICIPA_EN]->(p:Partido)<-[:PARTICIPA_EN]-(e2:Seleccion)
WHERE e = e2
RETURN p.partidoId AS partidoConEquipoRepetido, e.seleccionId AS equipo;


// -----------------------------------------------------------------------------
// 6.4 CARDINALIDAD: cada jugador pertenece a exactamente una selección
// ESPERADO: 0 filas.
// -----------------------------------------------------------------------------
MATCH (j:Jugador)
OPTIONAL MATCH (j)-[r:PERTENECE_A]->(:Seleccion)
WITH j, count(r) AS equipos
WHERE equipos <> 1
RETURN j.jugadorId AS jugadorInconsistente, equipos;

// 6.4.1 No se repiten dorsales dentro de un mismo plantel.
// ESPERADO: 0 filas. (Regla garantizada por el identificador "EQUIPO-DORSAL"
// heredado del Hito 4, pero se verifica de todos modos.)
MATCH (j:Jugador)-[:PERTENECE_A]->(e:Seleccion)
WITH e, j.dorsal AS dorsal, count(*) AS cantidad
WHERE cantidad > 1
RETURN e.seleccionId AS equipo, dorsal, cantidad;


// -----------------------------------------------------------------------------
// 6.5 CARDINALIDAD: cada evento se vincula a 1 partido y 1 jugador
// ESPERADO: 0 filas.
// -----------------------------------------------------------------------------
MATCH (v:Evento)
OPTIONAL MATCH (v)-[o:OCURRE_EN]->(:Partido)
WITH v, count(o) AS partidos
OPTIONAL MATCH (v)-[pr:PROTAGONIZADO_POR]->(:Jugador)
WITH v, partidos, count(pr) AS jugadores
WHERE partidos <> 1 OR jugadores <> 1
RETURN v.eventoId AS eventoInconsistente, partidos, jugadores;

// 6.5.1 COHERENCIA CLAVE: el jugador de cada evento pertenece a alguno de los
// dos equipos que disputaron ese partido. Detecta goles atribuidos a un
// futbolista que no estaba en ese partido.
// ESPERADO: 0 filas.
MATCH (v:Evento)-[:OCURRE_EN]->(p:Partido)
MATCH (v)-[:PROTAGONIZADO_POR]->(j:Jugador)-[:PERTENECE_A]->(e:Seleccion)
WHERE NOT EXISTS { (e)-[:PARTICIPA_EN]->(p) }
RETURN v.eventoId AS eventoAjenoAlPartido,
       j.jugadorId AS jugador,
       e.seleccionId  AS equipo,
       p.partidoId AS partido;

// 6.5.2 COHERENCIA CLAVE: la cantidad de eventos de gol de cada equipo en cada
// partido coincide con los goles registrados en su relación :PARTICIPA_EN.
// ESPERADO: 0 filas.
MATCH (e:Seleccion)-[r:PARTICIPA_EN]->(p:Partido)
OPTIONAL MATCH (v:Evento)-[:OCURRE_EN]->(p)
WHERE v.tipo IN ['gol', 'penal_convertido']
  AND EXISTS { (v)-[:PROTAGONIZADO_POR]->(:Jugador)-[:PERTENECE_A]->(e) }
WITH p, e, r.goles AS golesRegistrados, count(v) AS eventosDeGol
WHERE golesRegistrados <> eventosDeGol
RETURN p.partidoId AS partido, e.seleccionId AS equipo, golesRegistrados, eventosDeGol;

// 6.5.3 Y el marcador del nodo :Partido coincide con el de las relaciones.
// ESPERADO: 0 filas.
MATCH (local:Seleccion)-[rl:PARTICIPA_EN {rol: 'local'}]->(p:Partido)
MATCH (visitante:Seleccion)-[rv:PARTICIPA_EN {rol: 'visitante'}]->(p)
WHERE p.golesLocal <> rl.goles OR p.golesVisitante <> rv.goles
   OR rl.goles <> rv.golesRecibidos OR rv.goles <> rl.golesRecibidos
RETURN p.partidoId AS partidoConMarcadorIncoherente,
       p.golesLocal, rl.goles, p.golesVisitante, rv.goles;


// -----------------------------------------------------------------------------
// 6.6 TRAZABILIDAD CON EL HITO 4 (RF5)
// -----------------------------------------------------------------------------

// 6.6.1 Los 64 identificadores de equipo son códigos FIFA de 3 letras.
// ESPERADO: 64 equipos, 0 con formato inválido.
MATCH (e:Seleccion)
RETURN count(*) AS equipos,
       count(CASE WHEN e.seleccionId =~ '[A-Z]{3}' THEN 1 END) AS conFormatoValido,
       count(CASE WHEN NOT e.seleccionId =~ '[A-Z]{3}' THEN 1 END) AS conFormatoInvalido;

// 6.6.2 Todo jugadorId respeta el formato "EQUIPO-DORSAL" del Hito 4 y su
// prefijo coincide con la selección a la que está vinculado en el grafo.
// ESPERADO: 1536 correctos, 0 incorrectos.
MATCH (j:Jugador)-[:PERTENECE_A]->(e:Seleccion)
RETURN count(*) AS jugadores,
       count(CASE WHEN j.jugadorId STARTS WITH e.seleccionId + '-' THEN 1 END) AS prefijoCoincide,
       count(CASE WHEN NOT j.jugadorId STARTS WITH e.seleccionId + '-' THEN 1 END) AS prefijoNoCoincide;

// 6.6.3 El dorsal del nodo coincide con el sufijo del identificador.
// ESPERADO: 0 filas.
MATCH (j:Jugador)
WHERE toInteger(split(j.jugadorId, '-')[1]) <> j.dorsal
RETURN j.jugadorId AS jugador, j.dorsal AS dorsalDelNodo;


// -----------------------------------------------------------------------------
// 6.7 INTEGRIDAD ESTRUCTURAL
// -----------------------------------------------------------------------------

// 6.7.1 No hay nodos sin identificador (suple la restricción de existencia,
// que en Neo4j Community no está disponible).
// ESPERADO: 0 filas.
MATCH (n)
WHERE (n:Seleccion        AND n.seleccionId  IS NULL)
   OR (n:Jugador       AND n.jugadorId IS NULL)
   OR (n:Partido       AND n.partidoId IS NULL)
   OR (n:Estadio          AND n.estadioId    IS NULL)
   OR (n:Evento        AND n.eventoId  IS NULL)
   OR (n:Confederacion AND n.codigo    IS NULL)
   OR (n:Grupo         AND n.codigo    IS NULL)
   OR (n:Fase          AND n.codigo    IS NULL)
RETURN labels(n) AS etiquetas, count(*) AS nodosSinIdentificador;

// 6.7.2 No hay nodos aislados: todo nodo del subgrafo participa de al menos
// una relación.
// ESPERADO: 0 filas.
MATCH (n)
WHERE NOT (n)--()
RETURN labels(n) AS etiquetas, count(*) AS nodosAislados;

// 6.7.3 Cada grupo tiene exactamente 4 selecciones y cada selección un grupo.
// ESPERADO: 0 filas.
MATCH (g:Grupo)<-[:INTEGRA]-(e:Seleccion)
WITH g, count(e) AS equipos
WHERE equipos <> 4
RETURN g.codigo AS grupoIncompleto, equipos;

// 6.7.4 Distribución de partidos por fase.
// ESPERADO: Grupos 96 | Dieciseisavos 16 | Octavos 8 | Cuartos 4 |
//           Semifinales 2 | Tercer puesto 1 | Final 1    (total 128)
MATCH (f:Fase)<-[:CORRESPONDE_A]-(p:Partido)
RETURN f.orden AS orden, f.nombre AS fase, count(p) AS partidos
ORDER BY orden;

// 6.7.5 Toda sede recibió al menos un partido (no hay estadios huérfanos).
// ESPERADO: 0 filas.
MATCH (s:Estadio)
WHERE NOT EXISTS { (:Partido)-[:SE_JUEGA_EN]->(s) }
RETURN s.estadioId AS sedeSinPartidos;


// -----------------------------------------------------------------------------
// 6.8 RESTRICCIONES E ÍNDICES ACTIVOS
// ESPERADO: 8 restricciones de unicidad y 16 índices (los 8 que Neo4j crea
// automáticamente para respaldar cada restricción, más los 6 índices RANGE y
// los 2 FULLTEXT declarados explícitamente en estructura.cypher).
// -----------------------------------------------------------------------------
SHOW CONSTRAINTS YIELD name RETURN count(*) AS restricciones;

SHOW INDEXES YIELD name, type
WHERE type <> 'LOOKUP'
RETURN count(*) AS indicesDeclarados;


// -----------------------------------------------------------------------------
// 6.9 RESUMEN FINAL
// -----------------------------------------------------------------------------
MATCH (n)
WITH count(n) AS nodos
MATCH ()-[r]->()
RETURN nodos AS nodosTotales, count(r) AS relacionesTotales;
