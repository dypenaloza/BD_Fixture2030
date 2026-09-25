Modelo tabular

Keyspace: "fixture2030"

Tabla principal: "comentarios_por_partido"

Propósito:
Resolver PA1 y PA2: recuperar comentarios recientes de un partido y comentarios dentro de una ventana temporal.

Columnas principales:
- "partido_id": text
- "bucket_temporal": text
- "creado_en": timestamp
- "comentario_id": uuid
- "usuario_id": text
- "contenido": text
- "estado_moderacion": text
- "likes": int

Clave primaria:
PRIMARY KEY (("partido_id", "bucket_temporal"), "creado_en", "comentario_id")

Clave de partición:
("partido_id", "bucket_temporal")

Columnas de clustering:
- "creado_en"
- "comentario_id"

Orden:
"creado_en DESC"

Justificación:
"partido_id" identifica el partido y "bucket_temporal" evita que toda la actividad de un partido popular quede en una única partición.

"creado_en" permite recuperar comentarios ordenados por tiempo y consultar rangos temporales.

"comentario_id" garantiza que dos comentarios creados en el mismo instante puedan distinguirse.

Tabla secundaria: "comentarios_por_usuario"

Propósito:
Resolver PA3: recuperar el historial de comentarios de un usuario.

Clave primaria propuesta:
PRIMARY KEY (("usuario_id", "bucket_temporal"), "creado_en", "comentario_id")

Justificación:
Se utiliza una tabla separada porque consultar por usuario en la tabla principal obligaría a recorrer particiones de distintos partidos.