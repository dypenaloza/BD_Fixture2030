Supuestos de volumen

- Un partido popular puede recibir una cantidad muy alta de comentarios durante su duración.
- La mayor carga se concentra durante el partido en vivo.
- No se utilizará únicamente "partido_id" como clave de partición para evitar particiones demasiado grandes y hotspots.
- Los comentarios se dividirán utilizando buckets temporales.

Estrategia de particionamiento

La clave de partición propuesta será:

("partido_id", "bucket_temporal")

El "bucket_temporal" dividirá los comentarios de cada partido en ventanas de tiempo.

Se propone inicialmente un bucket de 5 minutos.

Justificación

Un bucket de 5 minutos limita la cantidad de comentarios y escrituras que se concentran en una sola partición, manteniendo al mismo tiempo consultas simples para recuperar comentarios recientes o por ventana temporal.

Las columnas de clustering serán "creado_en" y "comentario_id", permitiendo ordenar los comentarios por fecha y distinguir comentarios creados en el mismo instante.