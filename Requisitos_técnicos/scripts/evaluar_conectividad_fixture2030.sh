#!/usr/bin/env bash
# Hito 11 — Adaptación para el repositorio BD_Fixture2030 (basada en el script de Clase 12)
#
# Este script NO crea, modifica ni elimina datos. Realiza:
#   1) una prueba TCP opcional;
#   2) una prueba HTTP donde corresponde;
#   3) una lectura mínima con clientes nativos si están instalados;
#   4) una prueba de endpoints de la API integrada del Hito 10.
#
# Pensado para macOS/Linux/WSL/Git Bash con Docker Desktop.
# Si la API corre dentro de Docker, reemplazar los hosts por los nombres de
# servicio de la red Compose y ejecutar desde el mismo entorno de red.

set -u

API_URL="${API_URL:-http://127.0.0.1:8000}"
MONGO_HOST="${MONGO_HOST:-127.0.0.1}"
MONGO_PORT="${MONGO_PORT:-27017}"
MONGO_DATABASE="${MONGO_DATABASE:-fixture2030}"
NEO4J_HOST="${NEO4J_HOST:-127.0.0.1}"
NEO4J_BOLT_PORT="${NEO4J_BOLT_PORT:-7687}"
NEO4J_HTTP_PORT="${NEO4J_HTTP_PORT:-7474}"
CASSANDRA_HOST="${CASSANDRA_HOST:-127.0.0.1}"
CASSANDRA_PORT="${CASSANDRA_PORT:-9042}"
CASSANDRA_KEYSPACE="${CASSANDRA_KEYSPACE:-fixture2030}"
REDIS_HOST="${REDIS_HOST:-127.0.0.1}"
REDIS_PORT="${REDIS_PORT:-6379}"
INFLUX_URL="${INFLUX_URL:-http://127.0.0.1:8181}"
INFLUX_HOST="${INFLUX_HOST:-127.0.0.1}"
INFLUX_PORT="${INFLUX_PORT:-8181}"
IRIS_HOST="${IRIS_HOST:-127.0.0.1}"
IRIS_PORT="${IRIS_PORT:-1972}"
IRIS_PORTAL_URL="${IRIS_PORTAL_URL:-http://localhost:52773}"
CONNECT_TIMEOUT="${CONNECT_TIMEOUT:-3}"
API_TIMEOUT="${API_TIMEOUT:-5}"

MODE="all"
case "${1:-}" in
  --api-only) MODE="api" ;;
  --tcp-only) MODE="tcp" ;;
  --native-only) MODE="native" ;;
  --help|-h)
    cat <<'USAGE'
Uso:
  ./evaluar_conectividad_fixture2030.sh                todas las pruebas disponibles
  ./evaluar_conectividad_fixture2030.sh --tcp-only     solo resolución/puertos TCP
  ./evaluar_conectividad_fixture2030.sh --native-only  solo clientes nativos disponibles
  ./evaluar_conectividad_fixture2030.sh --api-only     solo endpoints de la API

Variables útiles:
  API_URL=http://localhost:8000
  CONNECT_TIMEOUT=3 API_TIMEOUT=5
  MONGO_HOST=127.0.0.1 MONGO_PORT=27017 (Mongo nativo requiere MONGO_USER y MONGO_PASSWORD)
  NEO4J_HOST=127.0.0.1 NEO4J_BOLT_PORT=7687 NEO4J_HTTP_PORT=7474
  CASSANDRA_HOST=127.0.0.1 CASSANDRA_PORT=9042
  REDIS_HOST=127.0.0.1 REDIS_PORT=6379
  INFLUX_URL=http://127.0.0.1:8181
  IRIS_HOST=127.0.0.1 IRIS_PORT=1972 IRIS_PORTAL_URL=http://127.0.0.1:52773

El script no recibe passwords por argumentos y no imprime secretos.
USAGE
    exit 0
    ;;
  "") ;;
  *) echo "Argumento desconocido: $1. Usar --help." >&2; exit 2 ;;
esac

TOTAL=0
OK=0
WARN=0
FAIL=0
SKIP=0

now() { date '+%Y-%m-%dT%H:%M:%S%z'; }

record() {
  local status="$1" name="$2" detail="$3"
  TOTAL=$((TOTAL + 1))
  case "$status" in
    OK) OK=$((OK + 1)); printf '[OK]   %-30s %s\n' "$name" "$detail" ;;
    WARN) WARN=$((WARN + 1)); printf '[WARN] %-30s %s\n' "$name" "$detail" ;;
    FAIL) FAIL=$((FAIL + 1)); printf '[FAIL] %-30s %s\n' "$name" "$detail" ;;
    SKIP) SKIP=$((SKIP + 1)); printf '[SKIP] %-30s %s\n' "$name" "$detail" ;;
  esac
}

