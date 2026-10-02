# Ciclo de vida y caché/invalidación (RF3, RF4, RF6, RF7)

## 1. Ciclo de vida de una sesión

```
   usuario hace login
          │
          ▼
    HSET sesion:{id} ...
    EXPIRE sesion:{id} 1800   ───► CREAR (RF3)
          │
          ▼
  cada request autenticado ──► HSET ultimo_acceso + EXPIRE 1800  (RENOVAR)
          │
          ├── el usuario hace logout ──► DEL sesion:{id}   (CIERRE EXPLÍCITO)
          │
          └── pasan 1800s sin actividad ──► Redis la borra sola  (EXPIRACIÓN)
```

- **Regla de validez:** una sesión es válida si y solo si la clave
  `sesion:{usuarioId}` existe. No hay un campo "activo: true/false" que
  revisar — la propia existencia de la clave *es* el estado.
- **Evento que renueva:** cualquier request autenticado del usuario.
  Importante (y fácil de pasar por alto): modificar un campo del Hash con
  `HSET` **no** renueva el TTL por sí solo — hay que llamar `EXPIRE`
  explícitamente después, en la misma operación lógica. Esto está
  documentado también en la Clase 8 y se verifica en
  `scripts/sesiones.redis` (paso 3).
- **Duración elegida — 30 minutos:** es la misma duración usada como
  ejemplo en la Clase 8 (`EXPIRE sesion:U019 1800`). Se adopta ese valor
  porque es razonable para una sesión de "fan navegando la plataforma
  durante un partido" (un partido dura ~105-120 minutos con
  interrupciones; 30 minutos de inactividad sin ninguna acción es
  suficiente para considerar que el usuario se fue) y porque mantiene
  consistencia con el material de la materia en lugar de inventar un
  número sin referencia.
- **Comprobación de vencimiento:** `TTL sesion:{id}` (segundos restantes,
  `-1` sin expiración, `-2` no existe) o simplemente `EXISTS`/`HGETALL`
  antes de usarla.
- **Ante una sesión inexistente:** la aplicación debe tratar un
  `HGETALL` vacío como "no autenticado" y redirigir a login — nunca
  como una sesión válida con campos vacíos. Ver `scripts/sesiones.redis`,
  sección 6.
- **Mecanismo nativo, no manual (obligatorio según el enunciado):** se
  usa `EXPIRE` sobre la clave completa; no existe ningún proceso que
  recorra periódicamente las sesiones para decidir cuáles borrar — Redis
  lo hace solo, de forma pasiva (al acceder a una clave vencida) y activa
  (muestreo periódico interno).

## 2. Caché del resultado de un partido (Cache-Aside)

```
   usuario pide la ficha del partido
          │
          ▼
   GET cache:partido:{id}
          │
   ┌──────┴──────┐
   │             │
 HIT           MISS
   │             │
   │             ▼
   │      consultar Neo4j (fuente de verdad)
   │             │
   │             ▼
   │      SET cache:partido:{id} ... EX 45
   │             │
   └─────┬───────┘
         ▼
  responder al usuario
```

- **Fuente de verdad:** Neo4j, nodo `:Partido` (`golesLocal`,
  `golesVisitante`, `estado` — Hito 5). Redis nunca es la única copia del
  resultado de un partido.
- **Condición de cache hit:** `GET cache:partido:{id}` devuelve un valor
  no nulo.
- **Camino ante cache miss:** la aplicación consulta Neo4j, construye la
  respuesta y la guarda en Redis con `SET ... EX 45` antes de responder.
  Si Neo4j tampoco tuviera el dato (partido inexistente), el error se
  propaga igual que si no existiera la caché — Redis nunca inventa un
  resultado.
- **Por qué el TTL es corto (45s) y no largo:** es la pieza central de
  este patrón y la que el enunciado pide no dejar sin resolver. El
  resultado de un partido **en curso** cambia en cualquier momento (un
  gol). Un TTL de 45 segundos acota el peor caso de "ver un marcador
  viejo" a menos de un minuto incluso si, por algún motivo, la
  invalidación explícita (siguiente punto) no llegara a ejecutarse. Para
  un partido ya `finalizado` el dato no vuelve a cambiar, así que el
  mismo TTL corto solo implica que se va a recalcular unas pocas veces
  más de las estrictamente necesarias — un costo bajo y aceptado a cambio
  de no tener que distinguir dos políticas de TTL distintas según el
  estado del partido.
- **Invalidación explícita (no depender solo del TTL):** cuando se
  registra un evento nuevo (gol) en Neo4j, la aplicación ejecuta
  `DEL cache:partido:{id}` **en el mismo momento**, no espera a que
  venza el TTL. El TTL de 45s queda como red de seguridad para el caso en
  que, por un error, la invalidación explícita no se dispare — nunca como
  el mecanismo principal. Ver `scripts/cache.redis`, sección 3.
- **Si Redis no tiene la clave o no está disponible:** mismo camino que
  un cache miss — la aplicación cae a Neo4j. La caché es prescindible y
  reconstruible por definición; un resultado nunca depende únicamente de
  que Redis esté arriba.
- **Qué NO se cachea acá:** el nombre de los jugadores que figuran en la
  encuesta de figura (PA4) no se duplica en Redis — se resuelve contra
  MongoDB por `jugador_id` cuando la aplicación arma la pantalla. Evita
  mantener sincronizados dos lugares con el mismo nombre de jugador.
