# Guía de demostración (RF13, sección 6.3)

Todos los comandos de este documento fueron **ejecutados y verificados
en vivo** contra las 6 bases reales antes de entregarlo. Los IDs no son
de ejemplo genérico: son los que efectivamente existen en los datasets
cargados por cada módulo.

No hace falta mostrar los 6 flujos. Elegir 1-2 (sugerencia: MongoDB
por ser el más simple de entender, y Cassandra o Redis por mostrar una
decisión de modelado más interesante — partición temporal o TTL).

## Antes de arrancar

```bash
# Las 6 bases + la API del Hito 10 corriendo (ver API_REST/README.md)
# El stack de monitoreo del Hito 13 corriendo:
cd Hito13 && ./scripts/iniciar_monitoreo.sh && python3 scripts/verificar_targets.py
```

Abrir de antemano, en pestañas separadas: Swagger (`http://localhost:8000/docs`),
Grafana (`http://localhost:3000`), y una terminal.

## Opción A — Vía Swagger UI (recomendada si no hay Postman preparado)

1. Abrir `http://localhost:8000/docs`.
2. Elegir el endpoint `GET /selecciones/{codigo}`, "Try it out", poner
   `ARG`, ejecutar. Mostrar la respuesta 200 y señalar en el código
   (`API_REST/app/adapters/mongo_adapter.py`) que es una lectura
   directa de la colección `selecciones` por `_id`.
3. Elegir `GET /partidos/{partido_id}/comentarios`, poner
   `partido_id=M001`, `bucket_temporal=20:00-20:05`, `limit=5`.
   Mostrar la respuesta y explicar que `bucket_temporal` es la
   partición temporal real de Cassandra (ventana de 5 minutos) — no un
   filtro arbitrario, es la clave de partición.
4. (Opcional, para mostrar un error controlado) Repetir el punto 3 con
   `bucket_temporal=00:00-00:05` (partición real sin comentarios) →
   200 con lista vacía, para diferenciar "no hay datos" de "está caído".

## Opción B — Vía cURL (si se prefiere mostrar la terminal)

```bash
# MongoDB — lectura documental directa
curl -s http://localhost:8000/selecciones/ARG | python3 -m json.tool

# Neo4j — recorrido de grafo (eventos del partido P-A-1)
curl -s "http://localhost:8000/partidos/P-A-1/eventos" | python3 -m json.tool

# Cassandra — lectura por partición temporal (partido M001, ventana 20:00-20:05)
curl -s "http://localhost:8000/partidos/M001/comentarios?bucket_temporal=20:00-20:05&limit=5" | python3 -m json.tool

# Redis — sesión con TTL (usuario U27961)
curl -s http://localhost:8000/sesiones/U27961 | python3 -m json.tool

# InfluxDB — estadísticas en una ventana temporal (partido M001, equipo ARG)
curl -s "http://localhost:8000/partidos/M001/estadisticas?equipo_id=ARG&desde=2030-10-08T08:00:00Z&hasta=2030-10-08T08:30:00Z&limit=5" | python3 -m json.tool

# IRIS — entidad compleja con su relación hijo (partido M004 y sus eventos)
curl -s http://localhost:8000/partidos/M004/detalle | python3 -m json.tool
```

Casos de error, para mostrar que la API no "esconde" las fallas:

```bash
# Validación: formato de ID equivocado (ID de Cassandra en la ruta de Neo4j)
curl -s -w "\nHTTP %{http_code}\n" http://localhost:8000/partidos/M001/eventos
# -> 400 VALIDATION_ERROR

# Recurso inexistente
curl -s -w "\nHTTP %{http_code}\n" http://localhost:8000/partidos/Z999/detalle
# -> 404 PARTIDO_NOT_FOUND
```

## Opción C — Prueba de falla en vivo (si el tiempo alcanza, ~2 min)

Repite exactamente lo documentado en `Hito13/evidencia/prueba_de_falla.md`.
Tener Grafana abierto en el panel "Disponibilidad" antes de arrancar.

```bash
cd Hito13
./scripts/ejecutar_prueba_controlada.sh
```

Mientras corre (dura ~70 segundos), señalar en Grafana: el panel de
Redis pasa a DOWN, el panel de errores 5xx sube, y al final vuelve a
UP sin reiniciar nada. Si no alcanza el tiempo en la defensa, mostrar
directamente `Hito13/evidencia/dashboard_02_durante_falla_redis.png`.

## Opción D — Clientes nativos (si se quiere mostrar que no es "magia de la API")

```bash
# Redis directo (sin pasar por la API)
docker exec fixture2030-redis redis-cli HGETALL sesion:U27961
docker exec fixture2030-redis redis-cli TTL sesion:U27961

# Cassandra directo
docker exec fixture2030-cassandra cqlsh -e \
  "SELECT comentario_id, contenido FROM fixture2030.comentarios_por_partido WHERE partido_id='M001' AND bucket_temporal='20:00-20:05';"

# MongoDB directo
docker exec fixture2030-mongodb mongosh -u admin -p password123 \
  --authenticationDatabase admin --quiet \
  --eval 'db.getSiblingDB("fixture2030").selecciones.findOne({_id:"ARG"})'
```

Esto conecta con la pregunta típica de la FIFA ("¿cómo distinguen que
el problema está en la API y no en la base?"): si el cliente nativo
funciona y la API falla, el problema es de la API/adaptador; si ambos
fallan, es de la base o la red (ver `docs/defensa_por_base.md` y la
tabla de diagnóstico de la Clase 12).

## Grafana (para la sección "Evidencia" del guion)

1. Dashboard "Fixture 2030 — Observabilidad (Hito 13)".
2. Panel "Disponibilidad por componente": las 7 filas en UP.
3. Panel "Latencia P50/P95 por fuente": señalar que IRIS suele ser la
   más lenta (conexión nueva por consulta, no pool) — es una decisión
   consciente, no un bug (ver `Hito13/docs/decisiones_de_arquitectura.md` #3).
4. Panel "Comparación entre bases: Mongo vs Redis": Redis
   consistentemente más rápido o igual — esperable por ser lectura en
   memoria vs. documento en disco/caché del motor.
