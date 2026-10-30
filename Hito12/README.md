# Hito 12 — Pruebas de carga y optimización

## 1. Descripción general

Este hito corresponde al proyecto Fixture Mundial 2030 de Ingeniería de Datos II.

El objetivo es evaluar el comportamiento de una parte de la plataforma ante múltiples solicitudes, identificar oportunidades de optimización y comparar el rendimiento antes y después de aplicar una mejora.

Se utiliza la API REST desarrollada durante la cursada, conectada a MongoDB.

También se presenta una propuesta conceptual de Data Mart y una comparación con estructuras relacionales.

## 2. Flujo seleccionado

Se seleccionó la consulta de información de una selección nacional.

**Endpoint:** `GET /selecciones/ARG`

**Fuente:** MongoDB.

**Operación:** lectura de información de la selección argentina.

**Consumidor:** usuarios que consultan información del Fixture 2030 mediante la API REST.

El endpoint devuelve información como país, nombre, confederación, grupo, ranking y condición de anfitrión.

Se eligió este flujo porque representa una consulta que podría repetirse frecuentemente antes de un partido.

## 3. Entorno de ejecución

Las pruebas se realizaron el 30 de octubre de 2026, en una notebook con Windows, PowerShell, Docker Desktop y Python.

Se utilizó MongoDB mediante un contenedor Docker y una API REST desarrollada con FastAPI.

Las mediciones corresponden a un entorno de laboratorio, no a una infraestructura productiva.

**Versión de referencia anterior a la optimización:**

`1d0001c8d0bd3cbfce7a52df6b03fba82b64553a`

Los archivos JSON registran este mismo commit porque la modificación de la caché todavía no estaba confirmada en Git al ejecutar la segunda prueba. La versión optimizada queda identificada mediante el cambio del servicio y el commit posterior.

## 4. Escenario de carga

Se simularon consultas concurrentes al mismo endpoint.

| Parámetro             | Configuración                   |
| --------------------- | ------------------------------- |
| Operación             | GET                             |
| Endpoint              | `/selecciones/ARG`              |
| Lecturas              | 100%                            |
| Escrituras            | 0%                              |
| Calentamiento         | 5 solicitudes                   |
| Rampa inicial         | 2 usuarios durante 5 segundos   |
| Rampa intermedia      | 5 usuarios durante 5 segundos   |
| Sostenimiento         | 10 usuarios durante 20 segundos |
| Duración medida total | Aproximadamente 30 segundos     |
| Intervalo por usuario | 0,5 segundos                    |
| Timeout               | 3 segundos                      |

El generador realiza solicitudes concurrentes y registra su duración individual.

La tasa de solicitudes está limitada por el intervalo configurado para cada usuario.

La prueba finaliza al completar las tres fases. Cada solicitud tiene un timeout de 3 segundos para evitar esperas indefinidas.

## 5. Datos utilizados

Se utilizó el documento correspondiente a la selección argentina, identificado mediante la clave `ARG`.

Los datos provienen del entorno de laboratorio del Fixture 2030.

Todas las solicitudes consultan la misma selección, simulando una clave de acceso frecuente.

Esta distribución permite evaluar consultas repetidas, pero no representa la variedad ni el volumen total proyectado para el Mundial.

No se generan ni modifican registros durante la prueba.

## 6. Ejecución

### Requisitos

* Python y las dependencias existentes de la API REST.
* Docker Desktop.
* MongoDB funcionando.
* API REST disponible en el puerto 8000.

### Preparar el entorno

Desde la carpeta `API_REST`, iniciar la API:

```powershell
.\.venv311\Scripts\python.exe -m uvicorn app.main:app --reload
```

Si MongoDB está detenido, iniciar su contenedor:

```powershell
docker start fixture2030-mongodb
```

La API requiere la configuración de conexión correspondiente, que debe mantenerse fuera del repositorio.

### Ejecutar la carga

Desde la raíz del proyecto:

**Línea base:**

```powershell
.\API_REST\.venv311\Scripts\python.exe .\Hito12\scripts\ejecutar_carga.py linea_base
```

**Prueba optimizada:**

```powershell
.\API_REST\.venv311\Scripts\python.exe .\Hito12\scripts\ejecutar_carga.py optimizada
```

Para reproducir una comparación válida, la primera prueba debe ejecutarse con el servicio original sin caché y la segunda con la optimización incorporada.

El script utiliza la misma configuración para ambas ejecuciones.

Los resultados se guardan automáticamente en archivos CSV y JSON.

La prueba es exclusivamente de lectura, por lo que no requiere eliminar registros generados.

## 7. Línea base

Se ejecutaron tres fases de carga con distintos niveles de concurrencia.

| Métrica           | 2 usuarios | 5 usuarios | 10 usuarios |
| ----------------- | ---------: | ---------: | ----------: |
| Solicitudes       |         20 |         50 |         400 |
| Exitosas          |         20 |         50 |         400 |
| Errores           |          0 |          0 |           0 |
| Latencia promedio |   21,69 ms |   23,68 ms |    24,28 ms |
| P95               |   32,70 ms |   92,86 ms |    35,82 ms |
| P99               |   37,42 ms |  132,87 ms |   124,59 ms |
| Throughput        | 4,00 req/s | 9,99 req/s | 19,99 req/s |

Las 470 solicitudes finalizaron correctamente.

No obstante, se observaron diferencias entre la latencia promedio y las solicitudes más lentas.

Se registró también una captura de recursos de Docker posterior a la ejecución, que no representa necesariamente el consumo durante el pico de carga.

## 8. Hipótesis y optimización

### Hipótesis

