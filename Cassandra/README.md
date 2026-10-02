### BD_Fixture2030 — Hito 6: Módulo de Comentarios Masivos (Apache Cassandra)
**Grupo 12** · Ingeniería de Datos 2, Viernes turno noche.
**Integrantes:** Dayana Peñaloza · Franco Churba · Juan Bautista Mangoni.

Módulo tabular distribuido de **Comentarios Masivos** del Fixture del Mundial 2030, implementado sobre **Apache Cassandra**. Ver el análisis completo de patrones de acceso en [`docs/patrones_de_acceso.md`](docs/patrones_de_acceso.md), la especificación del modelo en [`docs/modelo_tabular.md`](docs/modelo_tabular.md), la estrategia de bucketing en [`docs/decisiones_de_particionamiento.md`](docs/decisiones_de_particionamiento.md) y la medición de rendimiento en [`docs/rendimiento.md`](docs/rendimiento.md).

---

### Requisitos Previos
* **Docker Desktop** (con Docker Engine + Docker Compose Plugin v2) en la notebook del equipo.
* **Python 3.9+** (solo para `scripts/generar_comentarios.py`, el generador del dataset de carga masiva). No usa librerías externas: no hace falta `pip install` nada ni un entorno virtual.
* **cqlsh** (incluido dentro del contenedor de Cassandra; no requiere instalación local en la SO).

---

### 1. Ambiente de Ejecución (Docker & Cassandra)

#### Archivo `docker-compose.yml`
```yaml
services:
  cassandra:
    image: cassandra:latest
    container_name: fixture2030-cassandra
    restart: unless-stopped
    environment:
      CASSANDRA_CLUSTER_NAME: Fixture2030_Cassandra
      CASSANDRA_DC: datacenter1
      CASSANDRA_RACK: rack1
      CASSANDRA_ENDPOINT_SNITCH: GossipingPropertyFileSnitch
    ports:
      - "9042:9042"
    volumes:
      - cassandra_data:/var/lib/cassandra
      - ./scripts:/scripts:ro
      - ./data:/data

volumes:
  cassandra_data:
    name: fixture2030_cassandra_data
```

#### Iniciar el servicio
```bash
# 1. Abrir Docker Desktop
# 2. Desde la carpeta raíz del módulo (Cassandra/):
docker compose up -d
```
*Esto descarga la imagen `cassandra:latest` (si no está en caché local), configura el puerto nativo CQL y crea el volumen nombrado `fixture2030_cassandra_data`.*

#### Verificar que Cassandra está disponible
```bash
# 1. Verificar que el contenedor esté corriendo (puede tardar ~30-40s en estar listo)
docker compose ps

# 2. Comprobar el estado del nodo con nodetool (Estado esperado: UN = Up/Normal)
docker exec -it fixture2030-cassandra nodetool status

# 3. Conectarse a la consola interactiva de CQL
docker exec -it fixture2030-cassandra cqlsh
```

#### Detención, reinicio y persistencia de datos
```bash
docker compose stop      # Detiene el contenedor, conserva todos los datos
docker compose start     # Vuelve a levantar el servicio sobre los mismos datos
docker compose restart   # Equivalente a stop + start
docker compose down      # Elimina el contenedor, PERO EL VOLUMEN NOMBRADO PERSISTE
```
* **Persistencia (RNF2):** los datos de Cassandra viven en el volumen nombrado de Docker `fixture2030_cassandra_data`, fuera del ciclo de vida del contenedor — sobreviven a `stop`, `restart` y `down` (sin `-v`).
* **Reinicio desde cero (Reset):** `docker compose down -v` elimina también el volumen (⚠️ se pierden todos los datos). Luego `docker compose up -d` y repetir la carga desde el paso 4.

---

### 2. Diseño Tabular Dirigido por Consultas (*Query-Driven Design*)

