#!/usr/bin/env bash
# Detiene el stack de monitoreo. Por defecto NO borra los volumenes de
# Prometheus/Grafana (historial de metricas y configuracion de Grafana).
# Pasar --volumenes para borrarlos tambien (nunca borra las 6 bases del
# Fixture ni sus datos: esto es exclusivamente el stack de monitoreo).
set -euo pipefail

cd "$(dirname "$0")/.."

if [[ "${1:-}" == "--volumenes" ]]; then
  docker compose down -v
  echo "Stack de monitoreo detenido y volumenes (Prometheus/Grafana) eliminados."
else
  docker compose down
  echo "Stack de monitoreo detenido. Volumenes conservados (usar --volumenes para borrarlos)."
fi
