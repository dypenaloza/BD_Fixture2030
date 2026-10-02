# fixture2030-redis — Hito 7: Caché de Usuarios y Sesiones

**Grupo 12** · Ingeniería de Datos II, viernes turno noche
Integrantes: Dayana Peñaloza · Franco Churba · Juan Bautista Mangoni

Módulo de caché y sesiones de la plataforma del Mundial 2030, implementado
sobre **Redis** en Docker Compose. Mantiene el estado transitorio de la
plataforma — sesiones de usuario, resultado de partidos en caché,
contadores y una encuesta de figura del partido — sin reemplazar a ningún
módulo anterior: la fuente de verdad de cada dato sigue viviendo en
[MongoDB](../MongoDB) (Hito 4) o [Neo4j](../Neo4j) (Hito 5).

📄 **Documentación:** [patrones de acceso](docs/patrones_de_acceso.md) ·
[modelo clave-valor](docs/modelo_clave_valor.md) ·
[ciclo de vida e invalidación](docs/ciclo_de_vida_e_invalidacion.md) ·
[memoria y escalabilidad](docs/memoria_y_escalabilidad.md) ·
[decisiones y análisis completo](docs/decisiones.md) ·
[evidencia técnica](docs/evidencia/)

---

## 1. Requisitos previos

- **Docker Desktop** (o Docker Engine + Compose v2) en la notebook.
- **Python 3.9+**, solo si se quiere regenerar `scripts/carga_muestra.redis`
  (no usa librerías externas). El archivo ya está versionado, así que no
  es obligatorio tenerlo para levantar y probar el módulo.
- Puerto **6379** libre.

## 2. Puesta en marcha

```bash
# 1. Levantar el ambiente (RF1)
docker compose up -d
docker compose ps                 # STATUS: "Up ... (healthy)"

# 2. Verificar el ambiente sin tocar datos
./scripts/ejecutar.sh scripts/inicializacion.redis

# 3. Cargar el dataset de muestra (RF11, idempotente — ver docs/decisiones.md §5)
./scripts/ejecutar.sh scripts/carga_muestra.redis
```

