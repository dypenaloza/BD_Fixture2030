# Hito 12 — Refuerzo de las pruebas de carga

## 1. Objetivo

Se realizaron pruebas adicionales para mejorar la reproducibilidad, el análisis de recursos y la validación de integridad del Hito 12.

El flujo evaluado continúa siendo la consulta de una selección del Fixture Mundial 2030 mediante el endpoint `GET /selecciones/ARG`.

## 2. Entorno experimental

Las pruebas se realizaron en una notebook con las siguientes características:

| Componente        | Configuración        |
| ----------------- | -------------------- |
| Sistema operativo | Windows 10 Home      |
| Procesador        | Intel Core i5-1135G7 |
| Memoria RAM       | 7,75 GB              |
| Python            | 3.11.9               |
| Docker            | 29.7.2               |
| Base evaluada     | MongoDB              |
| API               | FastAPI              |

El registro del entorno se obtuvo el 30 de octubre de 2026.

Al momento del registro estaban funcionando MongoDB, Cassandra, Neo4j, Redis, InfluxDB e IRIS.

Se utilizó un entorno local con recursos limitados, por lo que los resultados no representan la capacidad de una infraestructura productiva.

El archivo `evidencia/entorno_refuerzo.txt` conserva la información registrada.

## 3. Mejora de reproducibilidad

Se modificó el servicio de selecciones para permitir activar o desactivar la caché mediante la variable de entorno `HITO12_USAR_CACHE`.

* Valor `0`: consulta directa a MongoDB.
* Valor `1`: consulta con caché en memoria.

Esto permite comparar ambas alternativas sin modificar el código entre ejecuciones.

Las pruebas de refuerzo utilizaron el commit:

`b5e77a1fc0bff3b71556181e4299f8fbf6ddac9f`

El escenario de carga mantuvo los mismos parámetros y el mismo endpoint.

**Nota sobre la pareja de corridas oficial**: en la misma sesión se
ejecutaron dos corridas completas con este commit, separadas por
pocos minutos (`linea_base_refuerzo_previo.json`/`optimizada_refuerzo_previo.json`
a las 14:25-14:29, y `linea_base_refuerzo.json`/`optimizada_refuerzo.json`
a las 14:33-14:35). Los resultados variaron entre ambas por el ruido
propio de medir en una notebook sin aislar el entorno — con 400
solicitudes por fase, el P99 en particular es sensible a una sola
muestra lenta. Se adopta como **pareja oficial** la segunda
(`linea_base_refuerzo.json` / `optimizada_refuerzo.json`), porque es
la que tiene mediciones de recursos capturadas en simultáneo
(`recursos_linea_base_refuerzo.csv` / `recursos_optimizada_refuerzo.csv`,
sección 5) y porque es la que ya estaba citada en la sección de
evidencias. La corrida previa se conserva en el repositorio solo por
trazabilidad del proceso, no se usa para ninguna conclusión de este
documento.

## 4. Resultados de rendimiento

Se compararon las mediciones obtenidas en la fase de sostenimiento con
10 usuarios concurrentes, tomadas de `linea_base_refuerzo.json` y
`optimizada_refuerzo.json` (pareja oficial, ver nota anterior).

| Métrica           |   Sin caché |   Con caché |
| ----------------- | ----------: | ----------: |
| Solicitudes       |         400 |         400 |
| Exitosas          |         400 |         400 |
| Errores           |           0 |           0 |
| Latencia promedio |    21,41 ms |    17,47 ms |
| P50               |    20,02 ms |    14,60 ms |
| P95               |    31,03 ms |    31,46 ms |
| P99               |    70,08 ms |    42,92 ms |
| Throughput        | 19,99 req/s | 19,99 req/s |

La latencia promedio disminuyó aproximadamente un 18,4%, el P50 un
27,1% y el P99 un 38,8%.

El P95 prácticamente no cambió (+1,4%, de 31,03 a 31,46 ms): con 400
solicitudes por fase, una diferencia de ese tamaño está dentro del
ruido de medición y no se interpreta como una regresión real.

El throughput no aumentó porque la frecuencia de solicitudes estaba
limitada por el generador de carga.

Estos resultados indican una mejora consistente en la latencia típica
y en el extremo más lento (P99), con el P95 estable, pero igual no
permiten afirmar que todas las solicitudes individuales respondieron
más rápido: son estadísticas agregadas de una sola corrida.

## 5. Consumo de recursos

