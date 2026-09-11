# fixture2030-neo4j — Hito 5: Módulo de Grafos del Fixture 2030

**Grupo 12** · Ingeniería de Datos II, viernes turno noche
Integrantes: Dayana Peñaloza · Franco Churba · Juan Bautista Mangoni

Módulo de grafos de la plataforma del Mundial 2030, implementado sobre
**Neo4j** en Docker Compose. Representa las relaciones deportivas y de
programación del torneo —planteles, participación en partidos, sedes, fases y
eventos— y conserva la trazabilidad con los equipos y jugadores del
[módulo documental del Hito 4](../MongoDB).

| | |
|---|---|
| **Subgrafo cargado** | 2.528 nodos · 3.700 relaciones |
| **Entidades** | 64 selecciones · 1.536 jugadores · 128 partidos · 18 sedes · 753 eventos |
| **Etiquetas / relaciones** | 8 etiquetas de nodo · 9 tipos de relación |
| **Integridad** | 8 restricciones de unicidad · 8 índices propios (16 activos, contando los de respaldo de cada restricción) |
| **Ambiente validado** | 11/09/2026 — Neo4j 2026.07.1 Community (`neo4j:latest`), APOC 2026.07.1, GDS 2026.07.0 |

📄 **Documentación:** [modelo del grafo](docs/modelo_grafo.md) ·
[análisis y decisiones](docs/decisiones.md) ·
[evidencia técnica](docs/evidencia/)

---

## 1. Requisitos previos

- **Docker Desktop** (o Docker Engine + Compose v2) en la notebook.
- **Python 3.9+**, sólo si se quiere regenerar el dataset. Los CSV ya están
  versionados en `import/`, así que **no hace falta Python para levantar y
  cargar el módulo**. El generador no usa dependencias externas.
- Puertos **7474** y **7687** libres.

---

## 2. Puesta en marcha

### 2.1 Camino rápido

```bash
cp .env.example .env          # Windows PowerShell:  copy .env.example .env
./scripts/cargar.sh           # Windows PowerShell:  .\scripts\cargar.ps1
```

El script levanta el contenedor, espera a que Neo4j acepte consultas y ejecuta
en orden `estructura.cypher` → `carga.cypher` → `verificacion.cypher`. Al
terminar, **Neo4j Browser queda disponible en <http://localhost:7474>**.

Es idempotente: puede volver a ejecutarse cuantas veces se quiera.

### 2.2 Paso a paso

```bash
# 1. Credenciales locales (RNF8): se leen de .env, no están en el compose
cp .env.example .env

# 2. Levantar el ambiente
docker compose up -d
docker compose ps                      # STATUS debe decir "Up (healthy)"

# 3. Declarar restricciones e índices
docker compose exec neo4j cypher-shell -u neo4j -p fixture2030 -f /queries/estructura.cypher

# 4. Cargar el subgrafo (LOAD CSV + MERGE)
docker compose exec neo4j cypher-shell -u neo4j -p fixture2030 -f /queries/carga.cypher

# 5. Verificar la coherencia del resultado
docker compose exec neo4j cypher-shell -u neo4j -p fixture2030 -f /queries/verificacion.cypher
```

> **Git Bash en Windows:** convierte `/queries/...` en una ruta de Windows y el
> comando falla con *No such file or directory*. Ejecutar antes
> `export MSYS_NO_PATHCONV=1` (los scripts de `scripts/` ya lo hacen). En
> PowerShell y en Linux/macOS no hace falta.

### 2.3 Conexión

| Cliente | Acceso |
|---|---|
| **Neo4j Browser** | <http://localhost:7474> — usuario `neo4j`, contraseña la de `.env` (`fixture2030`) |
| **Bolt** (drivers, Neo4j Desktop) | `neo4j://localhost:7687` |
| **cypher-shell** | `docker compose exec neo4j cypher-shell -u neo4j -p fixture2030` |

### 2.4 Gestión del ambiente

```bash
docker compose stop      # detiene el contenedor; los datos persisten
docker compose start     # lo vuelve a levantar sobre los mismos datos
docker compose logs -f neo4j
docker compose down      # elimina el contenedor; LOS VOLÚMENES PERSISTEN
docker compose down -v   # ⚠️ elimina también los volúmenes: se pierden los datos
```

La persistencia se apoya en tres **volúmenes nombrados** —
`fixture2030_neo4j_data`, `_logs` y `_plugins` — comprobada en
[`docs/evidencia/10_persistencia_reinicio.txt`](docs/evidencia/10_persistencia_reinicio.txt):
los 2.528 nodos y las 8 restricciones sobreviven a un ciclo `stop`/`start`.

Para reconstruir todo desde cero: `docker compose down -v && ./scripts/cargar.sh`.

---

## 3. Uso: consultas y análisis

