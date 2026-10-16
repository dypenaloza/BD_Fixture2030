#!/usr/bin/env bash
# Levanta la API REST del Fixture 2030 (requiere .env configurado y las
# 6 bases levantadas; ver docs/conectividad_y_configuracion.md).
set -euo pipefail

cd "$(dirname "$0")/.."

if [ ! -f .env ]; then
    echo "Falta .env. Copiar .env.example a .env y completar las credenciales." >&2
    exit 1
fi

exec uvicorn app.main:app --host 0.0.0.0 --port 8000
