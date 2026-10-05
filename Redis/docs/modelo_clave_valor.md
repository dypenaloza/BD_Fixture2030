# Modelo clave-valor (RF2, RNF5)

Namespace de claves usado por el módulo. Todas siguen la convención
`dominio:identificador[:subdominio]`, separadas por `:` (es una convención
de lectura humana — Redis no crea jerarquías reales de carpetas con eso).

| Prefijo de clave | Estructura | TTL | Campos / contenido | Patrón de acceso |
|---|---|---|---|---|
| `sesion:{usuarioId}` | Hash | 1800s (30 min), renovado en cada actividad | `usuario_id`, `nombre`, `rol`, `ultimo_acceso`, `partido_siguiendo` | PA1 |
| `cache:partido:{partidoId}` | String (JSON serializado) | 45s | `golesLocal`, `golesVisitante`, `estado` | PA2 |
| `contador:partido:{partidoId}:visitas` | String (entero) | sin TTL — se reinicia por torneo, no por tiempo | contador | PA3 |
| `encuesta:{partidoId}:figura` | Sorted Set | sin TTL — vive mientras dure el análisis del partido | miembro = `jugador_id` (formato `EQUIPO-DORSAL` del Hito 4), score = votos | PA4 |

## Por qué cada tipo de estructura

- **Hash para la sesión** (y no varios `String` sueltos, uno por campo):
  la sesión se lee y se borra como una unidad. Separarla en
  `sesion:{id}:usuario`, `sesion:{id}:rol`, etc. multiplicaría por 5 la
  cantidad de claves y de operaciones de expiración a coordinar, sin
  ninguna ventaja: nunca se necesita leer *un* campo de la sesión sin los
  demás.

- **String simple para la caché del partido** (y no un Hash con un campo
  por estadística): el consumidor siempre pide el resultado completo de
  un partido de una vez (PA2), nunca "solo los goles sin el estado". Un
  único `GET`/`SET` es más simple y no hay ningún caso de uso que
  necesite leer un campo aislado.

- **String con `INCR` para el contador de visitas**: es el caso de uso
  textual de `INCR` — un entero que solo crece, con actualización atómica
  nativa. No hace falta nada más expresivo.

- **Sorted Set para la encuesta de figura** (y no un Hash
  `jugador_id -> votos` con `HINCRBY`): un Hash puede incrementar un
  campo atómicamente, pero **no mantiene el orden** — para armar el
  ranking (PA4, RF9) habría que traer todos los pares al cliente y
  ordenarlos ahí. Un Sorted Set mantiene el orden por `score` en el
  servidor: `ZREVRANGE ... WITHSCORES` devuelve el Top-N ya ordenado, sin
  traer ni procesar en el cliente los jugadores que no entran en el
  ranking.

## Por qué NO hay más estructuras que estas cuatro

Se evaluó agregar un `Set` (`conectados:partido:{id}`) para "usuarios
viendo el partido en vivo" — es un caso de uso real mencionado en la
Clase 8 — pero se descartó para este entregable: no hay ningún patrón de
acceso (sección anterior) que lo necesite todavía, y agregarlo solo para
"mostrar más estructuras" violaría RNF4 (toda estructura debe responder a
un patrón de acceso concreto, no a la posibilidad de agregarla). Queda
anotado como extensión futura si surge el patrón de acceso que lo
justifique.

## Identificadores: coherencia con hitos anteriores (RF5, RNF6)

- `jugador_id` en `encuesta:*:figura` usa el mismo formato
  `EQUIPO-DORSAL` que `jugadores._id` en MongoDB (Hito 4, ej. `ARG-10`).
- `partido_id` en `cache:partido:*`, `contador:partido:*:visitas` y
  `encuesta:*:figura` usa el mismo formato que `Partido.partidoId` en
  Neo4j (Hito 5, ej. `P-A-1`, `P-R16-3`).
- `usuario_id` en `sesion:*` usa el mismo formato `U#####` que
  `usuario_id` en Cassandra (Hito 6, `comentarios_por_usuario`).

Ningún identificador se inventó desde cero para este hito: todos
reutilizan el espacio de IDs ya definido en un módulo anterior, para que
una aplicación real pueda cruzar un dato de Redis con su fuente de verdad
sin una tabla de traducción intermedia.
