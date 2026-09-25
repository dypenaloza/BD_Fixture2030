PA1 — Últimos comentarios de un partido

Entrada: "partido_id", "bucket_temporal", límite.
Salida: comentarios más recientes.
Orden: "creado_en DESC".
Frecuencia: muy alta.
Diseño: consulta sobre una partición identificada por ("partido_id", "bucket_temporal").
Justificación: permite leer una cantidad acotada de comentarios sin recorrer otras particiones. El bucket evita concentrar toda la actividad de un partido popular en una única partición.

PA2 — Comentarios de un partido en una ventana temporal

Entrada: "partido_id", "bucket_temporal", fecha inicial, fecha final.
Salida: comentarios del intervalo solicitado.
Orden: "creado_en DESC".
Frecuencia: alta.
Diseño: misma tabla principal que PA1.
Justificación: "creado_en" como clustering permite consultas por rango temporal dentro de una partición conocida.

PA3 — Historial de comentarios de un usuario

Entrada: "usuario_id", "bucket_temporal", límite.
Salida: comentarios recientes del usuario.
Orden: "creado_en DESC".
Frecuencia: media.
Diseño: tabla secundaria orientada por ("usuario_id", "bucket_temporal").
Justificación: buscar por usuario en la tabla principal obligaría a recorrer particiones de distintos partidos. Cassandra recomienda una tabla específica cuando cambia el patrón de acceso.

Prácticas en las que nos basamos:
	Conocer la clave de partición antes de consultar.
	Limitar la cantidad de resultados.
	Utilizar clustering para orden y rangos temporales.
	Evitar "ALLOW FILTERING" como solución habitual.
	Evitar particiones ilimitadas mediante buckets.
	Crear tablas adicionales cuando existan patrones de acceso diferentes.