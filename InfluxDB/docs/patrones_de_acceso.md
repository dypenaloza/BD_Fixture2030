Patrones de acceso temporales

**Patrón 1 — Evolución de estadísticas de un equipo durante un partido**

# Pregunta:
¿Cómo evolucionaron las estadísticas de un equipo durante un intervalo de un partido?

# Genera:
La fuente de estadísticas en vivo del partido.

# Consulta:
La plataforma Fixture 2030.

# Rango temporal:
Un intervalo acotado dentro del partido.

# Dimensiones necesarias:
- partido
- equipo

# Medidas:
- posesión
- pases
- tiros

# Frecuencia esperada:
Observaciones frecuentes durante el partido.

# Precisión temporal:
Segundos.

# Respuesta esperada:
Recuperar los puntos ordenados por tiempo para observar cómo evolucionan las medidas.

# Datos faltantes o tardíos:
La ausencia de un punto no debe interpretarse como valor cero. Un dato tardío conserva el timestamp correspondiente al instante en que fue observado.


**Patrón 2 — Comparación de estadísticas entre equipos**

# Pregunta:
¿Cómo se comparan las estadísticas de los dos equipos durante un intervalo de un partido?

# Genera:
La fuente de estadísticas en vivo del partido.

# Consulta:
La plataforma Fixture 2030.

# Rango temporal:
Un intervalo acotado dentro del partido.

# Dimensiones necesarias:
- partido
- equipo

# Medidas:
- posesión
- pases
- tiros

# Frecuencia esperada:
Observaciones frecuentes durante el partido.

# Precisión temporal:
Segundos.

# Respuesta esperada:
Recuperar las estadísticas de ambos equipos dentro del mismo intervalo para poder compararlas.

# Datos faltantes o tardíos:
La ausencia de un punto no se interpreta como valor cero. Los datos tardíos conservan el timestamp correspondiente al instante en que fueron observados.

**Patrón 3 – Resumen de estadísticas por intervalo**

# Pregunta:
¿Cuál fue el resumen de las estadísticas de cada equipo durante un intervalo de un partido?

# Genera:
La fuente de estadísticas en vivo del partido.

# Consulta:
La plataforma Fixture 2030.

# Rango temporal:
Un intervalo determinado dentro del partido.

# Dimensiones necesarias:
- partido
- equipo

# Medidas:
- posesión
- pases
- tiros

# Frecuencia esperada:
Observaciones frecuentes durante el partido.

# Precisión temporal:
Segundos.

# Respuesta esperada:
Obtener un resumen de las estadísticas de cada equipo durante el intervalo consultado.

# Datos faltantes o tardíos:
La ausencia de un punto no se interpreta como valor cero. Los datos tardíos conservan el timestamp correspondiente al instante en que fueron observados.