have() { command -v "$1" >/dev/null 2>&1; }

PYTHON_FALLBACK="$(dirname "$0")/chequeo_nativo_python.py"

# Cuando la CLI del producto no esta instalada (frecuente en Windows sin
# WSL), usa los mismos drivers Python que ya requiere la API del Hito 10
# en vez de dejar la capa nativa sin evaluar (RNF4: no se acepta un unico
# chequeo HTTP generico como reemplazo de la verificacion nativa real).
native_fallback_python() {
  local nombre="$1" producto="$2"
  if ! have python3 || [[ ! -f "$PYTHON_FALLBACK" ]]; then
    record SKIP "$nombre nativo" "CLI no instalada y python3/$PYTHON_FALLBACK no disponible"
    return
  fi
  local salida estado
  salida="$(python3 "$PYTHON_FALLBACK" "$producto" 2>&1)"
  estado="${salida%% *}"
  case "$estado" in
    OK) record OK "$nombre nativo (python)" "${salida#OK }" ;;
    FAIL) record FAIL "$nombre nativo (python)" "${salida#FAIL }" ;;
    SKIP) record SKIP "$nombre nativo (python)" "${salida#SKIP }" ;;
    *) record SKIP "$nombre nativo (python)" "salida inesperada del chequeo python" ;;
  esac
}

check_tcp() {
  local name="$1" host="$2" port="$3"
  if have nc; then
    if nc -z -w "$CONNECT_TIMEOUT" "$host" "$port" >/dev/null 2>&1; then
      record OK "$name TCP $host:$port" "listener alcanzable"
    else
      record FAIL "$name TCP $host:$port" "sin conexión; revisar host, puerto, red o contenedor"
    fi
  elif have timeout && have bash; then
    if timeout "$CONNECT_TIMEOUT" bash -c "</dev/tcp/$host/$port" >/dev/null 2>&1; then
      record OK "$name TCP $host:$port" "listener alcanzable (bash TCP)"
    else
      record FAIL "$name TCP $host:$port" "sin conexión; revisar host, puerto, red o contenedor"
    fi
  else
    record SKIP "$name TCP $host:$port" "se necesita nc o bash con /dev/tcp"
  fi
}

check_http() {
  local name="$1" url="$2"
  if ! have curl; then
    record SKIP "$name HTTP" "curl no está instalado"
    return
  fi
  local code
  code="$(curl -k -L -sS -o /dev/null -w '%{http_code}' --connect-timeout "$CONNECT_TIMEOUT" --max-time "$API_TIMEOUT" "$url" 2>/dev/null || true)"
  if [[ "$code" =~ ^2|^3 ]]; then
    record OK "$name HTTP" "$url respondió HTTP $code"
  elif [[ "$code" == "000" || -z "$code" ]]; then
    record FAIL "$name HTTP" "no se obtuvo respuesta; revisar URL, puerto y servicio"
  else
    record WARN "$name HTTP" "$url respondió HTTP $code; el servicio es alcanzable"
  fi
}

native_mongodb() {
  if ! have mongosh; then
    native_fallback_python "MongoDB" "mongodb"
    return
  fi
  if [[ -z "${MONGO_PASSWORD:-}" ]]; then
    record SKIP "MongoDB nativo" "configurar MONGO_USER y MONGO_PASSWORD en el entorno local (no en el script)"
    return
  fi
  local uri="mongodb://${MONGO_HOST}:${MONGO_PORT}/${MONGO_DATABASE}"
  # Autenticar contra admin usando variables de entorno heredadas por mongosh;
  # evitar imprimir o incluir la contraseña en la línea de comandos.
  if MONGO_USER="${MONGO_USER:-admin}" MONGO_PASSWORD="$MONGO_PASSWORD" \
      mongosh "$uri" --quiet --eval '        try {          const auth = db.getSiblingDB("admin").auth(process.env.MONGO_USER, process.env.MONGO_PASSWORD);          if (!auth || (auth !== true && auth.ok !== 1)) quit(1);          if (db.runCommand({ping: 1}).ok !== 1) quit(1);          quit(0);        } catch(e) { quit(1); }      ' >/dev/null 2>&1; then
    record OK "MongoDB nativo" "autenticación y ping correctos en ${MONGO_DATABASE}"
  else
    record FAIL "MongoDB nativo" "falló autenticación, contexto o ping; revisar configuración sin mostrar secretos"
  fi
}

