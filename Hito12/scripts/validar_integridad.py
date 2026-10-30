import json
import sys
from datetime import datetime
from pathlib import Path
from urllib.request import urlopen

RAIZ = Path(__file__).resolve().parents[2]

sys.path.insert(0, str(RAIZ / "API_REST"))

from app.adapters import mongo_adapter

URL = "http://127.0.0.1:8000/selecciones/ARG"

# Obtener respuesta desde la API
with urlopen(URL, timeout=3) as respuesta:
    codigo_http = respuesta.status
    datos_api = json.load(respuesta)

# Consultar directamente MongoDB
try:
    datos_mongo = mongo_adapter.buscar_seleccion("ARG")
finally:
    mongo_adapter.cerrar_cliente()

# Verificar integridad
coinciden = datos_api == datos_mongo

resultado = {
    "fecha": datetime.now().astimezone().isoformat(),
    "endpoint": URL,
    "codigo_http": codigo_http,
    "identificador_correcto": datos_api.get("id") == "ARG",
    "coincidencia_completa": coinciden,
    "campos_verificados": sorted(datos_api.keys()),
    "integridad_correcta": (
        codigo_http == 200
        and datos_api.get("id") == "ARG"
        and coinciden
    )
}

# Guardar evidencia
carpeta = RAIZ / "Hito12" / "docs" / "evidencia"
carpeta.mkdir(parents=True, exist_ok=True)

archivo = carpeta / "validacion_integridad.json"

with open(archivo, "w", encoding="utf-8") as f:
    json.dump(resultado, f, indent=4, ensure_ascii=False)

print(json.dumps(resultado, indent=4, ensure_ascii=False))

if not resultado["integridad_correcta"]:
    sys.exit(1)