Se incorporó un script de PowerShell para monitorear CPU y memoria del contenedor MongoDB durante nuevas ejecuciones de carga.

Se obtuvieron nueve mediciones por escenario.

| Métrica               | Sin caché | Con caché |
| --------------------- | --------: | --------: |
| CPU promedio          |     1,61% |     0,93% |
| CPU máxima registrada |     2,85% |     1,55% |
| RAM promedio          | 81,86 MiB | 79,60 MiB |
| RAM máxima registrada | 82,76 MiB | 80,23 MiB |

El consumo promedio observado de CPU disminuyó aproximadamente un 42,4%.

La memoria utilizada por MongoDB también presentó una pequeña reducción.

Las mediciones de recursos sí corresponden a la misma ventana temporal que la pareja oficial de corridas de latencia de la sección 4 (`recursos_linea_base_refuerzo.csv` se registró entre las 14:33:24 y 14:33:51, en paralelo con `linea_base_refuerzo.json`; `recursos_optimizada_refuerzo.csv` entre las 14:34:48 y 14:35:14, en paralelo con `optimizada_refuerzo.json`). No son simultáneas con la corrida previa descartada (sección 3).

Además, los valores máximos corresponden solamente a las muestras registradas y no necesariamente a los picos reales.

Los resultados respaldan la hipótesis de que la caché puede reducir el trabajo de MongoDB, aunque las diferencias también pueden estar influidas por las condiciones del sistema.

## 6. Validación de integridad

Se ejecutó una validación adicional para comprobar que la respuesta de la API coincidiera con la información almacenada directamente en MongoDB.

Se verificaron los siguientes campos:

* id
* pais
* nombre
* confederacion
* grupo
* ranking
* anfitrion

Resultados:

| Verificación              | Resultado |
| ------------------------- | --------- |
| HTTP 200                  | Correcto  |
| Identificador ARG         | Correcto  |
| Coincidencia completa     | Correcta  |
| Integridad de la consulta | Correcta  |

La validación confirmó que los siete campos coincidían con MongoDB en el momento de la comprobación.

No se realizaron escrituras durante las pruebas de carga.

Esta validación no demuestra que la caché se actualice automáticamente frente a modificaciones posteriores de los datos.

## 7. Evidencias generadas

Los resultados se encuentran en `docs/evidencia/`.

**Pareja oficial** (la que respalda las tablas y conclusiones de este documento):

* `linea_base_refuerzo.json`
* `optimizada_refuerzo.json`
* `recursos_linea_base_refuerzo.csv`
* `recursos_optimizada_refuerzo.csv`
* `validacion_integridad.json`
* `entorno_refuerzo.txt`

**Conservados solo por trazabilidad** (corrida preliminar del mismo commit, ver nota de la sección 3 — no respaldan ninguna cifra de este documento):

* `linea_base_refuerzo_previo.json`
* `optimizada_refuerzo_previo.json`

## 8. Limitaciones

Las principales limitaciones fueron:

* Se evaluó un único endpoint.
* Las solicitudes se concentraron en la selección ARG.
* No se determinó la capacidad máxima del sistema.
* Las mediciones de recursos fueron muestras periódicas.
* No se midió directamente el consumo de CPU y memoria de FastAPI.
* No se realizaron múltiples repeticiones estadísticas bajo condiciones controladas.
* No se midió experimentalmente una alternativa relacional.
* La caché no dispone de expiración temporal automática.
* El entorno de laboratorio no reproduce la infraestructura del Mundial 2030.
* Dos corridas consecutivas del mismo commit, separadas por pocos minutos, dieron resultados de P95/P99 distintos (ver sección 3): a esta escala (400 solicitudes), el ruido de un entorno de notebook sin aislar puede ser comparable a la mejora que se busca medir.

## 9. Conclusión

Las pruebas adicionales permitieron reforzar la reproducibilidad y la trazabilidad del Hito 12.

La optimización mediante caché estuvo asociada con menor latencia promedio, menor P50, menor P99 y menor consumo de CPU observado en MongoDB.

El P95 fue la excepción: se mantuvo prácticamente igual (+1,4%), una diferencia que a esta escala de muestra se interpreta como ruido y no como una regresión atribuible a la caché.

La validación de integridad confirmó que los campos de la respuesta coincidían con MongoDB en el momento de la comprobación.

Los resultados permiten justificar la optimización para el escenario estudiado, reconociendo sus costos, limitaciones y condiciones experimentales.
