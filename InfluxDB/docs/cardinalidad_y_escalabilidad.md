**Cardinalidad del modelo**

# ¿Qué es la cardinalidad?
Es la cantidad de combinaciones diferentes de tabla y tags que forman series temporales.

# Tags utilizados:
- partido_id
- equipo_id

# ¿Qué combinación forma una serie?
Cada combinación diferente de partido_id y equipo_id dentro de la tabla estadisticas forma una serie.

Ejemplo:

estadisticas + M001 + ARG → una serie

estadisticas + M001 + POR → otra serie

# Estimación:
El Fixture 2030 contempla 127 partidos.

Como cada partido contiene las estadísticas de sus dos equipos:

127 partidos × 2 equipos = 254 series aproximadas.

# Conclusión:
La cardinalidad se mantiene acotada porque partido_id y equipo_id poseen una cantidad limitada de valores y son dimensiones necesarias para las consultas definidas.

**Atributos excluidos de los tags**

# ¿Por qué posesion_pct no es un tag?
Porque su valor cambia constantemente y puede tomar muchos valores diferentes.

Usarlo como tag aumentaría innecesariamente la cantidad de series.

Por eso se mantiene como field.

# ¿Por qué pases no es un tag?
Porque representa una medida que cambia durante el partido.

No se utiliza para identificar una serie, sino para analizar el valor observado.

Por eso se mantiene como field.

# ¿Por qué tiros no es un tag?
Porque representa una medida que cambia durante el partido.

No necesitamos crear una serie diferente según la cantidad de tiros.

Por eso se mantiene como field.

# ¿Por qué el timestamp no es un tag?
Porque cada observación posee su propio instante temporal.

Si el timestamp se utilizara como tag, prácticamente cada punto podría generar una combinación diferente y aumentar enormemente la cardinalidad.

El tiempo se utiliza como timestamp propio de la observación.

**Escalabilidad del modelo**

# Objetivo de volumen:
El módulo debe estar diseñado para soportar un objetivo de 10M+ puntos de estadísticas temporales, pero para la prueba local utiliza un volumen menor.

# ¿Cómo se plantea el crecimiento?
La carga debe realizarse en lotes y no necesariamente punto por punto.

Para escalar se deben considerar:
- tamaño de lote;
- concurrencia;
- generación de timestamps;
- manejo de errores;
- reintentos;
- validación de puntos cargados.

# ¿Qué ayuda a mantener el modelo escalable?
- Mantener baja la cardinalidad de series.
- Evitar tags con demasiados valores diferentes.
- Consultar rangos temporales acotados.
- Filtrar por las dimensiones necesarias.
- Utilizar agregaciones cuando no se necesita recuperar cada punto individual.
- Definir una política de retención para evitar conservar indefinidamente datos de alta frecuencia sin necesidad.

# Diferencia entre objetivo y prueba real:
El objetivo del diseño es soportar 10M+ puntos.

La prueba realizada en el ambiente local utilizará un volumen acorde al hardware disponible.

El volumen efectivamente probado, el método y los resultados están documentados sin suponer rendimientos no medidos.

**Prueba local de carga**

# Fecha de ejecución:
06/10/2026

# Ambiente utilizado:
- InfluxDB 3 Core versión 3.12.0.
- Procesador: 11th Gen Intel(R) Core(TM) i5-1135G7 @ 2.40GHz.
- Memoria RAM: 7,75 GB.
- Entorno ejecutado localmente mediante Docker Compose.

# Volumen probado:
Se generaron y cargaron 10.000 puntos temporales correspondientes al partido M002.

Los puntos se distribuyeron de la siguiente manera:
- ARG: 5.000 puntos.
- POR: 5.000 puntos.

# Método de prueba:
Los 10.000 puntos fueron generados mediante el script generacion_volumen.ps1 y almacenados en un archivo de line protocol.

La carga fue realizada mediante carga_lotes.ps1 utilizando influxdb3 write con precisión temporal en segundos.

La cantidad y distribución de los puntos fueron verificadas posteriormente mediante validacion.ps1.

# Resultados observados:
El CLI de InfluxDB informó:

- Tiempo de escritura: 320 ms.
- Solicitudes realizadas: 1.
- Velocidad informada: 31.174 líneas/s.
- Datos procesados: 887,09 KiB.
- Velocidad de transferencia informada: 2,70 MiB/s.

El cronómetro externo del script carga_lotes.ps1 registró un tiempo total de 1,0744054 segundos.

# Interpretación:
Los 320 ms corresponden al tiempo informado por el comando de escritura de InfluxDB.

Los 1,0744054 segundos corresponden al tiempo total observado por el script alrededor de la ejecución del comando.

Por este motivo, ambas mediciones se registran por separado y no se consideran equivalentes.

# Validación:
Luego de la carga se verificó que M002 contuviera exactamente 10.000 puntos:

- ARG: 5.000 puntos.
- POR: 5.000 puntos.

La cantidad y distribución coincidieron con los datos generados.

# Limitaciones:
Esta prueba corresponde únicamente al ambiente local disponible y a un volumen real de 10.000 puntos.

No se afirma que este resultado represente el rendimiento con 10M+ puntos.

El objetivo de 10M+ puntos se considera una meta de diseño y escalabilidad, mientras que la medición realizada corresponde únicamente al volumen efectivamente probado.