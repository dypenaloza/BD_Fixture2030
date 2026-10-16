#!/usr/bin/env bash
# Corre los tests unitarios siempre, y los de integracion solo si la
# API responde en API_BASE_URL (default http://127.0.0.1:8000).
# Complementa a tests/pruebas_integracion.ps1 (Windows/PowerShell) con
# una suite multiplataforma.
set -euo pipefail

cd "$(dirname "$0")/.."

echo "--- Tests unitarios (no requieren bases levantadas) ---"
python3 -m pytest tests/unit/ -v

echo
echo "--- Tests de integracion (requieren las 6 bases + API arriba; se saltean si no responde) ---"
python3 -m pytest tests/integration/ -v