native_neo4j() {
  if ! have cypher-shell; then
    native_fallback_python "Neo4j" "neo4j"
    return
  fi
  local user="${NEO4J_USER:-neo4j}"
  local pass="${NEO4J_PASSWORD:-}"
  if [[ -z "$pass" ]]; then
    record SKIP "Neo4j nativo" "definir NEO4J_PASSWORD localmente para cypher-shell"
    return
  fi
  if cypher-shell -a "bolt://${NEO4J_HOST}:${NEO4J_BOLT_PORT}" -u "$user" -p "$pass" 'RETURN 1 AS connectivity' >/dev/null 2>&1; then
    record OK "Neo4j nativo" "sesión Bolt y lectura mínima correctas"
  else
    record FAIL "Neo4j nativo" "falló Bolt/autenticación/lectura; revisar usuario, password y base"
  fi
}

native_cassandra() {
  if ! have cqlsh; then
    native_fallback_python "Cassandra" "cassandra"
    return
  fi
  if cqlsh "$CASSANDRA_HOST" "$CASSANDRA_PORT" -e "USE ${CASSANDRA_KEYSPACE}; SELECT comentario_id, usuario_id FROM comentarios_por_partido WHERE partido_id = 'M001' AND bucket_temporal = '20:00-20:05' LIMIT 1;" >/dev/null 2>&1; then
    record OK "Cassandra nativo" "keyspace ${CASSANDRA_KEYSPACE} y lectura limitada correctos"
  else
    record FAIL "Cassandra nativo" "no se pudo seleccionar keyspace o ejecutar SELECT limitado"
  fi
}

native_redis() {
  if ! have redis-cli; then
    native_fallback_python "Redis" "redis"
    return
  fi
  local result
  result="$(redis-cli -h "$REDIS_HOST" -p "$REDIS_PORT" --raw PING 2>/dev/null || true)"
  if [[ "$result" == "PONG" ]]; then
    record OK "Redis nativo" "PING/PONG correctos"
  elif [[ -n "$result" ]]; then
    record FAIL "Redis nativo" "respuesta recibida pero no fue PONG: $result"
  else
    record FAIL "Redis nativo" "no se obtuvo PONG"
  fi
}

native_influx() {
  # InfluxDB 3 Core expone HTTP; el endpoint de health no modifica datos.
  check_http "InfluxDB health" "${INFLUX_URL%/}/health"
}

native_iris() {
  check_http "IRIS portal" "$IRIS_PORTAL_URL"
  # check_tcp ya tiene su propio fallback por /dev/tcp de bash cuando no
  # hay nc instalado: no hace falta (ni conviene) duplicar esa condicion
  # aca, para no generar un SKIP evitable.
  check_tcp "IRIS Superserver" "$IRIS_HOST" "$IRIS_PORT"
}

api_get() {
  # $3 (opcional): codigo HTTP esperado para este caso (ej. "400" para
  # un caso de validacion, "404" para un recurso que debe no existir).
  # Si se pasa, un codigo distinto al esperado es FAIL, no WARN: estamos
  # probando un escenario puntual, no "a ver que devuelve".
  local name="$1" path="$2" esperado="${3:-}"
  if ! have curl; then
    record SKIP "API $name" "curl no está instalado"
    return
  fi
  local body_file headers_file code duracion_ms request_id
  body_file="/tmp/fixture2030-api-response.$$"
  headers_file="/tmp/fixture2030-api-headers.$$"
  local inicio_ms fin_ms
  inicio_ms=$(($(date +%s%N) / 1000000))
  code="$(curl -k -sS -D "$headers_file" -o "$body_file" -w '%{http_code}' --connect-timeout "$CONNECT_TIMEOUT" --max-time "$API_TIMEOUT" "${API_URL%/}$path" 2>/dev/null || true)"
  fin_ms=$(($(date +%s%N) / 1000000))
  duracion_ms=$((fin_ms - inicio_ms))
  request_id="$(grep -i '^x-request-id:' "$headers_file" 2>/dev/null | tr -d '\r' | cut -d' ' -f2)"
  rm -f "$body_file" "$headers_file"

  local detalle="HTTP $code en $path, ${duracion_ms}ms, request_id=${request_id:-N/D}"

  if [[ -n "$esperado" ]]; then
    if [[ "$code" == "$esperado" ]]; then
      record OK "API $name" "$detalle (resultado esperado)"
    elif [[ "$code" == "000" || -z "$code" ]]; then
      record FAIL "API $name" "API no alcanzable en ${API_URL%/}$path (se esperaba HTTP $esperado)"
    else
      record FAIL "API $name" "$detalle (se esperaba HTTP $esperado)"
    fi
    return
  fi

  if [[ "$code" =~ ^2 ]]; then
    record OK "API $name" "$detalle"
  elif [[ "$code" == "404" ]]; then
    record WARN "API $name" "API alcanzable; recurso no encontrado. $detalle"
  elif [[ "$code" == "000" || -z "$code" ]]; then
    record FAIL "API $name" "API no alcanzable en ${API_URL%/}$path"
  elif [[ "$code" == "503" || "$code" == "502" ]]; then
    record WARN "API $name" "API alcanzable con dependencia fallida. $detalle"
  else
    record WARN "API $name" "API alcanzable; respondió HTTP $code. $detalle"
  fi
}

