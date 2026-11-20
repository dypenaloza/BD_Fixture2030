#!/usr/bin/env bash
# Prueba de falla controlada (RF10/RF20/RF21): detiene una dependencia,
# genera tráfico contra el endpoint que depende de ella, y la recupera.
# No borra volúmenes ni datos (RNF11).
#
# Uso: ./scripts/ejecutar_prueba_controlada.sh [contenedor] [endpoint]
# Por defecto usa Redis (igual que el Hito 11 y la evidencia en
# evidencia/prueba_de_falla.md).
set -euo pipefail

CONTENEDOR="${1:-fixture2030-redis}"
ENDPOINT="${2:-http://localhost:8000/sesiones/U27961}"
API_URL_BASE="${API_URL:-http://localhost:8000}"

echo "=== Condicion inicial ==="
date -u +%Y-%m-%dT%H:%M:%SZ
curl -s -w "\nHTTP %{http_code}\n" "$ENDPOINT" || true

echo
echo "=== Deteniendo $CONTENEDOR (reversible, sin tocar volumenes) ==="
docker stop "$CONTENEDOR"

echo
echo "=== Generando trafico de error (~60s) para poblar Prometheus/Grafana ==="
for _ in $(seq 1 20); do
  curl -s -o /dev/null -w "%{http_code} " "$ENDPOINT" || true
  sleep 3
done
echo

echo
echo "=== Recuperando $CONTENEDOR ==="
docker start "$CONTENEDOR"
sleep 3
curl -s -w "\nHTTP %{http_code}\n" "$ENDPOINT" || true

echo
echo "Revisar el dashboard de Grafana y la pagina /alerts de Prometheus"
echo "para ver la caida y la recuperacion reflejadas (puede demorar"
echo "hasta 2 intervalos de scraping, 20s, en reflejarse)."
