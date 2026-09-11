#!/usr/bin/env bash
# =============================================================================
# Hito 5 — Fixture 2030 | Captura de la evidencia técnica (RF11)
#
# Regenera docs/evidencia/ con la salida REAL de cada paso: ambiente, carga,
# idempotencia, verificación, CRUD, consultas, análisis y persistencia.
#
# Uso, desde la raíz del módulo (fixture2030-neo4j):
#     ./scripts/generar_evidencia.sh
#
# Requiere el ambiente ya cargado (./scripts/cargar.sh).
# =============================================================================
set -euo pipefail
export MSYS_NO_PATHCONV=1

cd "$(dirname "$0")/.."

NEO4J_USER="neo4j"
NEO4J_PASSWORD="fixture2030"
if [ -f .env ]; then set -a; . ./.env; set +a; fi

EV="docs/evidencia"
mkdir -p "$EV"

cypher() {
  docker compose exec -T neo4j cypher-shell \
    -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" --format plain "$@"
}

# Formato detallado: imprime el árbol de operadores del plan de ejecución,
# necesario para distinguir NodeIndexSeek de NodeByLabelScan.
cypher_verbose() {
  docker compose exec -T neo4j cypher-shell \
    -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" --format verbose "$@"
}

encabezado() {
  echo "==============================================================================="
  echo "$1"
  echo "Fixture 2030 — Hito 5 (Grupo 12) | Módulo de grafos en Neo4j"
  echo "Capturado: $(date '+%Y-%m-%d %H:%M:%S %Z')"
  echo "==============================================================================="
  echo
}

# -----------------------------------------------------------------------------
echo "==> 01 ambiente"
{
  encabezado "EVIDENCIA 01 — Ambiente local de Neo4j con Docker Compose (RF1, RNF1, RNF2)"
  echo "--- docker compose config: imagen declarada -----------------------------------"
  grep -n "image:" docker-compose.yml
  echo
  echo "--- docker compose ps ---------------------------------------------------------"
  docker compose ps
  echo
  echo "--- Version del servidor y edicion -------------------------------------------"
  cypher "CALL dbms.components() YIELD name, versions, edition RETURN name, versions, edition;"
  echo
  echo "--- Version de la imagen de Docker efectivamente descargada ------------------"
  docker image inspect neo4j:latest --format 'neo4j:latest -> {{index .RepoDigests 0}}'
  echo
  echo "--- Plugins disponibles (APOC y Graph Data Science) --------------------------"
  cypher "RETURN apoc.version() AS apoc, gds.version() AS gds;"
  echo
  echo "--- Volumenes nombrados de persistencia (RNF2) -------------------------------"
  docker volume ls --filter "name=fixture2030_neo4j"
  echo
  echo "--- Puertos publicados -------------------------------------------------------"
  docker compose port neo4j 7474
  docker compose port neo4j 7687
  echo
  echo "--- Neo4j Browser responde en HTTP (RF1) -------------------------------------"
  # Se usa wget DENTRO del contenedor (la imagen de Neo4j no trae curl, y el
  # curl de Git Bash sobre Windows falla con error de escritura cuando su
  # salida está redirigida a un archivo, lo que abortaría este script).
  docker compose exec -T neo4j wget -S -q -O /dev/null http://localhost:7474 2>&1 \
    | grep -E "HTTP/|Content-Type" || true
  echo
  echo "--- Endpoint de descubrimiento: URIs publicadas por el servidor --------------"
  docker compose exec -T neo4j wget -q -O - http://localhost:7474 || true
  echo
} > "$EV/01_ambiente_docker.txt" 2>&1

