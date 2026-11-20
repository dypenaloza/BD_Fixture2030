#!/usr/bin/env bash
# Levanta Prometheus, Grafana y los exporters (RF1).
# Requiere: las 6 bases y la API del Hito 10 ya corriendo (ver
# API_REST/docs/conectividad_y_configuracion.md y Requisitos_técnicos/README.md).
set -euo pipefail

cd "$(dirname "$0")/.."

docker compose up -d

echo
echo "Prometheus: http://localhost:9090"
echo "Grafana:    http://localhost:3000  (usuario: admin / password: ver GF_SECURITY_ADMIN_PASSWORD en docker-compose.yml)"
echo
echo "Verificar que todos los targets estén 'up' con: python3 scripts/verificar_targets.py"
