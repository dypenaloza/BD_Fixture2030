# Patrones de acceso (RF2, RNF4)

Antes de elegir ninguna clave ni estructura se identificaron los patrones
de acceso reales del módulo. Cada decisión de diseño posterior
(`docs/modelo_clave_valor.md`) se apoya en uno de estos cuatro patrones —
no se incorporó ninguna estructura sin una operación concreta que la
justifique (RNF4).

---

## PA1 — Crear/renovar sesión de usuario

| Aspecto | Detalle |
|---|---|
| Quién solicita/actualiza | La aplicación, en cada request autenticado del usuario. |
| Entrada | `usuario_id`. |
| Salida/respuesta | Confirmación de sesión activa; o redirección a login si no existe. |
| Frecuencia | Muy alta en lectura (se valida en cada request); baja en escritura real (solo al crear o renovar). |
| Temporal vs. fuente de verdad | 100% temporal — la sesión no existe en ningún otro módulo; si se pierde, el usuario simplemente vuelve a iniciar sesión. |
| Estructura elegida | **Hash** (`sesion:{usuarioId}`) + TTL sobre la clave completa. |

## PA2 — Consultar resultado de un partido (lectura de alta frecuencia)

| Aspecto | Detalle |
|---|---|
| Quién solicita | Cualquier usuario viendo la ficha de un partido. |
| Entrada | `partido_id`. |
| Salida/respuesta | Marcador y estado del partido. |
| Frecuencia | Extremadamente alta en lectura (miles de usuarios consultando el mismo partido); baja en escritura (solo cuando cambia el marcador real). |
| Temporal vs. fuente de verdad | La copia en Redis es temporal y descartable; la fuente de verdad es Neo4j (nodo `:Partido`, Hito 5). |
| Estructura elegida | **String** (`cache:partido:{partidoId}`) con el resultado serializado y TTL corto. |

## PA3 — Contar visitas a la ficha de un partido

| Aspecto | Detalle |
|---|---|
| Quién actualiza | La aplicación, una vez por cada vista de la ficha del partido. |
| Entrada | `partido_id`. |
| Salida/respuesta | Contador acumulado (para mostrar "X personas vieron este partido"). |
| Frecuencia | Escritura muy alta y concurrente (una por cada vista); lectura ocasional. |
| Temporal vs. fuente de verdad | Temporal — es una métrica de uso, no un dato de negocio que deba persistir en otro módulo. |
| Estructura elegida | **String** (`contador:partido:{partidoId}:visitas`) con `INCR`/`INCRBY`. |

## PA4 — Votar y consultar la figura del partido

| Aspecto | Detalle |
|---|---|
| Quién actualiza | Cualquier usuario autenticado, un voto por acción. |
| Quién consulta | Cualquier usuario, para ver el ranking actual. |
| Entrada (voto) | `partido_id`, `jugador_id`. |
| Entrada (ranking) | `partido_id`, cantidad de puestos a mostrar (Top-N). |
| Salida/respuesta | Ranking ordenado de jugadores por votos. |
| Frecuencia | Escritura muy alta y concurrente durante el partido; lectura alta y constante (tablero en vivo). |
| Temporal vs. fuente de verdad | El conteo de votos es 100% temporal (vive y muere con el partido); el **nombre** de cada jugador no se duplica acá — se resuelve contra MongoDB (Hito 4) a partir del `jugador_id` cuando la aplicación necesita mostrarlo. |
| Estructura elegida | **Sorted Set** (`encuesta:{partidoId}:figura`) con `ZINCRBY` para votar y `ZREVRANGE ... WITHSCORES` para el ranking. |

---

## Por qué estos cuatro y no otros

Se descartó deliberadamente modelar como caché cualquier dato de equipos o
jugadores (ficha de selección, plantel): esos datos cambian con muy poca
frecuencia (ver Hito 4) y ya se resuelven en un solo acceso por `_id` en
MongoDB — cachearlos no ahorra una consulta costosa, solo agrega una
segunda fuente de verdad a mantener sincronizada sin necesidad real. El
resultado de un partido en cambio es releído por órdenes de magnitud más
usuarios que los que lo escriben, que es exactamente el perfil que
justifica una caché (PA2).
