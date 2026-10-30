import csv
import json
import time
import sys
import subprocess
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen
from concurrent.futures import ThreadPoolExecutor

# Configuración del escenario
URL = "http://127.0.0.1:8000/selecciones/ARG"
FASES = [
    ("rampa_2", 2, 5),
    ("rampa_5", 5, 5),
    ("sostenimiento", 10, 20),
]
INTERVALO = 0.5
TIMEOUT = 3

TIPO = sys.argv[1] if len(sys.argv) > 1 else "linea_base"

if TIPO not in ("linea_base", "optimizada"):
    raise ValueError("Usar linea_base u optimizada")


def solicitar(fase):
    inicio = time.perf_counter()
    codigo = 0
    error = ""

    try:
        with urlopen(URL, timeout=TIMEOUT) as respuesta:
            codigo = respuesta.status
            datos = json.loads(respuesta.read())

        correcto = codigo == 200 and datos.get("id") == "ARG"

        if not correcto:
            error = "respuesta_incorrecta"

    except Exception as e:
        correcto = False
        codigo = getattr(e, "code", 0)
        error = type(e).__name__

    return {
        "fase": fase,
        "latencia_ms": round(
            (time.perf_counter() - inicio) * 1000, 2
        ),
        "http": codigo,
        "correcto": correcto,
        "error": error
    }


def usuario(fase, duracion):
    resultados = []
    fin = time.perf_counter() + duracion

    while time.perf_counter() < fin:
        inicio = time.perf_counter()
        resultados.append(solicitar(fase))

        pausa = INTERVALO - (time.perf_counter() - inicio)

        if pausa > 0:
            time.sleep(min(pausa, max(0, fin - time.perf_counter())))

    return resultados


def percentil(valores, porcentaje):
    if not valores:
        return None

    valores = sorted(valores)
    posicion = (len(valores) - 1) * porcentaje
    inferior = int(posicion)
    superior = min(inferior + 1, len(valores) - 1)

    return round(
        valores[inferior]
        + (valores[superior] - valores[inferior])
        * (posicion - inferior), 2
    )


def resumir(resultados, duracion):
    latencias = [r["latencia_ms"] for r in resultados]

    return {
        "solicitudes": len(resultados),
        "exitos": sum(r["correcto"] for r in resultados),
        "errores": sum(not r["correcto"] for r in resultados),
        "latencia_promedio_ms": round(
            sum(latencias) / len(latencias), 2
        ) if latencias else None,
        "p50_ms": percentil(latencias, 0.50),
        "p95_ms": percentil(latencias, 0.95),
        "p99_ms": percentil(latencias, 0.99),
        "throughput_req_s": round(len(resultados) / duracion, 2)
    }


# Calentamiento: no se incluye en las mediciones
print("Calentando API...")

for _ in range(5):
    solicitar("calentamiento")

resultados = []
resumen_fases = {}

for nombre, concurrencia, duracion in FASES:
    print(f"Ejecutando {nombre}: {concurrencia} usuarios")

    inicio_fase = time.perf_counter()

    with ThreadPoolExecutor(max_workers=concurrencia) as executor:
        futuros = [
            executor.submit(usuario, nombre, duracion)
            for _ in range(concurrencia)
        ]

        for futuro in futuros:
            resultados.extend(futuro.result())

    tiempo_real = time.perf_counter() - inicio_fase

    resumen_fases[nombre] = {
        "usuarios": concurrencia,
        "duracion_s": round(tiempo_real, 2),
        **resumir(
            [r for r in resultados if r["fase"] == nombre],
            tiempo_real
        )
    }


# Guardar evidencia
carpeta = Path(__file__).resolve().parents[1] / "docs" / "evidencia"
carpeta.mkdir(parents=True, exist_ok=True)

with open(carpeta / f"{TIPO}.csv", "w", newline="", encoding="utf-8") as f:
    escritor = csv.DictWriter(f, fieldnames=resultados[0].keys())
    escritor.writeheader()
    escritor.writerows(resultados)

commit = subprocess.run(
    ["git", "rev-parse", "HEAD"],
    capture_output=True,
    text=True
).stdout.strip()

reporte = {
    "fecha": datetime.now().astimezone().isoformat(),
    "commit": commit,
    "endpoint": URL,
    "metodo": "GET",
    "timeout_s": TIMEOUT,
    "intervalo_por_usuario_s": INTERVALO,
    "calentamiento_solicitudes": 5,
    "fases": resumen_fases
}

with open(carpeta / f"{TIPO}.json", "w", encoding="utf-8") as f:
    json.dump(reporte, f, indent=4, ensure_ascii=False)

print("\nRESULTADOS:")
print(json.dumps(resumen_fases, indent=4, ensure_ascii=False))
print("\nEvidencia guardada correctamente.")