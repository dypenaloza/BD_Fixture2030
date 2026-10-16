# API REST Integrada del Fixture 2030 (Hito 10)

API REST en FastAPI que integra las seis bases NoSQL construidas en
los hitos anteriores del TPO (MongoDB, Neo4j, Cassandra, Redis,
InfluxDB 3 Core e InterSystems IRIS), con un endpoint de lectura por
fuente.

## Arranque rápido

```bash
# 1. Levantar las 6 bases con sus datos de carga (ver cada hito).
# 2. Configurar credenciales
cp .env.example .env
# completar .env con host/puerto/password reales de cada base
# (IRIS requiere un paso extra, ver docs/conectividad_y_configuracion.md)

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Verificar que las 6 bases responden
python scripts/verificar_conectividad.py

# 5. Levantar la API
uvicorn app.main:app --reload
# o: bash scripts/iniciar_api.sh
```

Documentación interactiva (Swagger UI): `http://127.0.0.1:8000/docs`.

## Endpoints

| Método | Ruta | Fuente |
|---|---|---|
| GET | `/selecciones/{codigo}` | MongoDB |
| GET | `/partidos/{partido_id}/eventos` | Neo4j |
| GET | `/partidos/{partido_id}/comentarios` | Cassandra |
| GET | `/sesiones/{usuario_id}` | Redis |
| GET | `/partidos/{partido_id}/estadisticas` | InfluxDB 3 Core |
| GET | `/partidos/{codigo}/detalle` | InterSystems IRIS |

Contrato completo de parámetros, formatos de ID y códigos de error por
endpoint: `docs/contratos_y_errores.md`.

## Estructura

```
app/
  routes/       Routers FastAPI: validan parametros y arman la respuesta HTTP
  services/     Reglas de cada caso de uso
  adapters/     Un adaptador por fuente: unico lugar que usa el driver nativo
  schemas/      Modelos Pydantic de request/response
  config/       Configuracion via variables de entorno (.env)
  main.py       App FastAPI, routers, middleware de logging y ciclo de vida

docs/
  casos_de_uso.md                   Diseño funcional (CU01-CU06)
  arquitectura_y_adaptadores.md     Capas, patron de conexion por fuente
  contratos_y_errores.md            Parametros, formatos y codigos HTTP por endpoint
  conectividad_y_configuracion.md   Variables de entorno y puesta en marcha
  pruebas_y_evidencia.md            Que se probo, bugs encontrados, evidencia
  evidencia/                        Capturas de Swagger UI (exito/error por fuente)

openapi/openapi.json    Contrato OpenAPI exportado de la API real
postman/                 Coleccion Postman con los 6 endpoints (exito + error)
tests/unit/              Tests de validaciones (no requieren bases levantadas)
tests/integration/       Tests end-to-end en pytest (requieren las 6 bases)
tests/pruebas_integracion.ps1   Suite de integracion equivalente en PowerShell
scripts/                 iniciar_api, verificar_conectividad, ejecutar_pruebas
```

## Arquitectura

```
Cliente HTTP -> Router -> Servicio -> Adaptador especifico -> Base NoSQL
```

Cada fuente tiene su propio adaptador y nunca comparte conexión ni
formato de identificador con otra. Mongo/Neo4j/Cassandra/Redis cachean
un pool de conexión; InfluxDB e IRIS no mantienen estado entre
requests. Ver el detalle y las decisiones de diseño en
`docs/arquitectura_y_adaptadores.md`.

## Tests

```bash
pip install -r requirements-dev.txt

# Unitarios (puros, sin bases levantadas)
pytest tests/unit/ -v

# Integracion (requiere las 6 bases + la API corriendo)
pytest tests/integration/ -v

# Ambos
bash scripts/ejecutar_pruebas.sh

# Suite equivalente en PowerShell (Windows)
./tests/pruebas_integracion.ps1
```

## Notas de configuración

IRIS requiere un paso de configuración adicional (resetear la
contraseña de `_SYSTEM` para habilitar autenticación de red) que no
era necesario en el Hito 9. Ver `docs/conectividad_y_configuracion.md`,
sección 3.
