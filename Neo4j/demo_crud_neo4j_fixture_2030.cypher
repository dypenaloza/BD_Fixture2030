// =============================================================================
// DEMO EN VIVO — NEO4J Y CRUD DE GRAFOS
// Fixture del Mundial 2030 | Base de práctica: neo4j
//
// Uso recomendado: ejecutar cada bloque por separado desde Neo4j Browser.
// Los nodos de demostración tienen la etiqueta :Demo para aislarlos del Hito.
// =============================================================================

// -----------------------------------------------------------------------------
// 0. LIMPIEZA CONTROLADA
// Borra únicamente los nodos utilizados por esta demostración y sus relaciones.
// -----------------------------------------------------------------------------
MATCH (n:Demo)
DETACH DELETE n;

// -----------------------------------------------------------------------------
// 1. CREATE — CREAR NODOS Y RELACIONES
// -----------------------------------------------------------------------------
CREATE
  (arg:Demo:DemoEquipo:Equipo {
    codigo: 'ARG', nombre: 'Argentina', confederacion: 'CONMEBOL', ranking: 1
  }),
  (esp:Demo:DemoEquipo:Equipo {
    codigo: 'ESP', nombre: 'España', confederacion: 'UEFA', ranking: 3
  }),
  (por:Demo:DemoEquipo:Equipo {
    codigo: 'POR', nombre: 'Portugal', confederacion: 'UEFA', ranking: 7
  }),
  (mes:Demo:DemoJugador:Jugador {
    id: 'demo-10', nombre: 'Lionel Messi', posicion: 'Delantero', goles: 0
  }),
  (mol:Demo:DemoJugador:Jugador {
    id: 'demo-11', nombre: 'Lautaro Martínez', posicion: 'Delantero', goles: 0
  }),
  (ped:Demo:DemoJugador:Jugador {
    id: 'demo-7', nombre: 'Pedri', posicion: 'Mediocampista', goles: 0
  }),
  (ron:Demo:DemoJugador:Jugador {
    id: 'demo-8', nombre: 'Bruno Fernandes', posicion: 'Mediocampista', goles: 0
  }),
  (m1:Demo:DemoPartido:Partido {
    id: 'demo-p001', fecha: date('2030-06-14'), sede: 'Montevideo', estado: 'programado'
  }),
  (arg)-[:REPRESENTA]->(mes),
  (arg)-[:REPRESENTA]->(mol),
  (esp)-[:REPRESENTA]->(ped),
  (por)-[:REPRESENTA]->(ron),
  (arg)-[:DISPUTA {rol: 'local'}]->(m1),
  (esp)-[:DISPUTA {rol: 'visitante'}]->(m1);

// Visualizar el subgrafo completo creado.
MATCH p = (n:Demo)-[r]->(m:Demo)
RETURN p;

// -----------------------------------------------------------------------------
// 2. READ — CONSULTAR NODOS, RELACIONES Y PATRONES
// -----------------------------------------------------------------------------
// 2.1 Recuperar equipos ordenados por ranking.
MATCH (e:DemoEquipo)
RETURN e.codigo, e.nombre, e.confederacion, e.ranking
ORDER BY e.ranking ASC;

// 2.2 Recuperar los jugadores que representa Argentina.
MATCH (e:DemoEquipo {codigo: 'ARG'})-[:REPRESENTA]->(j:DemoJugador)
RETURN e.nombre AS equipo, j.nombre AS jugador, j.posicion AS posicion;

// 2.3 Recuperar el partido y los equipos participantes con sus roles.
MATCH (e:DemoEquipo)-[d:DISPUTA]->(p:DemoPartido {id: 'demo-p001'})
RETURN p.id AS partido, p.sede AS sede, e.nombre AS equipo, d.rol AS rol
ORDER BY d.rol;

// 2.4 Explorar el grafo desde un jugador con una relación de profundidad 1..2.
MATCH camino = (j:DemoJugador {id: 'demo-10'})-[*1..2]-(destino:Demo)
RETURN camino;

// -----------------------------------------------------------------------------
// 3. UPDATE — MODIFICAR PROPIEDADES Y RELACIONES
// -----------------------------------------------------------------------------
// 3.1 Actualizar una propiedad existente y añadir una nueva.
MATCH (p:DemoPartido {id: 'demo-p001'})
SET p.estado = 'en_juego',
    p.minuto = 63
RETURN p;

// 3.2 Registrar un evento como relación con propiedades.
MATCH (j:DemoJugador {id: 'demo-10'}),
      (p:DemoPartido {id: 'demo-p001'})
MERGE (j)-[a:ANOTA_EN]->(p)
SET a.minuto = 63,
    a.tipo = 'gol',
    j.goles = coalesce(j.goles, 0) + 1
RETURN j, a, p;

// 3.3 Comprobar el cambio en forma de grafo.
MATCH camino = (j:DemoJugador {id: 'demo-10'})-[r]->(p:DemoPartido {id: 'demo-p001'})
RETURN camino;

// -----------------------------------------------------------------------------
// 4. DELETE — ELIMINAR UNA RELACIÓN Y UN NODO TEMPORAL
// -----------------------------------------------------------------------------
// 4.1 Eliminar solo una relación: el nodo jugador y el partido se conservan.
MATCH (:DemoJugador {id: 'demo-10'})-[a:ANOTA_EN]->(:DemoPartido {id: 'demo-p001'})
DELETE a;

// 4.2 Crear un jugador temporal para demostrar DETACH DELETE con seguridad.
CREATE (:Demo:DemoJugador:Jugador {
  id: 'demo-temp', nombre: 'Jugador temporal', posicion: 'Arquero', goles: 0
});

MATCH (j:DemoJugador {id: 'demo-temp'})
DETACH DELETE j;

// -----------------------------------------------------------------------------
// 5. VERIFICACIÓN FINAL
// -----------------------------------------------------------------------------
MATCH (n:Demo)
RETURN labels(n) AS etiquetas, count(*) AS cantidad
ORDER BY etiquetas;

// OPCIONAL: limpiar completamente el subgrafo de demostración al terminar.
// MATCH (n:Demo) DETACH DELETE n;
