# Memoria y escalabilidad (RF10, RNF6)

## Política de memoria elegida: `noeviction` + `maxmemory 100mb`

```yaml
# docker-compose.yml
command: redis-server --maxmemory 100mb --maxmemory-policy noeviction
```

### El problema que esta decisión tiene que resolver

Sesiones (`sesion:*`) y caché (`cache:partido:*`) conviven en el mismo
proceso de Redis, pero tienen prioridades opuestas:

- Si Redis se queda sin memoria, **perder una entrada de caché no importa**
  — se reconstruye con el próximo cache miss contra Neo4j.
- Si Redis se queda sin memoria, **perder una sesión activa sí importa**
  — el usuario queda deslogueado sin haberlo pedido.

### Por qué no alcanza con una política LRU/LFU estándar

Las políticas `volatile-*` (`volatile-lru`, `volatile-lfu`,
`volatile-ttl`) solo consideran para evicción las claves que **tienen
TTL**. El problema es que en este módulo **tanto la caché como las
sesiones tienen TTL** (`cache:partido:*` con 45s, `sesion:*` con 1800s).
Activar `volatile-lru` no protege selectivamente a las sesiones: bajo
presión de memoria, Redis podría igual elegir borrar una sesión con
mucho tiempo de vida restante con tal de liberar espacio, simplemente
porque hace más tiempo que no se tocó. `allkeys-lru`/`allkeys-lfu` tienen
el mismo problema, agravado (consideran *todas* las claves, con o sin
TTL).

En otras palabras: en Redis la política de evicción es **una sola, para
toda la instancia** — no se puede decir "evictá `cache:*` libremente pero
nunca `sesion:*`" dentro de un único proceso.

### Alternativa evaluada y descartada (para este entregable)

La solución de fondo sería correr dos instancias lógicas separadas —
sesiones en una instancia con `noeviction`, caché en otra con
`allkeys-lru` — y que la aplicación decida a cuál conectarse según el
tipo de dato. Se descartó para este hito porque el enunciado no pide
(y explícitamente excluye) una topología de múltiples nodos o Cluster
para el laboratorio local, y el volumen de datos de la demo (unas pocas
decenas de KB) no se acerca ni de lejos a un límite real de memoria. Se
documenta acá como el paso natural de escalamiento si el módulo creciera
a producción.

### Por qué `noeviction` para este laboratorio

Con un solo proceso y la obligación de no sacrificar sesiones
silenciosamente, `noeviction` es la única política que no puede borrar
una sesión por error. El costo es que, si se alcanza el límite de
memoria, **las escrituras nuevas fallan con un error** (`OOM command not
allowed...`) en lugar de liberar espacio solas. Se acepta ese costo
porque:

1. Es un costo *visible y manejable por la aplicación* (puede reintentar,
   alertar o degradar), mientras que perder una sesión por evicción
   silenciosa no se nota hasta que el usuario se queja.
2. `maxmemory 100mb` es, para el volumen de este laboratorio (unas pocas
   decenas de KB con 200 sesiones + 6 claves de caché + 6 encuestas, ver
   `docs/evidencia/05_metricas.txt`), una cota muy por encima de lo que
   se necesita — en la práctica no se va a alcanzar durante la demo, y el
   valor queda ahí como un límite explícito y documentado en vez de
   dejar la memoria sin tope (lo que pide RF10: "definir y configurar, o
   justificar documentalmente, el comportamiento esperado").

## TTL (expiración) vs. evicción por memoria — no son el mismo mecanismo

| | Expiración (TTL) | Evicción (memoria) |
|---|---|---|
| Dispara por | Tiempo transcurrido desde el `EXPIRE`/`SET ... EX`. | `maxmemory` alcanzado. |
| Decide qué borrar | La aplicación, al definir el TTL de cada clave. | La política de `maxmemory-policy` (en este módulo, ninguna: con `noeviction` nunca evict). |
| Efecto sobre `sesion:*` | Esperado y deseado (inactividad = fin de sesión). | No debería ocurrir nunca con esta configuración. |
| Efecto sobre `cache:partido:*` | Esperado (dato "vivo" con ventana corta). | No debería ocurrir nunca con esta configuración. |
| Evidencia | `docs/evidencia/02_sesiones.txt` (TTL de 5s venciendo en vivo). | `docs/evidencia/05_metricas.txt` → `evicted_keys:0`. |

La métrica `evicted_keys` en `INFO stats` quedó en `0` durante toda la
prueba (ver evidencia): con el volumen de este laboratorio nunca se llegó
a presionar la memoria, que es exactamente el resultado esperado dado
`maxmemory 100mb`.

## Escalabilidad: de este laboratorio a un entorno real

El contenedor de este módulo es un **nodo único** — sirve para validar
operaciones y modelado, no para probar tolerancia a fallas ni
distribución real (ver Clase 8, sección "Escalabilidad y disponibilidad").
Si el volumen de usuarios/partidos creciera:

- **Primary + réplicas** (con Sentinel) resolvería disponibilidad de
  lectura y failover del primary, sin cambiar el modelo de claves.
- **Redis Cluster** resolvería el límite de memoria de un solo nodo,
  particionando por slot — las claves con un identificador en común (ej.
  todas las de un mismo partido) podrían forzarse al mismo slot con un
  hash tag (`cache:partido:{P-A-1}`, `encuesta:{P-A-1}:figura`) si alguna
  operación necesitara combinarlas atómicamente.
- Ninguno de los dos cambia RF3-RF9: son decisiones de infraestructura,
  no de modelo de datos — por eso no se implementan en este hito (el
  enunciado no las pide y el entorno local no las necesita), pero quedan
  documentadas como el camino de escalamiento.
