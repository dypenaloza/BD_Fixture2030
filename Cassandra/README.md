### BD_Fixture2030 — Hito 6: Módulo de Comentarios Masivos (Apache Cassandra)
**Grupo 12** · Ingeniería de Datos 2, Viernes turno noche.  
**Integrantes:** Dayana Peñaloza · Franco Churba · Juan Bautista Mangoni.

Módulo tabular distribuido de **Comentarios Masivos** del Fixture del Mundial 2030, implementado sobre **Apache Cassandra**. Ver el análisis completo de patrones de acceso en [`docs/patrones_de_acceso.md`](docs/patrones_de_acceso.md), la especificación del modelo en [`docs/modelo_tabular.md`](docs/modelo_tabular.md) y la estrategia de bucketing en [`docs/decisiones_particion.md`](docs/decisiones_particion.md).

---

### Requisitos Previos
* **Docker Desktop** (con Docker Engine + Docker Compose Plugin v2) en la notebook del equipo.
* **Python 3.9+** (para el script de carga masiva sintética `carga_masiva.py` con `cassandra-driver`).
* **cqlsh** (incluido dentro del contenedor de Cassandra; no requiere instalación local en la SO).

---

### 1. Ambiente de Ejecución (Docker & Cassandra)

#### Archivo `docker-compose.yml`
```yaml
version: '3.8'

services:
  cassandra:
    image: cassandra:latest
    container_name: fixture2030-cassandra
    restart: always
    ports:
      - "9042:9042"
    environment:
      - CASSANDRA_CLUSTER_NAME=Fixture2030Cluster
      - CASSANDRA_ENDPOINT_SNITCH=GossipingPropertyFileSnitch
      - MAX_HEAP_SIZE=2048M
      - HEAP_NEWSIZE=512M
    volumes:
      - ~/docker/data/cassandra:/var/lib/cassandra
      - ./scripts:/scripts
    healthcheck:
      test: ["CMD-SHELL", "nodetool status | grep -E '^UN'"]
      interval: 10s
      timeout: 10s
      retries: 10
      start_period: 40s
```

#### Iniciar el servicio
```bash
# 1. Abrir Docker Desktop
# 2. Desde la carpeta raíz del módulo Cassandra (fixture2030-cassandra/ o Cassandra/):
docker compose up -d
```
*Esto descarga la imagen `cassandra:latest`, configura los puertos y crea el montaje de volumen persistente.*

#### Verificar que Cassandra está disponible
```bash
# 1. Verificar que el contenedor esté corriendo y 'healthy'
docker compose ps

# 2. Comprobar el estado del nodo con nodetool (Estado esperado: UN = Up/Normal)
docker exec -it fixture2030-cassandra nodetool status

# 3. Conectarse a la consola interactiva de CQL
docker exec -it fixture2030-cassandra cqlsh
```

#### Detención, reinicio y persistencia de datos
```bash
docker compose stop      # Detiene el contenedor, conserva todos los datos en ~/docker/data/cassandra
docker compose start     # Vuelve a levantar el servicio sobre los mismos datos
docker compose restart   # Equivalente a stop + start
docker compose down      # Elimina el contenedor, PERO EL VOLUMEN LOCAL PERSISTE
```
* **Persistencia:** Los datos residen fuera del ciclo de vida del contenedor en `~/docker/data/cassandra`.
* **Reinicio desde cero (Reset):** Para recrear el ambiente completamente limpio, ejecutar `docker compose down`, eliminar el contenido de `~/docker/data/cassandra` y volver a ejecutar `docker compose up -d`.

---

### 2. Diseño Tabular Dirigido por Consultas (*Query-Driven Design*)

#### Definición de Keyspace
```cql
CREATE KEYSPACE IF NOT EXISTS fixture2030_comentarios
WITH replication = {
  'class': 'SimpleStrategy',
  'replication_factor': 1
};

USE fixture2030_comentarios;
```
*Nota de arquitectura:* Para el laboratorio local de nodo único se utiliza `SimpleStrategy` y `replication_factor: 1`. En un despliegue productivo multirregional se utiliza `NetworkTopologyStrategy` con factor de replicación 3 por datacenter.

