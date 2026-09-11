// =============================================================================
// CRUD (RF7) — Fixture 2030 / Hito 5
//
// Cubre alta, lectura, actualización y baja de nodos y relaciones sobre el
// modelo real (:Jugador, :Seleccion, :Partido, :Evento), no sobre un modelo
// paralelo de práctica. Para poder demostrar el ciclo completo sin arriesgar
// los datos de carga (RNF4), las operaciones de creación/baja usan un
// jugador y un evento claramente identificables como de prueba
// (jugadorId "TEST-01", eventoId "EV-TEST-01"), que el bloque 4 elimina de
// forma precisa al terminar. Ningún DELETE de este archivo usa un patrón sin
// filtrar: cada uno referencia el identificador exacto de la entidad de
// prueba, tal como recomienda el enunciado del hito.
//
// Ejecutar en orden: 1 (create) -> 2 (read) -> 3 (update) -> 4 (delete).
// =============================================================================

// -----------------------------------------------------------------------------
// 1. CREATE
// -----------------------------------------------------------------------------

// 1.1 Alta de un jugador y su relación de pertenencia a una selección real.
MERGE (j:Jugador {jugadorId: 'TEST-01'})
SET j.nombre = 'Jugador', j.apellido = 'De Prueba', j.posicion = 'Mediocampista',
    j.dorsal = 99, j.altura = 180, j.peso = 75.0, j.club = 'Club de Prueba', j.capitan = false
WITH j
MATCH (s:Seleccion {seleccionId: 'ARG'})
MERGE (j)-[:PERTENECE_A]->(s);

// 1.2 Alta de un evento de prueba, vinculado a un partido y a un jugador reales.
MATCH (p:Partido {partidoId: 'P-A-1'})
MATCH (j:Jugador {jugadorId: 'TEST-01'})
MERGE (ev:Evento {eventoId: 'EV-TEST-01'})
SET ev.tipo = 'Gol', ev.minuto = 45, ev.descripcion = 'Evento de prueba para CRUD'
MERGE (ev)-[:OCURRE_EN]->(p)
MERGE (ev)-[:PROTAGONIZADO_POR]->(j);

// -----------------------------------------------------------------------------
// 2. READ
// -----------------------------------------------------------------------------

// 2.1 Recuperar el jugador de prueba y la selección a la que pertenece.
MATCH (j:Jugador {jugadorId: 'TEST-01'})-[:PERTENECE_A]->(s:Seleccion)
RETURN j.jugadorId, j.nombre, j.apellido, j.posicion, s.pais;

// 2.2 Recuperar el evento de prueba con el partido y el jugador relacionados.
MATCH (ev:Evento {eventoId: 'EV-TEST-01'})-[:OCURRE_EN]->(p:Partido),
      (ev)-[:PROTAGONIZADO_POR]->(j:Jugador)
RETURN ev.eventoId, ev.tipo, ev.minuto, p.partidoId, j.jugadorId;

// -----------------------------------------------------------------------------
// 3. UPDATE
// -----------------------------------------------------------------------------

// 3.1 Actualizar propiedades del jugador de prueba (cambia de posición y dorsal).
MATCH (j:Jugador {jugadorId: 'TEST-01'})
SET j.posicion = 'Defensor', j.dorsal = 88
RETURN j.jugadorId, j.posicion, j.dorsal;

// 3.2 Actualizar el minuto y la descripción del evento de prueba.
MATCH (ev:Evento {eventoId: 'EV-TEST-01'})
SET ev.minuto = 67, ev.descripcion = 'Evento de prueba actualizado'
RETURN ev.eventoId, ev.minuto, ev.descripcion;

// -----------------------------------------------------------------------------
// 4. DELETE
// -----------------------------------------------------------------------------

// 4.1 Baja acotada de una sola relación: el evento y el jugador se conservan
// (demuestra que se puede borrar sólo el vínculo, no las entidades).
MATCH (ev:Evento {eventoId: 'EV-TEST-01'})-[r:PROTAGONIZADO_POR]->(:Jugador {jugadorId: 'TEST-01'})
DELETE r;

// 4.2 Baja completa y acotada del evento de prueba (nodo + relaciones restantes).
MATCH (ev:Evento {eventoId: 'EV-TEST-01'})
DETACH DELETE ev;

// 4.3 Baja completa y acotada del jugador de prueba (nodo + relación PERTENECE_A).
MATCH (j:Jugador {jugadorId: 'TEST-01'})
DETACH DELETE j;

// -----------------------------------------------------------------------------
// 5. VERIFICACIÓN — no debe quedar ningún rastro de las entidades de prueba.
// -----------------------------------------------------------------------------
MATCH (n)
WHERE n.jugadorId = 'TEST-01' OR n.eventoId = 'EV-TEST-01'
RETURN count(n) AS entidadesDePruebaRestantes;
