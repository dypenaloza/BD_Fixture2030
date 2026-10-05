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