#### Patrones de Acceso Prioritarios
1. **Q1 (Lectura Principal):** Recuperar los comentarios más recientes de un partido en una ventana de tiempo acotada (Feed en vivo).
2. **Q2 (Escritura Masiva):** Absorber ráfagas continuas de escrituras (más de 1.000.000 de comentarios por encuentro).
3. **Q3 (Consulta Secundario - Perfil de Usuario):** Recuperar el historial de comentarios publicados por un usuario sin realizar escaneos globales (`ALLOW FILTERING`).

#### Tabla Principal: `comentarios_por_partido` (Estrategia de Bucketing Temporal)
Para evitar que partidos extremadamente populares generen **Hotspots** o particiones gigantescas (>100MB / millones de filas), se aplica una estrategia de **Bucketing Temporal** combinando el `partido_id` con una ventana horaria (`fecha_bucket` = `YYYY-MM-DD-HH`).

```cql
CREATE TABLE IF NOT EXISTS comentarios_por_partido (
    partido_id text,
    fecha_bucket text,          -- Ej: '2030-06-13-20' (Bucket horario para acotar la partición)
    creado_en timestamp,
    comentario_id uuid,
    usuario_id text,
    usuario_nombre text,
    contenido text,
    estado_moderacion text,     -- 'APROBADO', 'PENDIENTE', 'OCULTO'
    likes int,
    PRIMARY KEY ((partido_id, fecha_bucket), creado_en, comentario_id)
) WITH CLUSTERING ORDER BY (creado_en DESC, comentario_id ASC);
```
* **Clave de Partición (`(partido_id, fecha_bucket)`):** Distribuye uniformemente la carga en el clúster a lo largo del tiempo y garantiza que ninguna partición supere el límite recomendado de Cassandra (~100MB).
* **Columnas de Clustering (`creado_en DESC, comentario_id ASC`):** Ordena físicamente los comentarios dentro del disco desde el más reciente al más antiguo.

#### Tabla Secundaria (RF10): `comentarios_por_usuario` (Duplicación Controlada)
Para responder a consultas de perfil de usuario sin depender del antipatrón `ALLOW FILTERING`, se implementa una tabla de acceso orientada a usuario con duplicación controlada:

```cql
CREATE TABLE IF NOT EXISTS comentarios_por_usuario (
    usuario_id text,
    creado_en timestamp,
    partido_id text,
    comentario_id uuid,
    contenido text,
    likes int,
    PRIMARY KEY (usuario_id, creado_en, comentario_id)
) WITH CLUSTERING ORDER BY (creado_en DESC, comentario_id ASC);
```

---

### 3. Instalación de Dependencias de Python
```bash
python3 -m venv .venv
source .venv/bin/activate        # En Windows: .venv\Scriptsctivate
pip install -r requirements.txt
```

---

### 4. Carga de Datos y Pruebas CQL

#### Ejecución de Scripts
```bash
# 1. Crear Keyspace y Tablas
docker exec -i fixture2030-cassandra cqlsh < scripts/esquema.cql

# 2. Cargar Dataset de muestra funcional
docker exec -i fixture2030-cassandra cqlsh < scripts/carga_muestra.cql

# 3. Ejecutar operaciones CRUD y consultas avanzadas
docker exec -i fixture2030-cassandra cqlsh < scripts/crud.cql
docker exec -i fixture2030-cassandra cqlsh < scripts/consultas.cql
```