```bash
export MSYS_NO_PATHCONV=1   # sólo en Git Bash
CS="docker compose exec neo4j cypher-shell -u neo4j -p fixture2030"

$CS -f /queries/consultas_grafo.cypher      # RF8: 14 consultas con patrones
$CS -f /queries/consultas.cypher            # RF8: 8 consultas de planteles
$CS -f /queries/crud.cypher                 # RF7: alta, lectura, edición y borrado
$CS -f /queries/analisis_relacional.cypher  # RF9: camino, conectividad, centralidad
$CS -f /queries/verificacion.cypher         # RNF6/RNF7: controles de coherencia
```

También pueden copiarse los bloques en Neo4j Browser: las consultas 4.14 y las
de [`docs/evidencia/README.md`](docs/evidencia/README.md) están pensadas para la
vista **Graph**.

Para consultar el modelo tal como Neo4j lo ve:

```cypher
CALL db.schema.visualization()
```

---

## 4. El modelo en una pantalla

```
(:Jugador)-[:PERTENECE_A]->(:Seleccion)
(:Seleccion)-[:AFILIADO_A]->(:Confederacion)
(:Seleccion)-[:INTEGRA]->(:Grupo)
(:Seleccion)-[:PARTICIPA_EN {rol, goles, golesRecibidos, resultado}]->(:Partido)
(:Partido)-[:SE_JUEGA_EN]->(:Estadio)
(:Partido)-[:CORRESPONDE_A]->(:Fase)
(:Estadio)-[:EN_PAIS_DE]->(:Seleccion)
(:Evento)-[:OCURRE_EN]->(:Partido)
(:Evento)-[:PROTAGONIZADO_POR]->(:Jugador)
```

Identificadores **compartidos con el Hito 4**: `:Seleccion.seleccionId` es el `_id` de
la colección `equipos` (`ARG`) y `:Jugador.jugadorId` el de `jugadores`
(`ARG-10`). Detalle completo en [`docs/modelo_grafo.md`](docs/modelo_grafo.md).

---

## 5. Datos

El dataset está versionado en `import/*.csv`, generado con **semilla fija
`SEED = 2030`** —la misma del Hito 4—, por lo que es idéntico en cualquier
notebook. Equipos y jugadores **no se inventan**: se leen de los JSON del
módulo documental.

```bash
python import/generar_dataset.py     # regenerar (opcional)
```

Contiene el fixture completo de un Mundial de 64 equipos: 16 grupos de 4, 96
partidos de grupos y 32 de eliminatorias, con resultados simulados a partir del
ranking FIFA y con las eliminatorias armadas según las posiciones reales de
cada grupo. Los eventos (goles y tarjetas) son coherentes con cada marcador; el
generador aborta si algún control de coherencia falla.

En el torneo generado, **Uruguay se consagra campeón** venciendo 2-0 a Alemania
en el Santiago Bernabéu.

---

## 6. Estructura del repositorio

```
Neo4j/
├── docker-compose.yml              # Neo4j latest + volúmenes nombrados + healthcheck
├── .env.example                    # credenciales locales (copiar a .env)
├── data/                           # snapshot de equipos.json y jugadores.json (Hito 4)
├── import/                         # insumos de carga
│   ├── generar_dataset.py          # generador reproducible (lee los datos del Hito 4)
│   ├── selecciones.csv             # 64 selecciones
│   ├── jugadores.csv               # 1.536 jugadores
│   ├── estadios.csv                # 18 estadios
│   ├── partidos.csv                # 128 partidos
│   ├── participaciones.csv         # 256 participaciones
│   ├── eventos.csv                 # 753 eventos
│   └── confederaciones.csv, grupos.csv, fases.csv
├── queries/
│   ├── estructura.cypher           # RF10: restricciones de unicidad e índices
│   ├── carga.cypher                # RF6:  LOAD CSV + MERGE idempotente
│   ├── crud.cypher                 # RF7:  alta, lectura, edición y borrado acotado
│   ├── consultas_grafo.cypher      # RF8:  14 consultas con patrones y recorridos
│   ├── consultas.cypher            # RF8:  8 consultas de planteles (ver capturas)
│   ├── analisis_relacional.cypher  # RF9:  camino, conectividad y centralidad
│   └── verificacion.cypher         # RNF6/RNF7: controles de coherencia
├── scripts/
│   ├── cargar.sh / cargar.ps1      # puesta en marcha completa
│   └── generar_evidencia.sh        # regenera docs/evidencia/
├── docs/
│   ├── modelo_grafo.md             # etiquetas, propiedades, relaciones, cardinalidades
│   ├── decisiones.md               # análisis completo (7 apartados del enunciado)
│   └── evidencia/                  # 10 salidas de consola + 13 capturas del Browser
└── README.md
```

---

## 7. Cobertura de los requisitos