# -----------------------------------------------------------------------------
echo "==> 02 generacion del dataset"
{
  encabezado "EVIDENCIA 02 — Generación reproducible del dataset (RF6, RNF3)"
  echo "--- Primera corrida de import/generar_dataset.py -----------------------------"
  python import/generar_dataset.py
  echo
  echo "--- Huellas MD5 de los CSV generados -----------------------------------------"
  (cd import && md5sum ./*.csv)
  echo
  echo "--- Segunda corrida: misma semilla, mismo resultado --------------------------"
  python import/generar_dataset.py
  echo
  echo "--- Huellas MD5 tras la segunda corrida (deben ser IDENTICAS) ----------------"
  (cd import && md5sum ./*.csv)
} > "$EV/02_generacion_dataset.txt" 2>&1

# -----------------------------------------------------------------------------
echo "==> 03 estructura"
{
  encabezado "EVIDENCIA 03 — Restricciones de unicidad e índices (RF10)"
  cypher -f /queries/estructura.cypher
} > "$EV/03_estructura_restricciones_indices.txt" 2>&1

# -----------------------------------------------------------------------------
echo "==> 04 carga e idempotencia"
{
  encabezado "EVIDENCIA 04 — Carga del subgrafo e IDEMPOTENCIA (RF6, RNF4)"
  echo "El archivo queries/carga.cypher se ejecuta DOS VECES consecutivas sobre el"
  echo "mismo ambiente. Los conteos finales de nodos y relaciones deben ser idénticos"
  echo "en ambas corridas: eso demuestra que la carga no genera duplicados."
  echo
  echo "############################ PRIMERA CORRIDA #################################"
  time cypher -f /queries/carga.cypher
  echo
  echo "############################ SEGUNDA CORRIDA #################################"
  time cypher -f /queries/carga.cypher
  echo
  echo "--- Comparacion explicita ----------------------------------------------------"
  cypher "MATCH (n) WITH count(n) AS nodos MATCH ()-[r]->() RETURN nodos AS nodosTotales, count(r) AS relacionesTotales;"
  echo
  echo "--- Y ninguna relacion duplicada entre el mismo par de nodos -----------------"
  cypher "MATCH (a)-[r]->(b) WITH a, b, type(r) AS tipo, count(*) AS cantidad WHERE cantidad > 1 RETURN a, b, tipo, cantidad;"
  echo "(sin filas = no existen relaciones paralelas duplicadas)"
} > "$EV/04_carga_idempotente.txt" 2>&1

# -----------------------------------------------------------------------------
echo "==> 05 verificacion"
{
  encabezado "EVIDENCIA 05 — Verificación de coherencia del subgrafo (RNF6, RNF7)"
  echo "NOTA: los controles cuyo valor esperado es \"0 filas\" no imprimen salida"
  echo "cuando pasan. Ver los valores esperados en queries/verificacion.cypher."
  echo
  cypher -f /queries/verificacion.cypher
} > "$EV/05_verificacion_coherencia.txt" 2>&1

# -----------------------------------------------------------------------------
echo "==> 06 crud"
{
  encabezado "EVIDENCIA 06 — CRUD sobre el modelo (RF7)"
  echo "Crea un amistoso de prueba, lo actualiza, lo elimina con patrones acotados y"
  echo "comprueba que el subgrafo del torneo queda intacto (64/1536/128/18/753)."
  echo
  cypher -f /queries/crud.cypher
} > "$EV/06_crud.txt" 2>&1

# -----------------------------------------------------------------------------
echo "==> 07 consultas"
{
  encabezado "EVIDENCIA 07 — Consultas con patrones de grafo (RF8)"
  cypher -f /queries/consultas_grafo.cypher
} > "$EV/07_consultas_grafo.txt" 2>&1

# -----------------------------------------------------------------------------
echo "==> 08 analisis relacional"
{
  encabezado "EVIDENCIA 08 — Análisis relacional: camino, conectividad y centralidad (RF9)"
  cypher -f /queries/analisis_relacional.cypher
} > "$EV/08_analisis_relacional.txt" 2>&1

# -----------------------------------------------------------------------------
echo "==> 09 rendimiento de los indices"
{
  encabezado "EVIDENCIA 09 — Uso de índices en los recorridos frecuentes (RF10)"
  echo "PROFILE muestra el plan de ejecución real. Se busca ver NodeIndexSeek"
  echo "(búsqueda por índice) en lugar de NodeByLabelScan (recorrido completo)."
  echo
  echo "--- 9.1 Agenda del dia: usa el indice partido_fecha --------------------------"
  cypher_verbose "PROFILE MATCH (p:Partido {fecha: date('2030-06-13')})-[:SE_JUEGA_EN]->(s:Estadio) RETURN p.partidoId, s.nombre;"
  echo
  echo "--- 9.2 CONTRASTE: el mismo tipo de filtro sobre una propiedad SIN indice ----"
  echo "    (p.estado no tiene indice: el plan cae en NodeByLabelScan y multiplica"
  echo "     los accesos a base de datos frente a 9.1)"
  cypher_verbose "PROFILE MATCH (p:Partido) WHERE p.estado = 'finalizado' RETURN count(p);"
  echo
  echo "--- 9.3 Busqueda de un equipo por su identificador del Hito 4 ----------------"
  echo "    (restriccion de unicidad -> NodeUniqueIndexSeek)"
  cypher_verbose "PROFILE MATCH (e:Seleccion {seleccionId: 'URU'})<-[:PERTENECE_A]-(j:Jugador) RETURN count(j);"
  echo
  echo "--- 9.4 Goleadores: el indice evento_tipo acota antes de recorrer ------------"
  cypher_verbose "PROFILE MATCH (v:Evento {tipo: 'gol'})-[:PROTAGONIZADO_POR]->(j:Jugador)-[:PERTENECE_A]->(e:Seleccion) RETURN e.pais, count(v) AS goles ORDER BY goles DESC LIMIT 5;"
  echo
  echo "--- 9.5 Top de selecciones por ranking: indice equipo_ranking ----------------"
  cypher_verbose "PROFILE MATCH (e:Seleccion) WHERE e.ranking <= 10 RETURN e.pais, e.ranking ORDER BY e.ranking;"
} > "$EV/09_rendimiento_indices.txt" 2>&1

# -----------------------------------------------------------------------------
echo "==> 10 persistencia"
{
  encabezado "EVIDENCIA 10 — Persistencia en volúmenes nombrados (RNF2)"
  echo "--- Conteos ANTES de detener el contenedor -----------------------------------"
  cypher "MATCH (n) WITH count(n) AS nodos MATCH ()-[r]->() RETURN nodos AS nodosTotales, count(r) AS relacionesTotales;"
  echo
  echo "--- docker compose stop ------------------------------------------------------"
  docker compose stop
  docker compose ps -a
  echo
  echo "--- docker compose start -----------------------------------------------------"
  docker compose start
  echo "Esperando a que Neo4j vuelva a aceptar consultas..."
  for _ in $(seq 1 30); do
    estado="$(docker inspect --format '{{.State.Health.Status}}' fixture2030-neo4j 2>/dev/null || true)"
    if [ "$estado" = "healthy" ]; then break; fi
    sleep 5
  done
  docker compose ps
  echo
  echo "--- Conteos DESPUES del reinicio (deben ser los mismos) ----------------------"
  cypher "MATCH (n) WITH count(n) AS nodos MATCH ()-[r]->() RETURN nodos AS nodosTotales, count(r) AS relacionesTotales;"
  echo
  echo "--- Las restricciones e indices tambien persisten ----------------------------"
  cypher "SHOW CONSTRAINTS YIELD name RETURN count(*) AS restricciones;"
} > "$EV/10_persistencia_reinicio.txt" 2>&1

echo
echo "Evidencia regenerada en $EV:"
ls -1 "$EV"
