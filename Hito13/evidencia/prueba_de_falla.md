# Prueba de falla controlada — Hito 13 (RF10/RF20/RF21)

- **Commit evaluado**: `7fcae442d4695990745709130678b62564e707aa` (HEAD
  de `main` en el momento de la prueba; RNF18).
- **Entorno**: Linux, Docker, API corriendo en el host (`127.0.0.1:8000`),
  stack de monitoreo (Prometheus/Grafana/exporters) en contenedores
  separados, 6 bases en contenedores Docker (ver `docker-compose.yml`
  de este hito y de cada módulo).
- **Dependencia elegida**: Redis (módulo de sesiones).
- **Operación**: `docker stop` / `docker start` — reversible, sin
  tocar volúmenes ni borrar datos.

## 1. Condición inicial (23:45:09Z)

- Contenedor `fixture2030-redis`: `running`.
- `GET /sesiones/U27961` → HTTP 200.
- Prometheus: los 7 targets (API + 2 exporters + 4 blackbox) en `up`.
- Las 4 alertas en `inactive`.
- Evidencia: `dashboard_01_estado_sano.png` (capturada después de la
  recuperación con una ventana corta, muestra el mismo estado sano).

## 2. Cambio aplicado (23:45:25Z)

```
docker stop fixture2030-redis
```

Sin `docker rm`, sin `-v`: el volumen de Redis permanece intacto.

## 3. Pruebas ejecutadas durante la falla

- `GET /sesiones/U27961` repetido ~55 veces durante los siguientes 110
  segundos → **HTTP 503** `{"code":"REDIS_UNAVAILABLE", ...}` en todos
  los casos (patrón ya documentado en el Hito 11 para Redis; se repite
  acá para generar la serie temporal en Prometheus/Grafana).

## 4. Respuesta observada en Prometheus/Grafana

- **Hallazgo clave** (documentado también en
  `docs/limitaciones_y_evidencia.md` y `docs/alertas_y_umbral.md` #4):
  el target `job="redis"` (el exporter) **se mantuvo en `up` para
  Prometheus** — el proceso del exporter seguía respondiendo al
  scrape. La métrica que sí reflejó la caída fue `redis_up` (propia
  del exporter, 1→0). Esto motivó reescribir la alerta
  `ExporterSinResponder` (que usaba `up{job="redis"}`) como
  `BaseInalcanzableDesdeSuExporter` (`redis_up == 0 or mongodb_up == 0`),
  porque la primera versión **no hubiera detectado esta caída real**.
- Panel "Disponibilidad": Redis pasó a `DOWN` (rojo) mientras las otras
  6 fuentes se mantuvieron en `UP`. Evidencia: `dashboard_02_durante_falla_redis.png`.
- Panel "Errores 5xx por fuente": serie de Redis subiendo desde 0 hasta
  ~0.2 errores/s. Mismo screenshot.
- Panel "Latencia P50/P95 por fuente": pico visible en la serie de
  Redis durante la ventana del incidente.
- Alertas en Prometheus (`prometheus_alertas_01_durante_falla.png`):
  - `APIErrorRateAlta` → **firing** (fuente=Redis).
  - `BaseInalcanzableDesdeSuExporter` → **firing** (componente=Redis).
  - `APILatenciaP95Alta` y `DependenciaTCPInalcanzable` → inactive (no
    les correspondía dispararse: Redis no tiene blackbox probe, y su
    latencia P95 durante la falla fue el tiempo de un 503 rápido, no
    una respuesta lenta).

## 5. Tiempo de espera

Cada request individual contra `/sesiones/U27961` con Redis caído
respondió en **~14 ms** (medido con `curl -w`), no hubo bloqueo ni
timeout largo: el adaptador de Redis usa `socket_connect_timeout=3`
pero el `connection refused` del puerto cerrado es inmediato.

## 6. Recuperación del servicio (23:50:17Z)

```
docker start fixture2030-redis
```

- `redis-cli PING` → `PONG` inmediato.
- `GET /sesiones/U27961` (sin reiniciar la API) → **HTTP 200**, mismos
  datos que antes de la caída (`ttlSegundos` había seguido bajando
  normalmente, sin resetearse: 1775s inicial → 1046s a la
  recuperación, consistente con el tiempo real transcurrido).
- `redis_up` volvió a 1 en el siguiente scrape.
- Alerta `BaseInalcanzableDesdeSuExporter` → resuelta (`inactive`) en
  el siguiente ciclo de evaluación.
- Alerta `APIErrorRateAlta` → siguió `firing` unos minutos más: la
  ventana de `rate(...[5m])` todavía incluía los 503 generados durante
  la falla. Se resuelve sola cuando esas muestras salen de la ventana
  de 5 minutos — comportamiento esperado de Prometheus, no un bug.
- Evidencia: `dashboard_03_despues_de_recuperar.png`,
  `prometheus_alertas_02_despues_de_recuperar.png`.

## 7. Datos/volúmenes conservados

El volumen de Redis nunca se tocó (`docker stop`/`docker start`, no
`rm`/`down -v`). La sesión de prueba sobrevivió la caída sin pérdida ni
reinicio de su TTL, confirmando que la falla fue exclusivamente de
disponibilidad del proceso, no de persistencia.