#### Definición de Keyspace
```cql
CREATE KEYSPACE IF NOT EXISTS fixture2030
WITH replication = {
  'class': 'SimpleStrategy',
  'replication_factor': 1
};

USE fixture2030;
```
*Nota de arquitectura:* para el laboratorio local de nodo único se utiliza `SimpleStrategy` y `replication_factor: 1`. En un despliegue productivo multirregional se utilizaría `NetworkTopologyStrategy` con factor de replicación por datacenter.

#### Patrones de Acceso Prioritarios
Ver el detalle completo en [`docs/patrones_de_acceso.md`](docs/patrones_de_acceso.md).
1. **PA1 (Lectura Principal):** últimos comentarios de un partido en una ventana reciente.
2. **PA2 (Lectura por ventana temporal):** comentarios de un partido dentro de un rango de tiempo acotado.
3. **PA3 (Historial de usuario):** comentarios publicados por un usuario, sin `ALLOW FILTERING`.

#### Tabla Principal: `comentarios_por_partido` (Bucketing Temporal)
Para evitar que partidos muy comentados generen **hotspots** o particiones gigantescas, se combina `partido_id` con un `bucket_temporal` (ventana de 5 minutos, ver [`docs/decisiones_de_particionamiento.md`](docs/decisiones_de_particionamiento.md)):

```cql
CREATE TABLE IF NOT EXISTS comentarios_por_partido (
    partido_id text,
    bucket_temporal text,
    creado_en timestamp,
    comentario_id uuid,
    usuario_id text,
    contenido text,
    estado_moderacion text,
    likes int,
    PRIMARY KEY ((partido_id, bucket_temporal), creado_en, comentario_id)
) WITH CLUSTERING ORDER BY (creado_en DESC, comentario_id ASC);
```
* **Clave de partición `(partido_id, bucket_temporal)`:** distribuye la carga de un mismo partido entre varias particiones a lo largo del encuentro, en vez de concentrarla en una sola.
* **Clustering `(creado_en DESC, comentario_id ASC)`:** ordena los comentarios del más reciente al más antiguo dentro de cada partición.

#### Tabla Secundaria: `comentarios_por_usuario` (PA3, duplicación controlada)
Para resolver el historial de un usuario sin recorrer particiones de distintos partidos (y sin `ALLOW FILTERING`), se duplica el comentario en una tabla orientada a usuario:

```cql
CREATE TABLE IF NOT EXISTS comentarios_por_usuario (
    usuario_id text,
    bucket_temporal text,
    creado_en timestamp,
    comentario_id uuid,
    partido_id text,
    contenido text,
    estado_moderacion text,
    likes int,
    PRIMARY KEY ((usuario_id, bucket_temporal), creado_en, comentario_id)
) WITH CLUSTERING ORDER BY (creado_en DESC, comentario_id ASC);
```
Acá `bucket_temporal` agrupa por mes (`AAAA-MM`): el volumen de comentarios de un único usuario es mucho menor que el de un partido, así que alcanza con una ventana más amplia.

---

### 3. Carga de Datos y Pruebas CQL (dataset mínimo)

```bash
# 1. Crear Keyspace y Tablas
docker exec -i fixture2030-cassandra cqlsh -f /scripts/esquema.cql

# 2. Cargar un dataset mínimo de ejemplo (3 comentarios)
docker exec -i fixture2030-cassandra cqlsh -f /scripts/carga_muestra.cql

# 3. Ejecutar operaciones CRUD y consultas de los patrones de acceso
docker exec -i fixture2030-cassandra cqlsh -f /scripts/crud.cql
docker exec -i fixture2030-cassandra cqlsh -f /scripts/consultas.cql
```

Estos scripts usan identificadores de ejemplo (`M001`, `U001`, etc.) para poder leerse y ejecutarse a mano, paso a paso — son independientes del dataset masivo de la sección siguiente.

---

### 4. Carga Masiva y Medición de Rendimiento (RF11, RF12 — 1.050.000 Comentarios)

