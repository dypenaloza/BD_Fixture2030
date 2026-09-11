#!/usr/bin/env bash
# =============================================================================
# Hito 5 — Fixture 2030 | Carga completa del subgrafo (Linux / macOS / Git Bash)
#
# Ejecuta, en orden: estructura -> carga -> verificación.
# Es idempotente: puede correrse tantas veces como se quiera.
#
# Uso, desde la raíz del módulo (fixture2030-neo4j):
#     ./scripts/cargar.sh
#     ./scripts/cargar.sh --regenerar     # regenera los CSV antes de cargar
# =============================================================================
set -euo pipefail

# Git Bash traduce las rutas tipo /queries/... a rutas de Windows. Esto lo evita.
export MSYS_NO_PATHCONV=1

# Ubicarse en la raíz del módulo, sin importar desde dónde se invoque.
cd "$(dirname "$0")/.."

# --- Credenciales: se leen de .env, nunca están escritas en el script --------
NEO4J_USER="neo4j"
NEO4J_PASSWORD="fixture2030"
if [ -f .env ]; then
  # shellcheck disable=SC1091
  set -a; . ./.env; set +a
else
  echo "AVISO: no existe .env; se usan los valores por defecto del compose."
fi

ejecutar_cypher() {
  echo
  echo "==> $1"
  docker compose exec -T neo4j cypher-shell \
    -u "$NEO4J_USER" -p "$NEO4J_PASSWORD" --format plain -f "/queries/$1"
}

# --- 0. Dataset ---------------------------------------------------------------
if [ "${1:-}" = "--regenerar" ]; then
  echo "==> Regenerando los CSV desde los datos del Hito 4"
  python import/generar_dataset.py
fi

# --- 1. Ambiente --------------------------------------------------------------
echo "==> Levantando el servicio Neo4j"
docker compose up -d

echo "==> Esperando a que Neo4j acepte consultas"
listo=0
for _ in $(seq 1 30); do
  estado="$(docker inspect --format '{{.State.Health.Status}}' fixture2030-neo4j 2>/dev/null || true)"
  if [ "$estado" = "healthy" ]; then listo=1; break; fi
  sleep 5
done
if [ "$listo" -ne 1 ]; then
  echo "ERROR: Neo4j no quedo disponible. Revisar: docker compose logs neo4j" >&2
  exit 1
fi
echo "    Neo4j disponible en http://localhost:7474"

# --- 2. Estructura, carga y verificación --------------------------------------
ejecutar_cypher "estructura.cypher"
ejecutar_cypher "carga.cypher"
ejecutar_cypher "verificacion.cypher"

echo
echo "Carga completa. Neo4j Browser: http://localhost:7474 (usuario: $NEO4J_USER)"
