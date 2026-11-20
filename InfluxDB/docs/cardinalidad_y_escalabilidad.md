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
El Fixture 2030 contempla 128 partidos.

Como cada partido contiene las estadísticas de sus dos equipos:

128 partidos × 2 equipos = 256 series aproximadas.

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

**Implementado, no solo planteado** (`scripts/carga_lotes.ps1`): la
versión anterior de este script escribía el archivo `.lp` completo en una
sola llamada a `influxdb3 write`, sin ningún control real de los seis
puntos de arriba — quedaban mencionados en este documento pero no se
reflejaban en el código. La versión actual:

- **Tamaño de lote**: parámetro `-TamanoLote` (default 2000 líneas por
  lote); el archivo de entrada se particiona antes de escribir nada.
- **Concurrencia**: parámetro `-Concurrencia` (default 2); los lotes se
  envían como `Start-Job` de PowerShell, con un máximo de lotes en vuelo
  a la vez — no espera a que termine un lote para lanzar el siguiente.
- **Manejo de errores y reintentos**: parámetro `-MaxReintentos` (default
  3); cada lote que falla (`influxdb3 write` con código de salida
  distinto de 0) se reintenta con backoff exponencial (2s, 4s, 8s...)
  antes de darlo por perdido. Si un lote agota los reintentos, el script
  termina con error y reporta cuál.
- **Validación de puntos cargados**: se cuenta `SELECT COUNT(*) FROM
  estadisticas` antes y después de la carga; el script falla
  explícitamente si el delta no coincide con la cantidad de puntos que se
  intentó cargar (esto también detecta el caso real de que dos puntos
  compartan serie y timestamp exacto, donde InfluxDB sobrescribe en vez
  de duplicar — no es un bug del script, es el comportamiento del motor,
  pero el script lo hace visible en vez de darlo por éxito silencioso).

No se reimplementó como un sistema de colas persistente ni con
reintentos distribuidos entre procesos distintos — para el volumen de
prueba de este hito (10.000 puntos) alcanza con jobs de PowerShell en un
mismo proceso; escalar a 10M+ puntos reales probablemente necesitaría
mover esto a un proceso dedicado con una cola persistente, pero esa
capa no se construyó y no se afirma que esté medida.

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