#!/usr/bin/env python3
"""
Verifica el estado de todos los targets de Prometheus (RF2/RF3) y, de
paso, de las alertas configuradas. No imprime secretos.

Uso: python3 scripts/verificar_targets.py [--prometheus-url http://localhost:9090]
"""

import sys
import json
import urllib.request


def obtener_json(url):
    with urllib.request.urlopen(url, timeout=5) as resp:
        return json.load(resp)


def main():

    base_url = "http://localhost:9090"

    for i, arg in enumerate(sys.argv):
        if arg == "--prometheus-url" and i + 1 < len(sys.argv):
            base_url = sys.argv[i + 1]

    try:
        targets = obtener_json(f"{base_url}/api/v1/targets")
    except Exception as error:
        print(f"No se pudo consultar Prometheus en {base_url}: {error}", file=sys.stderr)
        sys.exit(1)

    print("=== Targets ===")
    todo_ok = True

    for t in targets["data"]["activeTargets"]:
        job = t["labels"].get("job", "?")
        componente = t["labels"].get("componente", "")
        instance = t["labels"].get("instance", "?")
        salud = t["health"]
        todo_ok = todo_ok and (salud == "up")
        etiqueta = f"{job} ({componente})" if componente else job
        print(f"[{salud.upper():7}] {etiqueta:40} {instance}")

    print()
    print("=== Alertas ===")

    try:
        rules = obtener_json(f"{base_url}/api/v1/rules")
        for grupo in rules["data"]["groups"]:
            for regla in grupo["rules"]:
                if regla.get("type") != "alerting":
                    continue
                print(f"{regla['name']:30} estado={regla.get('state')}")
    except Exception as error:
        print(f"No se pudieron consultar las reglas: {error}", file=sys.stderr)

    sys.exit(0 if todo_ok else 1)


if __name__ == "__main__":
    main()
