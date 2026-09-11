// Restricción para Jugador
//ID único
CREATE CONSTRAINT jugador_id_unique IF NOT EXISTS
FOR (j:Jugador)
REQUIRE j.jugadorId IS UNIQUE;

// Restricción para Seleccion
//ID único
CREATE CONSTRAINT seleccion_id_unique IF NOT EXISTS
FOR (s:Seleccion)
REQUIRE s.seleccionId IS UNIQUE;

//Restricción ID de partido único
CREATE CONSTRAINT partido_id_unique IF NOT EXISTS
FOR (p:Partido)
REQUIRE p.partidoId IS UNIQUE;

//Res. ID estadio único
CREATE CONSTRAINT estadio_id_unique IF NOT EXISTS
FOR (e:Estadio)
REQUIRE e.estadioId IS UNIQUE;


//Res. id único evento
CREATE CONSTRAINT evento_id_unique IF NOT EXISTS
FOR (e:Evento)
REQUIRE e.eventoId IS UNIQUE;