printf '\nHito 11 — Evaluación de conectividad Fixture 2030\n'
printf 'Inicio: %s\n' "$(now)"
printf 'Modo: %s | API: %s\n\n' "$MODE" "$API_URL"

if [[ "$MODE" == "all" || "$MODE" == "tcp" ]]; then
  printf '%s\n' '--- 1. TCP / puertos ---'
  check_tcp MongoDB "$MONGO_HOST" "$MONGO_PORT"
  check_tcp Neo4j-Bolt "$NEO4J_HOST" "$NEO4J_BOLT_PORT"
  check_tcp Cassandra "$CASSANDRA_HOST" "$CASSANDRA_PORT"
  check_tcp Redis "$REDIS_HOST" "$REDIS_PORT"
  check_tcp InfluxDB "$INFLUX_HOST" "$INFLUX_PORT"
  check_tcp IRIS "$IRIS_HOST" "$IRIS_PORT"
  printf '\n'
fi

if [[ "$MODE" == "all" || "$MODE" == "native" ]]; then
  printf '%s\n' '--- 2. HTTP / clientes nativos ---'
  check_http "Neo4j Browser" "http://${NEO4J_HOST}:${NEO4J_HTTP_PORT}"
  native_mongodb
  native_neo4j
  native_cassandra
  native_redis
  native_influx
  native_iris
  printf '\n'
fi

if [[ "$MODE" == "all" || "$MODE" == "api" ]]; then
  printf '%s\n' '--- 3. API integrada del Hito 10 ---'
  api_get 'MongoDB / selección' '/selecciones/ARG'
  api_get 'Neo4j / eventos' '/partidos/P-A-1/eventos?limit=5'
  api_get 'Cassandra / comentarios' '/partidos/M001/comentarios?bucket_temporal=20%3A00-20%3A05&limit=5'
  api_get 'Redis / sesión' '/sesiones/U27961'
  api_get 'InfluxDB / estadísticas' '/partidos/M001/estadisticas?equipo_id=ARG&desde=2030-10-08T08%3A00%3A00Z&hasta=2030-10-08T08%3A30%3A00Z&limit=5'
  api_get 'IRIS / detalle' '/partidos/M004/detalle'
  printf '\n'

  printf '%s\n' '--- 3b. API: casos de error y de borde (RF18) ---'
  # Error de validacion (400): codigo con formato invalido, nunca llega
  # a tocar la base (se verifica ANTES de la capa 6 "operacion").
  api_get 'MongoDB / codigo invalido' '/selecciones/1234' '400'
  # Error de validacion (400): formato de Cassandra usado donde se
  # espera el de Neo4j (bug real encontrado y corregido en el Hito 10).
  api_get 'Neo4j / id con formato de Cassandra' '/partidos/M001/eventos' '400'
  # Respuesta vacia valida (200): particion real sin comentarios no es
  # lo mismo que "Cassandra caida"; debe distinguirse del 503.
  api_get 'Cassandra / particion sin comentarios' '/partidos/M001/comentarios?bucket_temporal=00%3A00-00%3A05&limit=5' '200'
  # Recurso inexistente (404): codigo con formato valido que no existe
  # en IRIS.
  api_get 'IRIS / partido inexistente' '/partidos/Z999/detalle' '404'
  printf '\n'
fi

printf '%s\n' '--- Resumen ---'
printf 'Total: %d | OK: %d | WARN: %d | FAIL: %d | SKIP: %d\n' "$TOTAL" "$OK" "$WARN" "$FAIL" "$SKIP"
printf 'Fin: %s\n' "$(now)"
printf '\nInterpretación: OK no garantiza rendimiento masivo; indica que la prueba de esa capa fue exitosa.\n'
printf 'Las pruebas nativas y de API deben contrastarse con logs y contexto, sin exponer secretos.\n'

# No se fuerza un exit 1 ante un producto caído: en clase se necesita ver el
# diagnóstico completo. Para automatización CI, agregar una política explícita.
exit 0
