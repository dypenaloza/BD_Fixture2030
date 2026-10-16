# Conectividad y configuración — API REST Fixture 2030

## 1. Variables de entorno

La API carga su configuración desde un archivo `.env` en la raíz de
`API_REST/` (ver `app/config/settings.py`, usa `python-dotenv`). Copiar
`.env.example` a `.env` y completar los valores reales:

```
cp API_REST/.env.example API_REST/.env
```

`.env` está en `.gitignore`: nunca se commitea con credenciales reales.

| Variable | Fuente | Default | Obligatoria |
|---|---|---|---|
| `MONGO_USER` | MongoDB | `admin` | No |
| `MONGO_PASSWORD` | MongoDB | — | Sí |
| `MONGO_HOST` / `MONGO_PORT` | MongoDB | `127.0.0.1` / `27017` | No |
| `MONGO_DB` | MongoDB | `fixture2030` | No |
| `NEO4J_URI` | Neo4j | `bolt://127.0.0.1:7687` | No |
| `NEO4J_USER` / `NEO4J_PASSWORD` | Neo4j | `neo4j` / — | Password sí |
| `NEO4J_DATABASE` | Neo4j | `neo4j` | No |
| `CASSANDRA_HOST` / `CASSANDRA_PORT` | Cassandra | `127.0.0.1` / `9042` | No |
| `CASSANDRA_KEYSPACE` | Cassandra | `fixture2030` | No |
| `REDIS_URL` | Redis | `redis://127.0.0.1:6379/0` | No |
| `INFLUX_URL` | InfluxDB | `http://127.0.0.1:8181` | No |
| `INFLUX_DATABASE` | InfluxDB | `fixture2030` | No |
| `INFLUX_TOKEN_FILE` | InfluxDB | `../InfluxDB/.influxdb3-token` | Sí (o el archivo debe existir) |
| `IRIS_HOST` / `IRIS_PORT` | IRIS | `127.0.0.1` / `1972` | No |
| `IRIS_NAMESPACE` | IRIS | `USER` | No |
| `IRIS_USERNAME` / `IRIS_PASSWORD` | IRIS | `_SYSTEM` / — | Password sí |

## 2. Puesta en marcha local (resumen)

1. Levantar las 6 bases (contenedores o instalaciones locales de hitos
   anteriores), cada una con los datos cargados por su propio script
   de carga (ver cada carpeta del hito correspondiente).
2. Completar `API_REST/.env` con host/puerto/credenciales reales.
3. Instalar dependencias: `pip install -r API_REST/requirements.txt`.
4. Ejecutar `python scripts/verificar_conectividad.py` para confirmar
   que las 6 bases responden antes de levantar la API.
5. Levantar la API: `bash scripts/iniciar_api.sh` (o `uvicorn
   app.main:app --reload` desde `API_REST/`).

## 3. Requisito nuevo de este hito: autenticación de red en IRIS

Los hitos anteriores de IRIS (Hito 9) solo usaron la terminal local
(`iris session IRIS`), que no exige autenticación de red. La API REST
se conecta por **DB-API sobre el puerto 1972**, y ahí sí se exige
autenticación (`%Service_Bindings` con `AutheEnabled=32`, password
requerido). Las credenciales por defecto (`_SYSTEM`/`SYS`, etc.) **no
sirven** para esta conexión: hay que resetear la contraseña del
usuario una vez por instancia, desde la terminal local:

```objectscript
zn "%SYS"
kill props
set props("Password")="<password-elegido>"
set props("PasswordNeverExpires")=1
set props("ChangePassword")=0
set sc = ##class(Security.Users).Modify("_SYSTEM",.props)
```

Verificar que funcionó, en la misma terminal:

```objectscript
write $System.Security.Login("_SYSTEM","<password-elegido>")
```

Debe devolver `1`. Ese mismo password va en `IRIS_PASSWORD` del
`.env` (usuario en `IRIS_USERNAME`, por defecto `_SYSTEM`). Este paso
se hace **una sola vez por instancia** de IRIS (no hay que repetirlo
en cada arranque de la API). Sin este paso, cualquier request a
`/partidos/{codigo}/detalle` falla con `IRIS_UNAVAILABLE` (503) aunque
el contenedor de IRIS esté arriba y "healthy".

## 4. Comportamiento ante una fuente caída

Las seis fuentes, ante una caída de conexión, responden **503** con el
formato de error común (nunca un 500 sin manejar ni un timeout
colgado). IRIS, al abrir una conexión nueva por consulta (ver
`docs/arquitectura_y_adaptadores.md`, sección 4), no requiere ningún
paso de recuperación manual: en cuanto la base vuelve a estar
disponible, el siguiente request ya funciona. Ver la evidencia de las
pruebas en `docs/pruebas_y_evidencia.md`.
