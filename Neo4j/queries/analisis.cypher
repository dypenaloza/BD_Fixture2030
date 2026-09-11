// =============================================================================
// ANÁLISIS RELACIONAL (RF9) — Fixture 2030 / Hito 5
//
// Objetivo: mostrar información que sólo emerge de recorrer el grafo, no de
// consultar una colección aislada. Se incluyen dos análisis:
//
//   1) Camino más corto entre dos selecciones que no se enfrentaron de forma
//      directa, atravesando los partidos y sedes que sí comparten con otras
//      selecciones (shortestPath).
//   2) Centralidad de grado de los estadios: cuántos partidos alojó cada uno,
//      como indicador de qué sedes concentran más operación logística.
//
// Ambos usan funciones estándar de Cypher (no requieren GDS), disponibles en
// cualquier instalación de neo4j:latest.
// =============================================================================

// -----------------------------------------------------------------------------
// 1. CAMINO MÁS CORTO ENTRE DOS SELECCIONES (conectividad)
// -----------------------------------------------------------------------------
// Argentina (grupo A) y Japón (grupo E) no compartieron grupo ni, según el
// sorteo generado, se cruzaron en la misma llave de eliminatorias. shortestPath
// recorre PARTICIPA_EN y SE_JUEGA_EN como un grafo no dirigido para encontrar
// la cadena más corta de partidos/sedes que las conecta indirectamente.
//
// Qué aporta al Fixture 2030: permite responder "¿qué tan lejos está una
// selección de otra dentro del torneo?" sin tener que armar el camino a mano
// cruzando tablas de partidos y sedes. Es la base para funciones como
// "equipos relacionados" o "seis grados de separación del Mundial" en la
// plataforma, y para detectar qué tan conectado (o disperso) quedó el fixture
// generado.

MATCH (a:Seleccion {seleccionId: "ARG"}), (b:Seleccion {seleccionId: "JPN"})
MATCH camino = shortestPath((a)-[:PARTICIPA_EN|SE_JUEGA_EN*..12]-(b))
RETURN
    [n IN nodes(camino) | coalesce(n.pais, n.partidoId, n.nombre)] AS recorrido,
    length(camino) AS saltos;

// -----------------------------------------------------------------------------
// 2. CENTRALIDAD DE GRADO DE LOS ESTADIOS
// -----------------------------------------------------------------------------
// Cuenta cuántos partidos se jugaron en cada estadio (grado de entrada de la
// relación SE_JUEGA_EN): una forma simple de centralidad de grado.
//
// Qué aporta al Fixture 2030: identifica qué sedes concentran más partidos
// y por lo tanto más demanda operativa (seguridad, logística, transporte),
// información que no surge de mirar un partido a la vez sino de agregar sobre
// todo el subgrafo Partido-Estadio.

MATCH (e:Estadio)<-[:SE_JUEGA_EN]-(p:Partido)
RETURN
    e.nombre AS estadio,
    e.ciudad AS ciudad,
    e.pais AS pais,
    count(p) AS cantidadPartidos
ORDER BY cantidadPartidos DESC, estadio;

// -----------------------------------------------------------------------------
// 3. (COMPLEMENTARIA) CENTRALIDAD DE GRADO DE JUGADORES POR PROTAGONISMO
// -----------------------------------------------------------------------------
// Cuenta cuántos eventos (goles + tarjetas) protagonizó cada jugador: otra
// lectura de centralidad de grado, esta vez sobre PROTAGONIZADO_POR, útil
// para tableros de "figuras del torneo".

MATCH (j:Jugador)<-[:PROTAGONIZADO_POR]-(ev:Evento)
RETURN
    j.jugadorId AS jugador,
    j.nombre AS nombre,
    j.apellido AS apellido,
    count(ev) AS cantidadEventos
ORDER BY cantidadEventos DESC
LIMIT 10;
