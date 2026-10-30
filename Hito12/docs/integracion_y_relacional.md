# Integración analítica y comparación relacional

## 1. Propuesta de Data Mart

### Pregunta analítica

¿Cuántos partidos tiene asociados cada selección en las distintas fases del Mundial 2030?

El objetivo es integrar información de diferentes fuentes NoSQL para obtener una vista analítica que facilite la consulta y comparación de los partidos asociados a cada selección.

### Fuentes involucradas

**MongoDB:** almacena información de las selecciones, incluyendo código, nombre, país, confederación, grupo y ranking.

**Neo4j:** representa las relaciones entre las entidades del Fixture 2030, permitiendo identificar los partidos vinculados con cada selección.

MongoDB proporciona los atributos descriptivos, mientras que Neo4j permite obtener la información de participación.

La propuesta requiere verificar previamente que las relaciones y los identificadores necesarios estén disponibles en el grafo.

## 2. Estructura propuesta

Se propone un modelo dimensional compuesto por:

**DIM_SELECCION**

* seleccion_id
* nombre
* pais
* confederacion
* grupo

**DIM_PARTIDO**

* partido_id
* fase

**FACT_PARTICIPACION**

* seleccion_id
* partido_id
* cantidad_partidos

El grano de la tabla de hechos será una fila por selección y partido.

El campo `cantidad_partidos` tendrá valor 1 por cada asociación válida. Su agregación permitirá calcular la cantidad de partidos por selección y fase.

Los identificadores de selección y partido permitirán relacionar la información de las fuentes.

## 3. Proceso ETL propuesto

Para construir el Data Mart se utilizaría un proceso ETL (Extract, Transform, Load).

**Extracción:**

Se obtendrían los datos de las selecciones desde MongoDB y las asociaciones entre partidos y selecciones desde Neo4j.

**Transformación:**

Se normalizarían los identificadores y se verificaría que cada partido estuviera correctamente asociado con las selecciones correspondientes.

También se eliminarían duplicados y se controlarían registros incompletos.

**Carga:**

Los datos transformados se almacenarían en una estructura analítica diseñada para responder la pregunta seleccionada.

Se propone una actualización por lotes cada 60 minutos. Este intervalo es una decisión de diseño, no una frecuencia implementada o medida.

El retraso esperado sería de hasta aproximadamente una hora, más el tiempo necesario para procesar cada lote.

### Control de duplicados y fallas

Se utilizaría la combinación de `seleccion_id` y `partido_id` para identificar asociaciones únicas.

Las cargas deberían ser idempotentes, evitando duplicados cuando se repite un proceso.

Ante una falla parcial, se conservaría el último lote completado y se repetiría la carga pendiente.

Los datos que lleguen tarde se incorporarían en una actualización posterior.

### Validación

Se verificaría que:

* Las selecciones existan en la fuente correspondiente.
* Los identificadores de partidos sean válidos.
* No existan asociaciones duplicadas.
* Los conteos del Data Mart coincidan con las relaciones válidas extraídas de Neo4j.

## 4. Ventajas y costos del Data Mart

El Data Mart permitiría realizar consultas analíticas sin acceder repetidamente a todas las fuentes operacionales.

Esto resulta conveniente para reportes que requieren combinar información de selecciones y partidos.

Sin embargo, introduce costos adicionales de almacenamiento, procesamiento y mantenimiento.

Además, los datos podrían presentar cierto retraso respecto de las fuentes originales.

La propuesta busca separar las consultas operacionales de las analíticas, como se explicó en la Clase 13.

## 5. Comparación con una estructura relacional

### Alternativa relacional

En una base relacional, la misma información podría organizarse en tres tablas:

* SELECCIONES
* PARTIDOS
* SELECCION_PARTIDO

La última tabla relacionaría las selecciones con sus partidos mediante claves foráneas.

Para responder la pregunta analítica se utilizarían operaciones JOIN y GROUP BY.

### Comparación de modelos

| Criterio                   | NoSQL                                                 | Relacional                                                |
| -------------------------- | ----------------------------------------------------- | --------------------------------------------------------- |
| Almacenamiento             | MongoDB y Neo4j                                       | Tablas relacionadas                                       |
| Consulta de selección      | Búsqueda por identificador                            | SELECT con clave primaria                                 |
| Relaciones entre entidades | Recorridos del grafo                                  | JOIN entre tablas                                         |
| Flexibilidad               | Modelos específicos para cada dato                    | Esquema estructurado                                      |
| Integración analítica      | Requiere integrar fuentes                             | Puede realizarse mediante SQL                             |
| Consistencia               | Depende de cada producto y del proceso de integración | Puede utilizar transacciones y restricciones relacionales |
| Complejidad                | Administración de múltiples motores                   | Administración del modelo y sus relaciones                |

### Relación con nuestra prueba de carga

En el Hito 12 evaluamos el endpoint:

`GET /selecciones/ARG`

Este endpoint utiliza MongoDB para recuperar información de una selección por su identificador.

En una alternativa relacional, la operación equivalente sería una consulta SELECT sobre una tabla SELECCIONES, utilizando el código ARG como clave de búsqueda.

Ambas alternativas podrían resolver eficientemente esta operación mediante un acceso indexado.

Nuestra prueba demostró una reducción de latencia al incorporar una caché en memoria sobre la implementación con MongoDB.

No realizamos una prueba experimental sobre una base relacional, por lo que no podemos afirmar que una alternativa sea más rápida que la otra.

## 6. Conclusión

MongoDB resulta adecuado para almacenar y consultar los documentos de las selecciones, mientras que Neo4j permite representar las relaciones entre entidades del Fixture 2030.

Una estructura relacional también podría resolver estas necesidades, especialmente cuando se requieren consultas con múltiples relaciones y garantías transaccionales dentro de un mismo motor.

La elección depende del patrón de acceso, el volumen de información, la consistencia requerida y las operaciones que necesita realizar el sistema.

La incorporación de un Data Mart permitiría desacoplar las consultas analíticas de las operaciones habituales de la plataforma.

Esta integración se presenta como una propuesta conceptual. No se implementó ni se midió experimentalmente su rendimiento.