#### Ejemplos de Sentencias CRUD
```cql
-- INSERT / UPSERT (Inyección de un nuevo comentario)
INSERT INTO comentarios_por_partido (partido_id, fecha_bucket, creado_en, comentario_id, usuario_id, usuario_nombre, contenido, estado_moderacion, likes)
VALUES ('F2030-001', '2030-06-13-20', '2030-06-13 20:15:30+0000', 11111111-1111-1111-1111-111111111111, 'USR-101', 'Sofía Gómez', '¡Golazo de Argentina!', 'APROBADO', 12);

-- SELECT (Ventana temporal acotada por Clave de Partición Completa)
SELECT creado_en, usuario_nombre, contenido, likes
FROM comentarios_por_partido
WHERE partido_id = 'F2030-001' AND fecha_bucket = '2030-06-13-20'
  AND creado_en >= '2030-06-13 20:10:00+0000' AND creado_en <= '2030-06-13 20:20:00+0000'
LIMIT 20;

-- UPDATE (Modificación delimitada por la Clave Primaria Completa)
UPDATE comentarios_por_partido
SET likes = 13
WHERE partido_id = 'F2030-001' AND fecha_bucket = '2030-06-13-20'
  AND creado_en = '2030-06-13 20:15:30+0000' AND comentario_id = 11111111-1111-1111-1111-111111111111;

-- DELETE (Eliminación precisa dejando tombstone)
DELETE FROM comentarios_por_partido
WHERE partido_id = 'F2030-001' AND fecha_bucket = '2030-06-13-20'
  AND creado_en = '2030-06-13 20:15:30+0000' AND comentario_id = 11111111-1111-1111-1111-111111111111;
```

---

### 5. Carga Masiva y Medición de Rendimiento (>1.000.000 Comentarios)

Para responder a **RF11** y **RF12**, se desarrolló el script `scripts/carga_masiva.py` que utiliza ejecuciones asíncronas concurrentes sobre la API de `cassandra-driver`.

```bash
# Iniciar la generación e ingesta asíncrona masiva:
python3 scripts/carga_masiva.py
```

#### Métrica y Resultados Observados (Evidencia en `docs/rendimiento.md`):
* **Volumen insertado:** 1.050.000 comentarios distribuidos en los 127 partidos del torneo.
* **Tiempo total de ingesta:** 112.4 segundos.
* **Tasa de transferencia (Throughput):** **9.341 escrituras / segundo** (picos de **11.200 req/s** en hardware local).
* **Distribución de Partición:** Promedio de ~1.8 MB por bucket de 1 hora, validando la eliminación de hotspots.

---

### 6. Estructura de Archivos
```text
fixture2030-cassandra/
├── docker-compose.yml          # Servicio Cassandra:latest y volumen nombrado
├── requirements.txt            # cassandra-driver, Faker
├── scripts/
│   ├── esquema.cql             # Creación de KEYSPACE y TABLAS
│   ├── carga_muestra.cql       # Dataset inicial mínimo
│   ├── crud.cql                # Sentencias de Insert, Select, Update, Delete
│   ├── consultas.cql           # Consultas por ventana de tiempo e historia de usuario
│   └── carga_masiva.py         # Script Python de ingestión asíncrona de 1M+ registros
├── docs/
│   ├── patrones_de_acceso.md   # Justificación de las preguntas de negocio
│   ├── modelo_tabular.md       # Detalle de esquemas, tipos y claves primarias
│   ├── decisiones_particion.md# Estrategia de Bucketing y hotspots
│   └── rendimiento.md          # Evidencia del benchmark y tasa de escritura
├── evidencia/
│   ├── 01_nodetool_status.txt  # Estado 'UN' del nodo en Docker
│   ├── 02_esquema_keyspace.txt # Verificación de tablas en cqlsh
│   ├── 03_operaciones_crud.txt # Logs de ejecución de sentencias CQL
│   ├── 04_carga_masiva.txt     # Log del proceso de ingestión de >1M comentarios
│   └── 05_tracing_cql.txt      # Trazado TRACING ON de consulta
└── README.md                   # Instrucciones de ejecución (este archivo)
```

---

### 7. Limitaciones Conocidas
1. **Laboratorio de Nodo Único:** El entorno local ejecuta 1 solo nodo (`SimpleStrategy`, `replication_factor: 1`). No simula la tolerancia a fallas de un clúster multirregional productivo (`NetworkTopologyStrategy`).
2. **Generación Sintética:** Los textos de los comentarios e identidades de usuario se generan con `Faker` manteniendo distribuciones de tiempo realistas.
3. **Límite de Hardware:** La velocidad máxima de escrituras está acotada por la capacidad de CPU/SSD de la máquina anfitriona.
4. **Tombstones:** Las operaciones de borrado (`DELETE`) generan registros tipo tombstone que impactan temporalmente la latencia hasta que el motor ejecuta la compactación (*Compaction*).
