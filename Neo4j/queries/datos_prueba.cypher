MERGE (s:Seleccion {seleccionId: "ARG"})
SET s.pais = "Argentina",
    s.nombre = "Argentina",
    s.entrenador = "Lionel Scaloni",
    s.ranking = 1;
//Merge se usa para no crearlos dos veces
MERGE (j:Jugador {jugadorId: "J001"})
SET j.nombre = "Lionel",
    j.apellido = "Messi",
    j.posicion = "Delantero",
    j.altura = 170,
    j.peso = 72.0;

MATCH (j:Jugador {jugadorId: "J001"})
MATCH (s:Seleccion {seleccionId: "ARG"})
MERGE (j)-[:PERTENECE_A]->(s);