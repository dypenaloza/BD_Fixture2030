# Comparación de rendimiento: línea base y optimización

## 1. Objetivo

Evaluar el rendimiento del endpoint `GET /selecciones/ARG` antes y después de implementar una caché en memoria mediante `lru_cache`.

La prueba representa un escenario de consultas repetidas a una selección del Fixture Mundial 2030.

## 2. Optimización aplicada

Inicialmente, cada solicitud consultaba MongoDB para obtener la información de Argentina.

Se incorporó una caché en el servicio de selecciones para reutilizar respuestas previamente consultadas y reducir accesos repetitivos a MongoDB.

La caché almacena hasta 64 resultados.

## 3. Resultados experimentales

| Métrica                        |  Línea base |  Optimizada |
| ------------------------------ | ----------: | ----------: |
| Solicitudes totales            |         470 |         470 |
| Solicitudes exitosas           |         470 |         470 |
| Errores                        |           0 |           0 |
| Latencia promedio, 2 usuarios  |    21,69 ms |    11,20 ms |
| Latencia promedio, 5 usuarios  |    23,68 ms |    13,23 ms |
| Latencia promedio, 10 usuarios |    24,28 ms |    17,47 ms |
| P95, 10 usuarios               |    35,82 ms |    29,92 ms |
| P99, 10 usuarios               |   124,59 ms |    33,99 ms |
| Throughput, 10 usuarios        | 19,99 req/s | 19,99 req/s |

Ambas pruebas utilizaron el mismo endpoint, configuración de carga, concurrencia y duración.

## 4. Interpretación

La optimización produjo una reducción del 28,0% en la latencia promedio durante la fase de sostenimiento.

El P95 disminuyó aproximadamente un 16,5%, mientras que el P99 se redujo un 72,7%.

El throughput permaneció prácticamente constante debido a la frecuencia de solicitudes establecida por el generador.

Estos resultados indican una mejora en los tiempos de respuesta observados, pero no demuestran un incremento de la capacidad máxima del sistema.

## 5. Integridad

Las 470 solicitudes de ambas pruebas finalizaron correctamente.

El script verificó que las respuestas tuvieran código HTTP 200 y que el identificador correspondiera a la selección ARG.

La prueba fue exclusivamente de lectura, por lo que no generó nuevos registros ni modificó datos existentes.

La validación no incluyó una comparación completa de todos los atributos de las respuestas.

## 6. Trade-off

La caché reduce las consultas repetidas a MongoDB, pero introduce consumo adicional de memoria y posibles problemas de actualización.

La implementación utilizada no tiene expiración temporal automática. Por lo tanto, una modificación realizada en MongoDB podría no reflejarse inmediatamente en las respuestas de la API.

## 7. Limitaciones

Las pruebas se ejecutaron en una notebook con un volumen reducido de datos.

Se evaluó un único endpoint y una misma selección repetidamente.

No se realizó una prueba de capacidad máxima ni se midieron directamente los aciertos y fallos de caché.

La captura disponible de recursos corresponde a un instante posterior a la línea base, por lo que no permite comparar el consumo durante ambas ejecuciones.

Los resultados corresponden al entorno de laboratorio y no pueden extrapolarse directamente a la demanda productiva del Mundial 2030.

## 8. Conclusión

En el escenario evaluado, la incorporación de caché estuvo asociada con una reducción de las latencias sin introducir errores observados.

La decisión resulta conveniente para consultas repetitivas de información relativamente estable, siempre que se considere una estrategia de invalidación o actualización de la caché.
