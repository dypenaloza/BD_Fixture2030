// =============================================================================
// Hito 5 — Fixture 2030 | 3. CRUD sobre el modelo del subgrafo
//
// Propósito (RF7): crear, recuperar, actualizar y eliminar nodos y relaciones
// del modelo desarrollado.
//
// SEGURIDAD DEL BORRADO (nota 3 del enunciado)
// --------------------------------------------
// Este archivo NO opera sobre los 128 partidos del torneo. Todo lo que crea
// lleva la etiqueta adicional :Prueba y la propiedad origen = 'crud_demo', y
// toda sentencia de eliminación filtra por esa etiqueta. Así, ejecutar este
// archivo deja el subgrafo del Fixture exactamente como estaba: las últimas
// consultas lo verifican comparando los conteos con los de la carga.
//
// Caso de negocio: se programa un amistoso preparatorio entre dos selecciones
// ya cargadas (URU y ARG), se registra su desarrollo y finalmente se anula.
//
// Ejecución:
//   docker compose exec neo4j cypher-shell -u neo4j -p <pass> -f /queries/crud.cypher
// =============================================================================


// -----------------------------------------------------------------------------
// 3.0 Punto de partida: conteos previos
// -----------------------------------------------------------------------------
MATCH (n)
RETURN 'ANTES DEL CRUD' AS momento, count(n) AS nodosTotales;


// =============================================================================
// 3.1 CREATE — alta de nodos y relaciones
// =============================================================================

// 3.1.1 Nueva sede de prueba.
// Se usa MERGE en lugar de CREATE para que el archivo pueda reejecutarse:
// si la sede ya existe, la encuentra en vez de fallar por la restricción de
// unicidad sobre estadioId.
MERGE (s:Estadio:Prueba {estadioId: 'TST-AMI'})
SET s.nombre    = 'Estadio de pruebas Fixture 2030',
    s.ciudad    = 'Montevideo',
    s.capacidad = 25000,
    s.origen    = 'crud_demo'
RETURN s AS sedeCreada;

// 3.1.2 Nuevo partido amistoso, vinculado a la sede y a una fase de prueba.
MERGE (f:Fase:Prueba {codigo: 'AMISTOSO'})
SET f.nombre = 'Amistoso preparatorio',
    f.orden  = 0,
    f.origen = 'crud_demo'
MERGE (p:Partido:Prueba {partidoId: 'F2030-AMI-01'})
SET p.fecha          = date('2030-06-05'),
    p.hora           = '19:00',
    p.estado         = 'programado',
    p.golesLocal     = 0,
    p.golesVisitante = 0,
    p.definidoPor    = 'tiempo_reglamentario',
    p.origen         = 'crud_demo'
WITH p, f
MATCH (s:Estadio {estadioId: 'TST-AMI'})
MERGE (p)-[:SE_JUEGA_EN]->(s)
MERGE (p)-[:CORRESPONDE_A]->(f)
RETURN p.partidoId AS partido, p.estado AS estado, s.nombre AS sede;

// 3.1.3 Relaciones de participación con DOS SELECCIONES REALES ya cargadas.
// Demuestra que un nodo nuevo se integra al subgrafo existente sin duplicar
// los equipos: se los localiza por el identificador del Hito 4.
MATCH (local:Seleccion     {seleccionId: 'URU'}),
      (visitante:Seleccion {seleccionId: 'ARG'}),
      (p:Partido        {partidoId: 'F2030-AMI-01'})
MERGE (local)-[rl:PARTICIPA_EN]->(p)
SET rl.rol = 'local', rl.goles = 0, rl.golesRecibidos = 0, rl.resultado = 'pendiente'
MERGE (visitante)-[rv:PARTICIPA_EN]->(p)
SET rv.rol = 'visitante', rv.goles = 0, rv.golesRecibidos = 0, rv.resultado = 'pendiente'
RETURN local.pais AS local, visitante.pais AS visitante, p.partidoId AS partido;


// =============================================================================
// 3.2 READ — recuperación por patrón
// =============================================================================

// 3.2.1 Ficha del amistoso: recorre partido -> sede y equipos -> partido.
MATCH (e:Seleccion)-[r:PARTICIPA_EN]->(p:Partido {partidoId: 'F2030-AMI-01'})-[:SE_JUEGA_EN]->(s:Estadio)
RETURN p.partidoId AS partido,
       p.fecha     AS fecha,
       r.rol       AS rol,
       e.pais      AS seleccion,
       s.nombre    AS sede,
       p.estado    AS estado
ORDER BY rol;

// 3.2.2 Vecindario del amistoso a dos saltos. Pensada para la vista de grafo
// de Neo4j Browser: ahí se ve el partido nuevo enganchado a las selecciones
// reales. En cypher-shell devuelve texto, por eso el LIMIT es bajo.
MATCH camino = (:Partido:Prueba {partidoId: 'F2030-AMI-01'})-[*1..2]-()
RETURN camino
LIMIT 10;


// =============================================================================
// 3.3 UPDATE — modificación de propiedades, etiquetas y relaciones
// =============================================================================

// 3.3.1 El partido comienza: se actualiza una propiedad existente y se agrega
// una nueva (el modelo de grafos no exige un esquema previo para hacerlo).
MATCH (p:Partido {partidoId: 'F2030-AMI-01'})
SET p.estado = 'en_juego',
    p.minuto = 37