Las consultas repetidas al mismo documento pueden generar accesos innecesarios a MongoDB.

Se planteó que una caché podría disminuir la latencia al reutilizar resultados previamente obtenidos.

### Modificación implementada

Se incorporó `lru_cache` en:

`API_REST/app/services/selecciones_service.py`

La caché permite almacenar hasta 64 resultados.

Las solicitudes posteriores al mismo identificador pueden reutilizar el resultado sin consultar nuevamente MongoDB.

### Trade-off

La optimización introduce consumo adicional de memoria.

Además, la implementación no dispone de expiración temporal automática.

Por lo tanto, podrían devolverse datos desactualizados si la información original se modifica.

La caché también es local al proceso de la aplicación, por lo que no constituye una solución distribuida.

## 9. Comparación de resultados

| Métrica — 10 usuarios |       Antes |     Después |
| --------------------- | ----------: | ----------: |
| Solicitudes           |         400 |         400 |
| Errores               |           0 |           0 |
| Latencia promedio     |    24,28 ms |    17,47 ms |
| P50                   |    21,13 ms |    15,57 ms |
| P95                   |    35,82 ms |    29,92 ms |
| P99                   |   124,59 ms |    33,99 ms |
| Throughput            | 19,99 req/s | 19,99 req/s |

La latencia promedio disminuyó aproximadamente un 28% durante la fase de sostenimiento.

El P99 disminuyó aproximadamente un 72,7%.

El throughput permaneció estable debido a la tasa de solicitudes configurada.

Los resultados son compatibles con la hipótesis de mejora, aunque no permiten establecer que la caché explique por sí sola toda la diferencia observada.

La comparación detallada se encuentra en:

`docs/comparacion_resultados.md`

## 10. Validación de integridad

Se verificó que las solicitudes devolvieran código HTTP 200 y que el identificador recibido fuera `ARG`.

No se detectaron errores en las 470 solicitudes de ninguna de las dos ejecuciones.

La prueba no realizó escrituras ni modificaciones sobre MongoDB.

La validación comprueba parcialmente el contenido de las respuestas, pero no todos sus atributos.

## 11. Propuesta de Data Mart

Se propone construir una vista analítica para responder:

**¿Cuántos partidos tiene asociados cada selección en las distintas fases del Mundial 2030?**

Se integrarían datos de MongoDB y Neo4j mediante un proceso ETL.

MongoDB proporcionaría información descriptiva de las selecciones y Neo4j aportaría las asociaciones entre selecciones y partidos.

Se propone una actualización por lotes cada 60 minutos.

La propuesta contempla normalización de identificadores, eliminación de duplicados, validación de conteos y recuperación ante fallas.

Este diseño es conceptual: no se implementó un Data Mart completo.

## 12. Comparación con estructuras relacionales

Una alternativa relacional podría utilizar tablas de selecciones, partidos y sus asociaciones.

La consulta analítica podría resolverse mediante operaciones JOIN y GROUP BY.

MongoDB y Neo4j permiten utilizar modelos específicos para cada tipo de información, mientras que una estructura relacional facilita ciertas consultas integradas y restricciones transaccionales.

No se realizó una comparación experimental de rendimiento contra una base relacional.

El análisis completo se encuentra en:

`docs/integracion_y_relacional.md`

## 13. Limitaciones

Las principales limitaciones identificadas son:

* Se utilizó una notebook y un volumen reducido de datos.
* Se evaluó un único endpoint.
* Todas las solicitudes consultaron la misma selección.
* La prueba no determina la capacidad máxima del sistema.
* No se midieron directamente los aciertos de caché.
* No se registraron métricas de recursos durante toda la ejecución.
* No se implementó una invalidación temporal de caché.
* No se realizó una comparación experimental con una base relacional.
* La caché se evaluó después de cinco solicitudes de calentamiento.

Por estos motivos, los resultados no pueden extrapolarse directamente a un escenario productivo de millones de usuarios.

## 14. Evidencias

La carpeta `docs/evidencia/` contiene:

| Archivo                      | Descripción                                   |
| ---------------------------- | --------------------------------------------- |
| `linea_base.csv`             | Mediciones individuales antes de optimizar    |
| `linea_base.json`            | Resumen de la línea base                      |
| `optimizada.csv`             | Mediciones individuales después de optimizar  |
| `optimizada.json`            | Resumen de la prueba optimizada               |
| `01_recursos_linea_base.png` | Captura de recursos posterior a la línea base |

Los resultados pueden reproducirse siguiendo las instrucciones de ejecución y utilizando las versiones correspondientes de la API.

## 15. Conclusión

El Hito 12 permitió analizar el comportamiento de una consulta del Fixture 2030 ante diferentes niveles de concurrencia.

Se estableció una línea base, se aplicó una optimización mediante caché y se repitió el escenario de carga.

Los resultados mostraron una reducción en los tiempos de respuesta sin errores observados.

También se identificaron limitaciones relacionadas con el entorno, el patrón de acceso y la actualización de los datos almacenados en caché.

Finalmente, se propuso una integración analítica mediante un Data Mart y se comparó conceptualmente la solución NoSQL con una alternativa relacional.

La experiencia demuestra la importancia de medir antes de optimizar y de evaluar tanto las mejoras como sus costos y limitaciones.

## Pruebas adicionales de refuerzo

Se realizaron pruebas complementarias para mejorar la reproducibilidad,
registrar el consumo de recursos y validar la integridad de los datos.

Los resultados, las comparaciones y las limitaciones se documentan en:

[Informe de pruebas de refuerzo](docs/refuerzo_pruebas.md)
