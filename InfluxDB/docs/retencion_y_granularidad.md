**Retención y granularidad**

# ¿Qué datos se conservan con precisión original?
Las estadísticas en vivo se conservan con su granularidad original durante el período en que se necesita analizar el partido en detalle.

# ¿Qué datos pueden resumirse?
Con el paso del tiempo, los datos pueden resumirse mediante agregaciones por ventanas temporales.

Ejemplos:
- posesión promedio por minuto;
- cantidad de tiros por intervalo;
- diferencia de pases acumulados entre el inicio y el final de una ventana.

# ¿Por qué resumir los datos?
Porque para el análisis histórico no siempre es necesario conservar cada observación individual.
Los resúmenes permiten mantener la tendencia general utilizando una menor cantidad de puntos.

# ¿Qué datos pueden expirar?
Los puntos de alta frecuencia pueden expirar cuando dejan de ser necesarios para consultas detalladas, siempre que se hayan conservado los resúmenes requeridos para el análisis histórico.

# ¿Qué diferencia hay entre datos en vivo e históricos?
Los datos en vivo requieren mayor detalle y rangos temporales cortos.
Los datos históricos pueden utilizar una granularidad menor, por ejemplo resúmenes por minuto o por intervalos mayores.

# Política propuesta:
- Durante el partido: conservar los puntos con precisión original.
- Los datos detallados se conservarán durante 30 días.
- Para análisis histórico se utilizarán datos resumidos mediante agregaciones temporales.
- Los datos detallados podrán expirar una vez finalizado su período de retención.