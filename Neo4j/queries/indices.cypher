// =============================================================================
// ÍNDICES (RF10) — Fixture 2030 / Hito 5
//
// Los identificadores (jugadorId, seleccionId, partidoId, estadioId, eventoId)
// ya están indexados automáticamente por sus restricciones de unicidad en
// constraints.cypher. Este archivo agrega SÓLO los índices que corresponden
// a patrones de acceso reales, usados por queries/consultas.cypher, y que no
// están cubiertos por ninguna restricción:
//
//   - Seleccion.pais    -> varias consultas de recuperación filtran por el
//                          nombre del país (ej. "Argentina") en lugar del
//                          código interno seleccionId ("ARG").
//   - Jugador.posicion  -> filtro frecuente para armar planteles por rol
//                          (arqueros, defensores, mediocampistas, delanteros).
//   - Partido.fecha     -> ordenar/filtrar partidos por fecha es el acceso
//                          típico de una pantalla de calendario/fixture.
//   - Estadio.pais      -> agrupar o filtrar partidos/sedes por país anfitrión.
//
// No se creó un índice sobre Partido.fase ni Evento.tipo: ambas propiedades
// tienen muy baja cardinalidad (5-8 valores distintos sobre cientos de nodos)
// y un escaneo completo de esa etiqueta ya es barato; un índice ahí sólo
// agregaría costo de mantenimiento en cada carga sin acelerar consultas reales.
// =============================================================================

CREATE INDEX seleccion_pais_idx IF NOT EXISTS
FOR (s:Seleccion) ON (s.pais);

CREATE INDEX jugador_posicion_idx IF NOT EXISTS
FOR (j:Jugador) ON (j.posicion);

CREATE INDEX partido_fecha_idx IF NOT EXISTS
FOR (p:Partido) ON (p.fecha);

CREATE INDEX estadio_pais_idx IF NOT EXISTS
FOR (e:Estadio) ON (e.pais);

// Verificación: listar restricciones e índices vigentes (evidencia RF10/RF11).
SHOW CONSTRAINTS;
SHOW INDEXES;
