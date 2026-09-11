# Neo4j — Hito 5: Módulo de Grafos del Fixture 2030

Módulo de grafos de la plataforma del Mundial 2030, implementado sobre
**Neo4j** en Docker Compose. Representa las relaciones deportivas y de
programación del torneo —planteles, participación en partidos, sedes y
eventos— y conserva la trazabilidad con los equipos y jugadores del
[módulo documental del Hito 4](../MongoDB).

| | |
|---|---|
| **Subgrafo cargado** | 2335 nodos · 3102 relaciones |
| **Entidades** | 64 selecciones · 1536 jugadores · 16 sedes · 128 partidos · 591 eventos |
| **Etiquetas / relaciones** | 5 etiquetas de nodo · 5 tipos de relación |
| **Integridad** | 5 restricciones de unicidad · 4 índices propios (RF10) |

📄 **Documentación:** [modelo del grafo](docs/modelo_grafo.md) ·
[decisiones y cobertura de requisitos](docs/decisiones.md) ·
[evidencia técnica](evidencias/)

---

## 1. Requisitos previos

- **Docker Desktop** (o Docker Engine + Compose v2).
- **Python 3.9+** con los paquetes de `requirements.txt` (`neo4j`,
  `python-dotenv`), sólo para cargar los datos (equipos, jugadores y
  fixture). No hace falta para levantar el contenedor en sí.
- Puertos **7474** y **7687** libres (o cambiarlos en `.env`, ver más abajo).

---

## 2. Puesta en marcha

```bash
# 1. Credenciales y puertos locales (RNF8): se leen de .env, no están en el compose
cp .env.example .env          # Windows PowerShell: copy .env.example .env

# 2. Instalar dependencias de los scripts de carga
pip install -r requirements.txt

# 3. Levantar el ambiente
docker compose up -d
docker compose ps                      # STATUS debe decir "Up (healthy)"

# 4. Declarar restricciones e índices (RF10)
docker compose exec -T neo4j cypher-shell -u neo4j -p fixture2030 -f /dev/stdin < queries/constraints.cypher
docker compose exec -T neo4j cypher-shell -u neo4j -p fixture2030 -f /dev/stdin < queries/indices.cypher

# 5. Cargar equipos y jugadores (mismos identificadores del Hito 4)
python scripts/load_data.py

# 6. Generar y cargar el fixture (sedes, partidos, eventos) — RF6
python scripts/generar_fixture.py
```

Es idempotente: los pasos 4 a 6 pueden repetirse cuantas veces se quiera
(`MERGE` + `IF NOT EXISTS` en toda la carga) sin generar duplicados — ver
`evidencias/evidencia_carga_idempotente.txt`.

> Los pasos 4 usan `-f /dev/stdin < archivo` en vez de `-f /archivo` porque
> el compose de este módulo no monta `queries/` dentro del contenedor. Como
> alternativa, se puede copiar el archivo adentro con
> `docker compose cp queries/constraints.cypher neo4j:/tmp/constraints.cypher`
> y correr `cypher-shell -f /tmp/constraints.cypher`.

### 2.1 Conexión

| Cliente | Acceso |
|---|---|
| **Neo4j Browser** | <http://localhost:7474> — usuario `neo4j`, contraseña la de `.env` |
| **Bolt** (drivers, Neo4j Desktop) | `bolt://localhost:7687` |
| **cypher-shell** | `docker compose exec neo4j cypher-shell -u neo4j -p <password>` |

### 2.2 Gestión del ambiente

```bash
docker compose stop      # detiene el contenedor; los datos persisten
docker compose start     # lo vuelve a levantar sobre los mismos datos
docker compose logs -f neo4j
docker compose down      # elimina el contenedor; LOS VOLÚMENES PERSISTEN
docker compose down -v   # ⚠️ elimina también los volúmenes: se pierden los datos
```

La persistencia se apoya en cuatro **volúmenes nombrados**
(`neo4j_data`, `neo4j_logs`, `neo4j_import`, `neo4j_plugins`, prefijados con
el nombre del proyecto Compose) — RNF2.

Para reconstruir todo desde cero:
`docker compose down -v && docker compose up -d` y repetir los pasos 4-6.

---

## 3. Uso: consultas y análisis

```bash
CS="docker compose exec -T neo4j cypher-shell -u neo4j -p fixture2030"

$CS -f /dev/stdin < queries/consultas.cypher   # RF8: recuperación/agregación + 2 consultas multi-salto
$CS -f /dev/stdin < queries/crud.cypher        # RF7: alta, lectura, edición y baja
$CS -f /dev/stdin < queries/analisis.cypher    # RF9: camino, conectividad y centralidad
```

