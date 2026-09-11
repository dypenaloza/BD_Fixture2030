// Consulta 1:
// Obtener todos los jugadores pertenecientes a una //selección.

MATCH (j:Jugador)-[:PERTENECE_A]->(s:Seleccion)
WHERE s.pais = "Argentina"
RETURN
    j.jugadorId AS id,
    j.nombre AS nombre,
    j.apellido AS apellido,
    j.posicion AS posicion,
    j.dorsal AS dorsal,
    s.pais AS seleccion
ORDER BY j.dorsal;

// Consulta 2:
// Obtener los jugadores de una selección filtrados por //posición.

MATCH (j:Jugador)-[:PERTENECE_A]->(s:Seleccion)
WHERE s.pais = "Argentina"
  AND j.posicion = "Delantero"
RETURN
    j.jugadorId AS id,
    j.nombre AS nombre,
    j.apellido AS apellido,
    j.posicion AS posicion,
    j.dorsal AS dorsal,
    s.pais AS seleccion
ORDER BY j.dorsal;

// Consulta 3:
// Obtener los capitanes y la selección a la que //pertenecen.

MATCH (j:Jugador)-[:PERTENECE_A]->(s:Seleccion)
WHERE j.capitan = true
RETURN
    j.jugadorId AS id,
    j.nombre AS nombre,
    j.apellido AS apellido,
    j.dorsal AS dorsal,
    s.pais AS seleccion
ORDER BY s.pais;

// Consulta 4:
// Contar la cantidad de jugadores pertenecientes a cada //selección.

MATCH (j:Jugador)-[:PERTENECE_A]->(s:Seleccion)
RETURN
    s.pais AS seleccion,
    count(j) AS cantidadJugadores
ORDER BY s.pais;

// Consulta 5:
// Contar jugadores por posición en todo el torneo.

MATCH (j:Jugador)
RETURN
    j.posicion AS posicion,
    count(j) AS cantidadJugadores
ORDER BY cantidadJugadores DESC;

// Consulta 6:
// Contar cuántos jugadores hay por posición dentro de //cada selección.

MATCH (j:Jugador)-[:PERTENECE_A]->(s:Seleccion)
RETURN
    s.pais AS seleccion,
    j.posicion AS posicion,
    count(j) AS cantidadJugadores
ORDER BY s.pais, j.posicion;

// Consulta 7:
// Obtener altura y peso promedio de los jugadores según //su posición.

MATCH (j:Jugador)
RETURN
    j.posicion AS posicion,
    round(avg(j.altura), 2) AS alturaPromedio,
    round(avg(j.peso), 2) AS pesoPromedio,
    count(j) AS cantidadJugadores
ORDER BY posicion;

// Consulta 8:
// Encontrar todos los compañeros de selección de un //jugador determinado.

MATCH (j1:Jugador {jugadorId: "ARG-01"})
      -[:PERTENECE_A]->(s:Seleccion)
      <-[:PERTENECE_A]-(j2:Jugador)

WHERE j1 <> j2

RETURN
    j1.nombre AS jugadorBuscado,
    j1.apellido AS apellidoBuscado,
    s.pais AS seleccion,
    j2.jugadorId AS compañeroId,
    j2.nombre AS compañeroNombre,
    j2.apellido AS compañeroApellido,
    j2.posicion AS posicion
ORDER BY j2.dorsal;

// =============================================================================
// RF8 — Consultas de 2 o más relaciones consecutivas (recorridos multi-salto)
// =============================================================================

// Consulta 9 (3 saltos):
// Jugador -> Seleccion -> Partido -> Estadio.
// Para un jugador puntual, en qué sedes jugó su selección durante el torneo.
// Útil para reconstruir la agenda de viajes/sedes de un jugador o su equipo
// sin tener que cruzar manualmente tres colecciones distintas.

MATCH (j:Jugador {jugadorId: "ARG-01"})-[:PERTENECE_A]->(s:Seleccion)
      -[:PARTICIPA_EN]->(p:Partido)-[:SE_JUEGA_EN]->(e:Estadio)
RETURN
    j.nombre AS jugador,
    j.apellido AS apellido,
    s.pais AS seleccion,
    p.partidoId AS partido,
    p.fecha AS fecha,
    p.fase AS fase,
    e.nombre AS estadio,
    e.ciudad AS ciudad
ORDER BY p.fecha;

// Consulta 10 (2 saltos, convergentes):
// Seleccion -> Partido <- Evento.
// Todos los eventos (goles y tarjetas) ocurridos en los partidos de una
// selección determinada, sin necesidad de conocer de antemano los IDs de
// esos partidos: el patrón conecta la selección con los eventos a través
// del partido que ambos comparten.

MATCH (s:Seleccion {seleccionId: "ARG"})-[:PARTICIPA_EN]->(p:Partido)<-[:OCURRE_EN]-(ev:Evento)
RETURN
    s.pais AS seleccion,
    p.partidoId AS partido,
    p.fase AS fase,
    ev.tipo AS evento,
    ev.minuto AS minuto,
    ev.descripcion AS descripcion
ORDER BY p.fecha, ev.minuto;