El mecanismo real de carga masiva tiene dos pasos:

**Paso 1 — Generar el dataset reproducible.** `scripts/generar_comentarios.py` genera, con semilla fija (`SEED = 2030`), 1.050.000 comentarios sintéticos distribuidos en 100 partidos y 50.000 usuarios, y los escribe como dos archivos CSV (uno por tabla) en `data/`:

```bash
python3 scripts/generar_comentarios.py
```

**Paso 2 — Cargarlos a Cassandra con `COPY`.** `scripts/carga_masiva.cql` ejecuta el `COPY ... FROM` sobre cada CSV (montado en el contenedor en `/data`, ver `docker-compose.yml`):

```bash
docker exec -i fixture2030-cassandra cqlsh -f /scripts/carga_masiva.cql
```

#### Métrica y Resultados Observados
Evidencia completa, con fecha y versión de Cassandra registradas, en [`docs/rendimiento.md`](docs/rendimiento.md):
* **Volumen insertado:** 1.050.000 comentarios, cargados en cada una de las dos tablas.
* **`comentarios_por_partido`:** 43,9 segundos → **23.906 filas/s**.
* **`comentarios_por_usuario`:** 35,0 segundos → **30.006 filas/s**.
* Ambas tasas superan el objetivo de referencia de 10.000 escrituras/segundo del Hito 6.

> Estas son las únicas cifras de rendimiento válidas de este módulo. El método es siempre el mismo (`generar_comentarios.py` + `COPY`): no existe una medición alternativa con otra herramienta para este módulo.

---

### 5. Estructura de Archivos
```text
Cassandra/
├── docker-compose.yml          # Servicio Cassandra:latest + volumen nombrado (RNF2)
├── data/                       # CSV generados por generar_comentarios.py (no versionados)
├── scripts/
│   ├── esquema.cql             # Creación de KEYSPACE y TABLAS
│   ├── carga_muestra.cql       # Dataset mínimo de ejemplo (3 comentarios)
│   ├── crud.cql                # Sentencias de Insert, Select, Update, Delete
│   ├── consultas.cql           # Consultas PA1/PA2/PA3
│   ├── generar_comentarios.py  # Genera 1.050.000 comentarios reproducibles (CSV)
│   └── carga_masiva.cql        # COPY de los CSV generados hacia ambas tablas
├── docs/
│   ├── patrones_de_acceso.md              # Justificación de PA1/PA2/PA3
│   ├── modelo_tabular.md                  # Detalle de esquemas, tipos y claves primarias
│   ├── decisiones_de_particionamiento.md  # Estrategia de bucketing y hotspots
│   ├── rendimiento.md                     # Evidencia del benchmark y tasa de escritura
│   └── evidencia/                         # Capturas de pantalla (ambiente, CRUD, consultas, carga)
└── README.md                   # Instrucciones de ejecución (este archivo)
```

---

### 6. Limitaciones Conocidas
1. **Laboratorio de Nodo Único:** el entorno local ejecuta 1 solo nodo (`SimpleStrategy`, `replication_factor: 1`). No simula la tolerancia a fallas de un clúster multirregional productivo (`NetworkTopologyStrategy`).
2. **Generación Sintética:** los comentarios se generan con `random.seed(2030)` a partir de un conjunto fijo de frases de ejemplo (ver `TEXTOS` en `generar_comentarios.py`), no con texto libre ni con `Faker`; lo que sí se distribuye pseudoaleatoriamente de forma reproducible es el partido, el usuario, el estado de moderación y los likes de cada comentario.
3. **Límite de Hardware:** la velocidad de escritura medida depende de la CPU/SSD de la máquina donde se corrió la prueba (ver `docs/rendimiento.md`); no es una cota general del motor.
4. **Tombstones:** las operaciones de borrado (`DELETE`) generan registros tipo tombstone que impactan temporalmente la latencia hasta que el motor ejecuta la compactación (*compaction*).
