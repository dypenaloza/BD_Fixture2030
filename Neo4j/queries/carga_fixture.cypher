// ========================================
// PARTIDOS
// ========================================

MERGE (p:Partido {partidoId: "P001"})
SET p.fecha = datetime("2030-06-08T20:00:00"),
    p.fase = "Fase de grupos",
    p.estado = "Programado",
    p.arbitros = ["Arbitro principal", "Asistente 1", "Asistente 2"];


// ========================================
// ESTADIOS
// ========================================

MERGE (e:Estadio {estadioId: "E001"})
SET e.nombre = "Estadio Monumental",
    e.ciudad = "Buenos Aires",
    e.pais = "Argentina",
    e.capacidad = 84567;


// ========================================
// PARTICIPACIÓN DE SELECCIONES EN PARTIDOS
// ========================================

MATCH (arg:Seleccion {seleccionId: "ARG"})
MATCH (bra:Seleccion {seleccionId: "BRA"})
MATCH (p:Partido {partidoId: "P001"})

MERGE (arg)-[:PARTICIPA_EN {rol: "Local"}]->(p)
MERGE (bra)-[:PARTICIPA_EN {rol: "Visitante"}]->(p);


// ========================================
// EVENTOS
// ========================================

MERGE (e:Evento {eventoId: "EV001"})
SET e.tipo = "Gol",
    e.minuto = 23,
    e.descripcion = "Gol de prueba";