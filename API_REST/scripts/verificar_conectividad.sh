#!/usr/bin/env bash
# Wrapper del chequeo de conectividad (ver verificar_conectividad.py).
set -euo pipefail

cd "$(dirname "$0")/.."

python3 scripts/verificar_conectividad.py
