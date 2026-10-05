**Modelo multidimensional**

# Tabla:
estadisticas

# Fenómeno que registra:
Estadísticas en vivo de los equipos durante un partido del Fixture 2030.

# Tags:
- partido_id
- equipo_id

# Fields:
- posesion_pct
- pases
- tiros

# Timestamp:
Instante en el que se registra cada observación.

# Precisión temporal:
Segundos.

# Serie resultante:
Cada combinación única de tabla + partido_id + equipo_id representa una serie temporal.

**Justificación de tags y fields**

# ¿Por qué partido_id es un tag?
Porque identifica el partido al que pertenecen las estadísticas y se utiliza como dimensión de filtro en las consultas.

# ¿Por qué equipo_id es un tag?
Porque permite identificar y comparar las estadísticas de cada equipo dentro de un partido.

# ¿Por qué posesion_pct es un field?
Porque es un valor observado que cambia a lo largo del tiempo y no identifica una serie.

# ¿Por qué pases es un field?
Porque representa una medida registrada durante el partido y su valor puede cambiar entre observaciones.

# ¿Por qué tiros es un field?
Porque representa una medida del partido que cambia con el tiempo y debe analizarse como valor observado.

**Medidas temporales**

# posesion_pct
Tipo: Decimal.

Semántica:
Representa el porcentaje de posesión del equipo en el instante observado.

Agregación:
AVG (promedio).

Justificación:
La posesión es una muestra que puede promediarse dentro de un intervalo para analizar su tendencia.

# pases
Tipo: Entero.

Semántica:
Representa la cantidad acumulada de pases realizados por el equipo hasta ese instante.

Agregación:
MAX o diferencia entre el valor final e inicial del intervalo.

Justificación:
Al ser un contador acumulado, sumar todas las observaciones contaría varias veces los mismos pases.

# tiros
Tipo: Entero.

Semántica:
Representa la cantidad de tiros ocurridos desde la observación anterior.

Agregación:
SUM (suma).

Justificación:
Como cada observación registra nuevos tiros ocurridos durante ese intervalo, pueden sumarse para obtener el total.