También pueden copiarse los bloques directamente en Neo4j Browser
(<http://localhost:7474>) para ver los resultados en la vista **Graph**.

Para ver el modelo tal como Neo4j lo interpreta:

```cypher
CALL db.schema.visualization()
```

---

## 4. El modelo en una pantalla

```
(:Jugador)-[:PERTENECE_A]->(:Seleccion)
(:Seleccion)-[:PARTICIPA_EN {rol, goles, golesRecibidos, resultado}]->(:Partido)
(:Partido)-[:SE_JUEGA_EN]->(:Estadio)
(:Evento)-[:OCURRE_EN]->(:Partido)
(:Evento)-[:PROTAGONIZADO_POR]->(:Jugador)
```

Identificadores **compartidos con el Hito 4**: `:Seleccion.seleccionId` es el
`_id` de la colección `equipos` (ej. `"ARG"`) y `:Jugador.jugadorId` el de
`jugadores` (ej. `"ARG-10"`). Detalle completo, incluidas cardinalidades y
justificación de cada decisión, en [`docs/modelo_grafo.md`](docs/modelo_grafo.md)
y [`docs/decisiones.md`](docs/decisiones.md).

---

## 5. Datos

- **Equipos y jugadores:** `data/equipos.json` (64 selecciones) y
  `data/jugadores.json` (1536 jugadores, 24 por selección) — los mismos
  archivos del módulo documental del Hito 4. No se inventan datos: se leen
  tal cual con `scripts/load_data.py`.
- **Fixture (sedes, partidos, eventos):** generado de forma determinística y
  reproducible por `scripts/generar_fixture.py` (semilla fija `SEED = 2030`):
  16 sedes repartidas entre los seis países anfitriones del Mundial 2030
  (Argentina, Uruguay, Paraguay, España, Portugal, Marruecos); fase de
  grupos completa (round-robin sobre los 16 grupos ya cargados, 96
  partidos) con resultados simulados según el ranking FIFA de cada
  selección; eliminatorias completas a partir de la tabla de posiciones real
  de cada grupo (dieciseisavos → octavos → cuartos → semifinal → tercer
  puesto y final, 32 partidos); y eventos (goles y tarjetas) coherentes con
  cada marcador. Detalle completo de la lógica de generación y de los
  controles de coherencia aplicados en [`docs/decisiones.md`](docs/decisiones.md) §4.

---

## 6. Estructura del repositorio

```
Neo4j/
├── docker-compose.yml               # Neo4j latest + volúmenes nombrados + healthcheck
├── .env.example                     # credenciales/puertos locales (copiar a .env) — RNF8
├── requirements.txt                 # dependencias de los scripts de carga
├── data/
│   ├── equipos.json                 # 64 selecciones (mismos IDs del Hito 4)
│   └── jugadores.json               # 1536 jugadores (mismos IDs del Hito 4)
├── scripts/
│   ├── load_data.py                 # RF6: carga selecciones + jugadores (idempotente)
│   └── generar_fixture.py           # RF6: genera y carga sedes, partidos y eventos
├── queries/
│   ├── constraints.cypher           # RF10: restricciones de unicidad
│   ├── indices.cypher                # RF10: índices + SHOW CONSTRAINTS/INDEXES
│   ├── crud.cypher                  # RF7: alta, lectura, edición y baja
│   ├── consultas.cypher             # RF8: recuperación/agregación + 2 consultas multi-salto
│   ├── analisis.cypher              # RF9: camino, conectividad y centralidad
│   ├── datos_prueba.cypher          # histórico: primer boceto manual (superado por load_data.py)
│   └── carga_fixture.cypher         # histórico: primer boceto manual (superado por generar_fixture.py)
├── docs/
│   ├── modelo_grafo.md              # etiquetas, propiedades, relaciones, cardinalidades
│   └── decisiones.md                # problema, modelo, decisiones, datos, consultas, integridad, análisis
├── evidencias/                      # capturas de Neo4j Browser + evidencia de texto de cada RF
└── README.md
```

---

## 7. Limitaciones y notas sobre `neo4j:latest`

- El enunciado exige la etiqueta `latest`, que es móvil: el mismo compose
  puede traer una versión distinta en otra fecha. Este módulo se validó el
  **11/09/2026**. Si una versión futura de la imagen rompiera algo
  incompatible, reemplazar temporalmente `image: neo4j:latest` por una
  versión fija y dejarlo documentado acá.
- El fixture (partidos/eventos) es **simulado**, no el resultado real de un
  Mundial 2030: sirve para tener una muestra completa y coherente (fase de
  grupos + eliminatorias enteras) que valide todos los recorridos exigidos,
  no como predicción deportiva.
- No se integra por código con el módulo MongoDB (no lo exige el enunciado):
  la coherencia entre ambos es semántica y de identificadores (RF5), no una
  integración en tiempo de ejecución.

---

## 8. Diagnóstico de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| `Couldn't load the external resource` al copiar `.cypher` | El archivo no llegó al contenedor | Usar `-f /dev/stdin < archivo` (ver §2) o `docker compose cp` |
| Error de credenciales al conectar | `.env` cambió después de crear el volumen | `docker compose down -v && docker compose up -d` (borra los datos) y volver a cargar |
| Puerto 7474 o 7687 ocupado | Otro contenedor de Neo4j en ejecución | `docker ps` y detenerlo, o cambiar `NEO4J_HTTP_PORT`/`NEO4J_BOLT_PORT` en `.env` |
| `ModuleNotFoundError: No module named 'neo4j'` | Faltan dependencias de los scripts | `pip install -r requirements.txt` |
| `KeyError: 'NEO4J_PASSWORD'` al correr un script | No existe `.env` | `cp .env.example .env` |