> **¿Por qué `./scripts/ejecutar.sh archivo.redis` y no
> `redis-cli < archivo.redis` directo?** `redis-cli` no sabe interpretar
> comentarios `#` al leer un archivo por `stdin` — los trata como un
> comando inválido. El wrapper filtra los comentarios antes de pasarle el
> archivo, así los `.redis` se pueden mantener comentados (RNF9) sin que
> eso rompa la ejecución. Detalle completo en
> [`docs/decisiones.md`](docs/decisiones.md#nota-técnica-por-qué-existe-scriptsejecutarsh).

### Conexión

| Cliente | Acceso |
|---|---|
| `redis-cli` (dentro del contenedor) | `docker exec -it fixture2030-redis redis-cli` |
| Driver / cliente externo | `redis://localhost:6379` (sin autenticación — ver Limitaciones) |

### Detención, reinicio y persistencia

```bash
docker compose stop      # detiene el contenedor; los datos persisten
docker compose start     # lo vuelve a levantar sobre los mismos datos
docker compose down      # elimina el contenedor; LOS DATOS PERSISTEN (bind mount)
```

La persistencia (RNF2) usa un **bind mount** a `~/docker/data/redis`
(convención específica de este hito, a diferencia de los volúmenes
nombrados usados en Mongo/Neo4j/Cassandra), con `appendonly yes` + `save
60 1`. Comprobado con un ciclo real `stop`/`start`:
[`docs/evidencia/06_persistencia.txt`](docs/evidencia/06_persistencia.txt).
Para reiniciar desde cero: detener el contenedor y borrar el contenido de
`~/docker/data/redis` antes de levantarlo de nuevo.

## 3. Uso: sesiones, caché, concurrencia y métricas

```bash
./scripts/ejecutar.sh scripts/sesiones.redis       # RF3/RF4/RF5/RF7
./scripts/ejecutar.sh scripts/cache.redis          # RF6/RF7
./scripts/ejecutar.sh scripts/concurrencia.redis   # RF8/RF9
./scripts/ejecutar.sh scripts/metricas.redis       # RF12/RF13
```

Cada script declara en su encabezado qué requisito cubre y qué espera
encontrar ya cargado. Pueden además copiarse bloque por bloque dentro de
`docker exec -it fixture2030-redis redis-cli` para una demostración en
vivo, parando entre cada comando — así es como están pensados los
comentarios internos de cada bloque.

## 4. El modelo en una pantalla

```
sesion:{usuarioId}                    Hash        TTL 1800s
cache:partido:{partidoId}             String      TTL 45s      (fuente de verdad: Neo4j)
contador:partido:{partidoId}:visitas  String      sin TTL      (INCR)
encuesta:{partidoId}:figura           Sorted Set  sin TTL      (ZINCRBY / ranking)
```

Detalle completo de propiedades, TTL y la justificación de cada estructura
en [`docs/modelo_clave_valor.md`](docs/modelo_clave_valor.md).

## 5. Datos

El dataset de muestra (200 sesiones, 6 partidos en caché, 6 contadores y 6
encuestas) está versionado en `scripts/carga_muestra.redis`, generado con
semilla fija (`SEED = 2030`, la misma del resto del TPO) por
`scripts/generar_datos.py`. Reutiliza identificadores ya existentes:
`usuario_id` del Hito 6 (Cassandra), `partido_id` del Hito 5 (Neo4j) y
`jugador_id` del Hito 4 (MongoDB) — ver
[`docs/decisiones.md §6`](docs/decisiones.md) para el detalle de
trazabilidad.

```bash
python3 scripts/generar_datos.py     # regenerar (opcional)
```

## 6. Estructura del repositorio

```
fixture2030-redis/
├── docker-compose.yml              # Redis latest + bind mount + maxmemory/noeviction
├── scripts/
│   ├── generar_datos.py            # genera carga_muestra.redis (reproducible)
│   ├── carga_muestra.redis         # dataset de muestra (generado)
│   ├── inicializacion.redis        # RF1: verificación del ambiente
│   ├── sesiones.redis              # RF3/RF4/RF5/RF7: ciclo de vida de sesión
│   ├── cache.redis                 # RF6/RF7: Cache-Aside + invalidación
│   ├── concurrencia.redis          # RF8/RF9: atomicidad + ranking
│   ├── metricas.redis              # RF12/RF13: observabilidad
│   └── ejecutar.sh                 # wrapper que filtra comentarios para redis-cli
├── docs/
│   ├── patrones_de_acceso.md       # RF2: PA1-PA4 justificados
│   ├── modelo_clave_valor.md       # RF2/RNF5: namespace de claves
│   ├── ciclo_de_vida_e_invalidacion.md  # RF3/RF4/RF6/RF7
│   ├── memoria_y_escalabilidad.md  # RF10
│   ├── decisiones.md               # análisis completo + tabla de decisiones
│   └── evidencia/                  # 6 salidas de consola reales
└── README.md
```

## 7. Cobertura de los requisitos

| Req. | Dónde se cumple |
|---|---|
| RF1 | `docker-compose.yml` · [`evidencia/01_ambiente.txt`](docs/evidencia/01_ambiente.txt) |
| RF2 | [`docs/patrones_de_acceso.md`](docs/patrones_de_acceso.md) |
| RF3 | [`scripts/sesiones.redis`](scripts/sesiones.redis) · [`evidencia/02_sesiones.txt`](docs/evidencia/02_sesiones.txt) |
| RF4 | [`docs/ciclo_de_vida_e_invalidacion.md §1`](docs/ciclo_de_vida_e_invalidacion.md) |
| RF5 | [`docs/modelo_clave_valor.md`](docs/modelo_clave_valor.md) |
| RF6 | [`docs/ciclo_de_vida_e_invalidacion.md §2`](docs/ciclo_de_vida_e_invalidacion.md) · [`scripts/cache.redis`](scripts/cache.redis) |
| RF7 | [`scripts/cache.redis`](scripts/cache.redis) · [`scripts/sesiones.redis`](scripts/sesiones.redis) |
| RF8 | [`scripts/concurrencia.redis`](scripts/concurrencia.redis) · [`evidencia/04_concurrencia_y_ranking.txt`](docs/evidencia/04_concurrencia_y_ranking.txt) |
| RF9 | Encuesta de figura (`ZREVRANGE ... WITHSCORES`), mismo script y evidencia que RF8 |
| RF10 | `docker-compose.yml` (`maxmemory`/`maxmemory-policy`) · [`docs/memoria_y_escalabilidad.md`](docs/memoria_y_escalabilidad.md) |
| RF11 | `scripts/generar_datos.py` + `scripts/carga_muestra.redis` |
| RF12 | [`scripts/metricas.redis`](scripts/metricas.redis) · [`docs/decisiones.md §5`](docs/decisiones.md) |
| RF13 | [`docs/evidencia/`](docs/evidencia/) (6 archivos) |
| RNF1 | `image: redis:latest`, sin versión fijada; versión observada registrada en `evidencia/01_ambiente.txt` |
| RNF2 | Bind mount `~/docker/data/redis` · [`evidencia/06_persistencia.txt`](docs/evidencia/06_persistencia.txt) |
| RNF3 | Este README + `scripts/ejecutar.sh` |
| RNF4 | `HSET`/`SET`/`ZADD` sobre claves determinísticas — reejecutar `carga_muestra.redis` no duplica nada (ver `docs/decisiones.md §3`) |
| RNF5 | Convención `dominio:id[:subdominio]`, documentada en `docs/modelo_clave_valor.md` |
| RNF6 | Todo dato temporal tiene TTL y regla de renovación/invalidación explícita (`docs/ciclo_de_vida_e_invalidacion.md`) |
| RNF7 | Sin credenciales reales; `redis-cli` local sin password (ver Limitaciones) |
| RNF8 | `scripts/metricas.redis` usa `SCAN`, nunca `KEYS *` |
| RNF9 | Scripts `.redis` separados por propósito y comentados |
| RNF10 | Fecha, versión de Redis y resultado observado registrados en `docs/decisiones.md §5` |

## 8. Limitaciones conocidas

- **Sin autenticación:** el contenedor no configura `requirepass` ni ACL,
  igual que el material de la Clase 8. Válido para un laboratorio local;
  en un ambiente real se definiría por variable de entorno (RNF7), nunca
  escrita en el compose.
- **Concurrencia demostrada, no medida bajo carga real:** `INCR`/`ZINCRBY`
  se ejecutan secuencialmente desde un único `redis-cli` en la demo. La
  atomicidad es una garantía del comando en el servidor, no depende de
  que la demo lance clientes paralelos reales — pero no se reportan
  cifras de throughput porque el método no incluyó carga concurrente real
  (ver `docs/decisiones.md §5`).
- **Nodo único:** sin réplicas, Sentinel ni Cluster — fuera de alcance
  explícito de este hito (ver `docs/memoria_y_escalabilidad.md`).
- **Dataset de demostración, no de producción:** 200 sesiones y 6
  partidos, suficientes para mostrar los seis flujos pedidos sin consumir
  el tiempo de la práctica.
