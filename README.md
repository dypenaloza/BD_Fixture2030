# BD_Fixture2030 — Hito 4: Módulo Documental (MongoDB)

**Grupo 12** · Ingeniería de Datos 2, Viernes turno noche.
Integrantes: Dayana Peñaloza · Franco Churba · Juan Bautista Mangoni.

Módulo documental de **Equipos (Selecciones)** y **Jugadores** del
Fixture del Mundial 2030, implementado sobre **MongoDB**. Ver el análisis
completo de decisiones en
[`Grupo_12_Hito_4_Decisiones_Documentales_Fixture2030.md`](Grupo_12_Hito_4_Decisiones_Documentales_Fixture2030.md)
y el diseño técnico detallado en [`docs/DISENO_DOCUMENTAL.md`](docs/DISENO_DOCUMENTAL.md).

## Requisitos

- Docker Desktop (o Docker Engine + Docker Compose Plugin v2) en la
  notebook de cualquier integrante.
- Python 3.9+ (solo para generar datos y ejecutar los scripts de
  carga/consultas; MongoDB en sí corre íntegramente en el contenedor).

## 1. Ambiente de ejecución

### Inicio

```bash
# 1. Abrir Docker Desktop
# 2. Desde la raíz del proyecto:
docker compose up -d
```

Esto crea, configura y levanta el contenedor `fixture2030-mongodb`
(MongoDB 7.x) con un volumen persistente y un healthcheck.

### Verificar que MongoDB está disponible

```bash
docker compose ps
# STATUS debe decir "Up ... (healthy)"

docker exec fixture2030-mongodb mongosh -u admin -p password123 \
  --authenticationDatabase admin --quiet --eval "db.adminCommand('ping')"
# { ok: 1 }
```


### Detener, reiniciar y recargar sin perder datos

```bash
docker compose stop      # detiene el contenedor, conserva el volumen
docker compose start     # lo vuelve a levantar sobre los mismos datos
docker compose restart   # equivalente a stop + start
```

El volumen nombrado `fixture2030_mongodb_data` almacena los archivos de
MongoDB fuera del ciclo de vida del contenedor: mientras no se borre
explícitamente, los datos sobreviven a `stop`/`restart`/`down` (sin
`-v`). Esto se verificó comparando el conteo de documentos antes y
después de un ciclo `stop` + `start` — evidencia en
[`evidencia/08_persistencia_stop_restart.txt`](evidencia/08_persistencia_stop_restart.txt).

```bash
docker compose down      # detiene y elimina el contenedor, EL VOLUMEN PERSISTE
docker compose down -v   # ⚠️ elimina también el volumen: se pierden los datos
```

Para "recargar" el ambiente completamente desde cero: `docker compose down -v`
seguido de `docker compose up -d` y del procedimiento de carga (sección 3).

> **Nota de red:** si `mongo:7` no puede descargarse por límites de
> Docker Hub, `docker-compose.yml` usa
> `mirror.gcr.io/library/mongo:7` (mismo binario oficial de MongoDB, vía
> el mirror público de Google). Si esa ruta tampoco está disponible en tu
> red, reemplazá la línea `image:` por `mongo:7`.

## 2. Instalación de dependencias Python

```bash
python3 -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## 3. Carga de datos

El dataset (64 selecciones + 1.500+ jugadores) ya está generado y versionado
en `data/equipos.json` y `data/jugadores.json` (generado con semilla fija,
100% reproducible). Para regenerarlo desde cero (opcional):

```bash
python3 data/generate_data.py
```

Para aplicar las validaciones documentales e índices, y luego cargar los
datos en MongoDB:

```bash
cd scripts
python3 setup_validations.py   # crea/actualiza validadores $jsonSchema e índices (idempotente)
python3 load_data.py           # carga 64 equipos + 1500+ jugadores (idempotente, sin duplicar)
```

`load_data.py` puede ejecutarse cualquier cantidad de veces: usa
`bulk_write` con `upsert` sobre el `_id` natural de cada documento, por lo
que reejecutarlo no genera duplicados ni inconsistencias (evidencia:
[`evidencia/03_carga_datos.txt`](evidencia/03_carga_datos.txt), que
muestra dos corridas consecutivas).

## 4. Ejecución de consultas y operaciones

Desde `scripts/`, con el entorno virtual activado:

```bash
python3 consultas_recuperacion.py     # RF10: id, filtros, proyección, orden + paginación
python3 consulta_agregacion.py        # RF11: pipelines de agregación
python3 operaciones_insert_update.py  # RF9: inserción y actualización (equipo y jugador)
python3 analisis_rendimiento.py       # RF12/RF13: explain() antes/después de indexar
```

Cada script imprime, para cada operación, su objetivo funcional y las
condiciones/campos usados, seguido del resultado real obtenido contra la
base ya cargada.

## 5. Estructura de archivos

```
BD_Fixture2030/
├── docker-compose.yml                 # MongoDB 7.x + volumen persistente + healthcheck
├── requirements.txt                   # pymongo, Faker
├── data/
│   ├── generate_data.py               # genera el dataset sintético (seed fija)
│   ├── equipos.json                   # 64 selecciones (generado)
│   └── jugadores.json                 # 1.536 jugadores (generado)
├── scripts/
│   ├── db.py                          # conexión centralizada a MongoDB
│   ├── setup_validations.py           # RF7 / RF12: $jsonSchema + índices
│   ├── load_data.py                   # RF4 / RF5 / RF8: carga idempotente
│   ├── consultas_recuperacion.py      # RF10
│   ├── consulta_agregacion.py         # RF11
│   ├── operaciones_insert_update.py   # RF9
│   └── analisis_rendimiento.py        # RF12 / RF13
├── docs/
│   └── DISENO_DOCUMENTAL.md           # esquemas, relación equipo-jugador, índices
├── evidencia/                         # salidas de consola reales de cada script
│   ├── 01_docker_compose_up.txt
│   ├── 02_validaciones_e_indices.txt
│   ├── 03_carga_datos.txt
│   ├── 04_consultas_recuperacion.txt
│   ├── 05_consulta_agregacion.txt
│   ├── 06_operaciones_insert_update.txt
│   ├── 07_analisis_rendimiento_indices.txt
│   ├── 08_persistencia_stop_restart.txt
│   └── 09_indices_y_validadores_final.txt
├── Grupo_12_Hito_4_Decisiones_Documentales_Fixture2030.md  # entregable de decisiones
└── README.md
```

## 6. Limitaciones conocidas

- Dataset sintético (generado con `Faker`, semilla fija `2030`); nombres
  de países y confederaciones son reales, jugadores no.
- No incluye API REST, interfaz gráfica ni la réplica multi-región
  descripta en el Hito 3 — fuera de alcance de este hito según los
  requisitos técnicos (foco exclusivo en MongoDB, documentos, carga y
  consultas).
- Credenciales de MongoDB (`admin` / `password123`, ver
  `docker-compose.yml`) son solo para desarrollo local.
- Detalle ampliado de limitaciones y trade-offs en la sección 7 de
  [`Grupo_12_Hito_4_Decisiones_Documentales_Fixture2030.md`](Grupo_12_Hito_4_Decisiones_Documentales_Fixture2030.md).
