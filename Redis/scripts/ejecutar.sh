#!/usr/bin/env bash
# =============================================================================
# Ejecuta un archivo .redis contra el contenedor fixture2030-redis.
#
# redis-cli, a diferencia de cypher-shell o cqlsh, no sabe interpretar
# comentarios "#" cuando lee comandos desde stdin: los trata como un
# comando desconocido y falla. Este wrapper filtra los comentarios y las
# líneas vacías antes de pasarle el archivo, para poder mantener los
# scripts .redis comentados (RNF9) sin que eso rompa la ejecución
# automática.
#
# Uso:
#   ./scripts/ejecutar.sh scripts/sesiones.redis
# =============================================================================
set -euo pipefail

if [ $# -ne 1 ]; then
  echo "Uso: $0 <archivo.redis>" >&2
  exit 1
fi

grep -v '^#' "$1" | grep -v '^[[:space:]]*$' | docker exec -i fixture2030-redis redis-cli
