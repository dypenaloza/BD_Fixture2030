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

## 4. Resultados de rendimiento

Se compararon las mediciones obtenidas en la fase de sostenimiento con 10 usuarios concurrentes.

| Métrica           |   Sin caché |   Con caché |
| ----------------- | ----------: | ----------: |
| Solicitudes       |         400 |         400 |
| Exitosas          |         400 |         400 |
| Errores           |           0 |           0 |
| Latencia promedio |    21,96 ms |    18,28 ms |
| P50               |    20,37 ms |    15,63 ms |
| P95               |    35,89 ms |    32,22 ms |
| P99               |    52,75 ms |    64,66 ms |
| Throughput        | 19,99 req/s | 19,99 req/s |

La latencia promedio disminuyó aproximadamente un 16,8% y el P95 se redujo un 10,2%.

Sin embargo, el P99 aumentó aproximadamente un 22,6%, lo que representa una regresión en las solicitudes del extremo más lento.

El throughput no aumentó porque la frecuencia de solicitudes estaba limitada por el generador de carga.

Estos resultados indican mejoras en algunas métricas, pero no permiten afirmar que todas las solicitudes respondieron más rápido.

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

Las mediciones de recursos corresponden a ejecuciones adicionales realizadas después de los JSON de refuerzo inicialmente analizados. Por lo tanto, no deben interpretarse como métricas obtenidas simultáneamente con aquellas primeras mediciones de latencia.

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

Se incorporaron:

* `linea_base_refuerzo.json`
* `optimizada_refuerzo.json`
* `recursos_linea_base_refuerzo.csv`
* `recursos_optimizada_refuerzo.csv`
* `validacion_integridad.json`
* `entorno_refuerzo.txt`

También se conservaron los resultados de las pruebas originales para mantener la trazabilidad del trabajo.

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

## 9. Conclusión

Las pruebas adicionales permitieron reforzar la reproducibilidad y la trazabilidad del Hito 12.

La optimización mediante caché estuvo asociada con menores latencias promedio y P95, además de un menor consumo de CPU observado en MongoDB.

Sin embargo, el aumento del P99 demuestra que no todas las métricas mejoraron.

La validación de integridad confirmó que los campos de la respuesta coincidían con MongoDB en el momento de la comprobación.

Los resultados permiten justificar la optimización para el escenario estudiado, reconociendo sus costos, limitaciones y condiciones experimentales.