| Req. | Dónde se cumple |
|---|---|
| RF1 | `docker-compose.yml` · evidencia [01](docs/evidencia/01_ambiente_docker.txt) (HTTP 200 en 7474) |
| RF2 | [`docs/modelo_grafo.md`](docs/modelo_grafo.md) |
| RF3 | 8 etiquetas, justificadas en [`decisiones.md`](docs/decisiones.md) §3 |
| RF4 | `:PERTENECE_A`, `:PARTICIPA_EN`, `:SE_JUEGA_EN`, `:OCURRE_EN` |
| RF5 | `seleccionId` / `jugadorId` del Hito 4 · verificación 6.6 · evidencia [05](docs/evidencia/05_verificacion_coherencia.txt) |
| RF6 | `import/` — 64 equipos, 1.536 jugadores, 128 partidos, 18 sedes, 753 eventos |
| RF7 | [`queries/crud.cypher`](queries/crud.cypher) · evidencia [06](docs/evidencia/06_crud.txt) |
| RF8 | [`queries/consultas_grafo.cypher`](queries/consultas_grafo.cypher) — 6 consultas de 2+ saltos |
| RF9 | [`queries/analisis_relacional.cypher`](queries/analisis_relacional.cypher) · interpretación en [`decisiones.md`](docs/decisiones.md) §7 |
| RF10 | [`queries/estructura.cypher`](queries/estructura.cypher) · evidencia [09](docs/evidencia/09_rendimiento_indices.txt) |
| RF11 | [`docs/evidencia/`](docs/evidencia/) — 10 salidas de consola + 13 capturas de Neo4j Browser |
| RNF1 | `image: neo4j:latest`, sin versión fijada |
| RNF2 | Volúmenes nombrados · evidencia [10](docs/evidencia/10_persistencia_reinicio.txt) |
| RNF3 | Este README + `scripts/cargar.sh` · dataset con semilla fija |
| RNF4 | `MERGE` en toda la carga · evidencia [04](docs/evidencia/04_carga_idempotente.txt) |
| RNF5 | Archivos `.cypher` separados por propósito y comentados |
| RNF6 | Identificadores del Hito 4 · trazabilidad con los Hitos 1–3 en [`decisiones.md`](docs/decisiones.md) §3 D8 |
| RNF7 | [`queries/verificacion.cypher`](queries/verificacion.cypher) · evidencia [05](docs/evidencia/05_verificacion_coherencia.txt) |
| RNF8 | Credenciales por variables de entorno; `.env` excluido por `.gitignore` |

---

## 8. Diagnóstico de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| `No such file or directory: C:/Program Files/Git/queries/...` | Git Bash traduce las rutas del contenedor | `export MSYS_NO_PATHCONV=1` o usar PowerShell |
| El contenedor reinicia en bucle y el log repite `chown: ... Read-only file system` | El montaje de `./import` se declaró `:ro`; el entrypoint de Neo4j necesita escribir en él | Dejar `./import` **sin** `:ro` (así está en este compose) |
| `Couldn't load the external resource at: file:///selecciones.csv` | Los CSV no están en `import/` | `python import/generar_dataset.py` |
| Error de credenciales | `.env` cambió después de crear el volumen | `docker compose down -v && ./scripts/cargar.sh` (borra los datos) |
| Puerto 7474 o 7687 ocupado | Otro contenedor de Neo4j en ejecución | `docker ps` y detenerlo, o cambiar `NEO4J_HTTP_PORT` / `NEO4J_BOLT_PORT` en `.env` |
| `Unknown function 'gds.version'` | Los plugins todavía se están instalando en el primer arranque | Esperar a que `docker compose ps` diga `(healthy)` |

### Nota sobre `neo4j:latest`

El enunciado exige la etiqueta `latest`, que es móvil: el mismo compose puede
traer una versión distinta en otra fecha. Este módulo se validó el
**11/09/2026** con **Neo4j 2026.07.1 Community**
(digest `sha256:dbc377fb9cd8fe8dabc19d3041b197d5ca0ef8bae514cea175b8df265e5b7a76`),
APOC 2026.07.1 y GDS 2026.07.0. No se encontró ningún cambio incompatible; toda
la sintaxis Cypher usada es estándar y los algoritmos GDS se invocan con la API
de proyección por agregación, vigente en esa versión. Si una versión futura
rompiera algo, el digest permite reproducir el ambiente exacto reemplazando la
línea `image:` por `neo4j@sha256:dbc377...`.

---

## 9. Autoría dentro del módulo

| Aporte | Archivos |
|---|---|
| Modelo, carga, consultas de grafo, análisis relacional, verificación y documentación | `docker-compose.yml`, `import/`, `queries/` (salvo `consultas.cypher`), `scripts/`, `docs/modelo_grafo.md`, `docs/decisiones.md`, `docs/evidencia/*.txt` |
| Snapshot del Hito 4, consultas de planteles y capturas de Neo4j Browser | `data/`, `queries/consultas.cypher`, `docs/evidencia/*.png` |

`consultas.cypher` se validó contra el subgrafo final: sus resultados y sus
capturas coinciden con los datos cargados. Los scripts de carga de la primera
iteración (`constraints.cypher`, `carga_fixture.cypher`, `datos_prueba.cypher` y
`scripts/load_data.py`) quedaron reemplazados por `queries/estructura.cypher` y
`queries/carga.cypher`, que cargan el fixture completo de forma idempotente;
siguen disponibles en el historial de git.