RETURN p.partidoId AS partido, p.estado AS estado, p.minuto AS minuto;

// 3.3.2 Gol de Uruguay: se crea el evento y se actualizan, en la misma
// transacción, las propiedades de la RELACIÓN de participación de ambos
// equipos. Esto muestra por qué goles y golesRecibidos viven en la relación:
// son el resultado de ese equipo en ese partido.
MATCH (j:Jugador)-[:PERTENECE_A]->(:Seleccion {seleccionId: 'URU'})
WHERE j.posicion = 'Delantero'
WITH j ORDER BY j.jugadorId LIMIT 1
MATCH (p:Partido {partidoId: 'F2030-AMI-01'})
MERGE (v:Evento:Prueba {eventoId: 'EV-F2030-AMI-01-01'})
SET v.tipo    = 'gol',
    v.minuto  = 37,
    v.detalle = 'Gol en jugada (amistoso de prueba)',
    v.origen  = 'crud_demo'
MERGE (v)-[:OCURRE_EN]->(p)
MERGE (v)-[:PROTAGONIZADO_POR]->(j)
WITH p, j
MATCH (:Seleccion {seleccionId: 'URU'})-[rl:PARTICIPA_EN]->(p)
MATCH (:Seleccion {seleccionId: 'ARG'})-[rv:PARTICIPA_EN]->(p)
SET rl.goles = rl.goles + 1, rv.golesRecibidos = rv.golesRecibidos + 1
SET p.golesLocal = p.golesLocal + 1
RETURN j.nombreCompleto AS goleador,
       p.golesLocal     AS golesLocal,
       p.golesVisitante AS golesVisitante;

// 3.3.3 Fin del partido: se cierra el estado y se resuelven los resultados.
MATCH (p:Partido {partidoId: 'F2030-AMI-01'})
SET p.estado = 'finalizado'
REMOVE p.minuto
WITH p
MATCH (e:Seleccion)-[r:PARTICIPA_EN]->(p)
SET r.resultado = CASE
                    WHEN r.goles > r.golesRecibidos THEN 'victoria'
                    WHEN r.goles < r.golesRecibidos THEN 'derrota'
                    ELSE 'empate'
                  END
RETURN e.pais AS seleccion, r.goles AS goles, r.resultado AS resultado
ORDER BY seleccion;

// 3.3.4 Agregado de una ETIQUETA a un nodo existente (no requiere migración).
MATCH (s:Estadio {estadioId: 'TST-AMI'})
SET s:SedeAuxiliar
RETURN s.estadioId AS sede, labels(s) AS etiquetas;


// =============================================================================
// 3.4 DELETE — eliminación precisa
//
// Cada sentencia acota el patrón con la etiqueta :Prueba o con un
// identificador explícito. NUNCA se usa "MATCH (n) DETACH DELETE n".
// =============================================================================

// 3.4.1 Eliminar UNA relación puntual: se desprograma la sede del amistoso.
// Los dos nodos siguen existiendo; sólo desaparece el vínculo.
MATCH (p:Partido {partidoId: 'F2030-AMI-01'})-[r:SE_JUEGA_EN]->(s:Estadio {estadioId: 'TST-AMI'})
DELETE r
RETURN 'Relacion SE_JUEGA_EN eliminada' AS resultado,
       p.partidoId AS partido, s.estadioId AS sede;

// 3.4.2 Quitar una etiqueta agregada.
MATCH (s:Estadio {estadioId: 'TST-AMI'})
REMOVE s:SedeAuxiliar
RETURN s.estadioId AS sede, labels(s) AS etiquetas;

// 3.4.3 Eliminar el evento de prueba junto con sus dos relaciones.
MATCH (v:Evento:Prueba {eventoId: 'EV-F2030-AMI-01-01'})
DETACH DELETE v;

// 3.4.4 Eliminar TODO lo creado por este archivo, y sólo eso.
// El filtro por la etiqueta :Prueba garantiza que ningún nodo del torneo
// entre en el patrón: se comprueba contando antes de borrar.
MATCH (n:Prueba)
RETURN 'A eliminar' AS accion, labels(n) AS etiquetas, count(*) AS cantidad
ORDER BY etiquetas;

MATCH (n:Prueba)
DETACH DELETE n;


// =============================================================================
// 3.5 VERIFICACIÓN: el subgrafo del Fixture quedó intacto
// =============================================================================

// 3.5.1 No debe quedar ningún nodo de prueba.
MATCH (n:Prueba)
RETURN count(n) AS nodosDePruebaRestantes;

// 3.5.2 Los conteos deben coincidir con los de la carga original
// (Seleccion 64, Jugador 1536, Partido 128, Estadio 18, Evento 753,
//  Confederacion 6, Grupo 16, Fase 7).
MATCH (n)
RETURN labels(n)[0] AS etiqueta, count(*) AS nodos
ORDER BY etiqueta;

// 3.5.3 Y ninguna selección real debe haber quedado con relaciones sobrantes.
MATCH (e:Seleccion)-[r:PARTICIPA_EN]->()
RETURN count(r) AS participacionesTotales;  // esperado: 256
