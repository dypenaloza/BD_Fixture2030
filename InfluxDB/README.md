# Hito 8 — Series Temporales de Estadísticas en Vivo

Módulo de series temporales del proyecto **Fixture 2030**, desarrollado para la asignatura Ingeniería de Datos II.

Repositorio del proyecto:

https://github.com/dypenaloza/BD_Fixture2030

---

## 1. Objetivo

El módulo permite registrar, consultar y analizar estadísticas que evolucionan a lo largo del tiempo durante los partidos del Fixture 2030.

Las observaciones temporales utilizadas incluyen:

- posesión;
- pases;
- tiros.

Cada observación se almacena junto con el partido, el equipo y el instante temporal correspondiente.

El objetivo de diseño del Hito es contemplar un volumen de **10M+ puntos**, aunque la prueba ejecutada localmente utiliza un volumen menor y medido de forma reproducible.

---

## 2. Tecnología utilizada

- InfluxDB 3 Core.
- Docker Compose.
- PowerShell.
- Line Protocol para escritura.
- SQL para consultas.
- Persistencia mediante bind mount local.

### Decisión sobre la versión de InfluxDB

El enunciado del Hito menciona `influxdb:latest`.

Sin embargo, la Clase 9 utilizada como referencia técnica aclara que `influxdb:latest` corresponde a la línea 2.x, mientras que el entorno trabajado en clase utiliza InfluxDB 3 Core, el comando `influxdb3`, SQL y el puerto `8181`.

Por este motivo se utiliza:

```yaml
image: influxdb:3-core
```

Esto mantiene coherencia con el entorno práctico y con el `docker-compose.yml` utilizado durante la clase.

---

## 3. Estructura del módulo

```text
InfluxDB/
├── docker-compose.yml
├── scripts/
│   ├── inicializacion.ps1
│   ├── autorizacion_local.ps1
│   ├── generacion_puntos.ps1
│   ├── generacion_volumen.ps1
│   ├── carga_lotes.ps1
│   ├── consultas_temporales.ps1
│   ├── agregaciones.ps1
│   └── validacion.ps1
├── docs/
│   ├── patrones_de_acceso.md
│   ├── modelo_multidimensional.md
│   ├── cardinalidad_y_escalabilidad.md
│   ├── retencion_y_granularidad.md
│   └── evidencia/
└── README.md
```

Los archivos de puntos generados durante las pruebas no forman parte de la entrega versionada.

---

## 4. Modelo multidimensional

Se utiliza la tabla:

```text
estadisticas
```

### Tags

```text
partido_id
equipo_id
```

Los tags representan dimensiones utilizadas para localizar y comparar las observaciones.

Ejemplo:

```text
partido_id=M001
equipo_id=ARG
```

### Fields

```text
posesion_pct
pases
tiros
```

Los fields representan valores observados que cambian durante el partido.

### Timestamp

Cada punto contiene el instante correspondiente a la observación.

La precisión temporal utilizada en el módulo es:

```text
segundos
```

Las escrituras se realizan declarando:

```text
--precision s
```

### Serie resultante

Una serie queda determinada por la tabla y la combinación de tags.

Ejemplos:

```text
estadisticas + M001 + ARG
estadisticas + M001 + POR
```

Los miles de puntos registrados para una misma combinación siguen perteneciendo a la misma serie.

---

## 5. Semántica de las medidas

### Posesión

`posesion_pct` representa una muestra porcentual de posesión en un instante.

Tipo:

```text
decimal
```

Agregación utilizada:

```text
AVG
```

El promedio permite resumir el comportamiento de la posesión durante un intervalo.

### Pases

`pases` representa un contador acumulado de pases realizados hasta cada observación.

Tipo:

```text
entero
```

Para conocer los pases nuevos de un intervalo se utiliza:

```text
MAX(pases) - MIN(pases)
```

No se suman todas las observaciones porque cada valor acumulado ya contiene los pases anteriores.

### Tiros

`tiros` registra los tiros nuevos ocurridos desde la observación anterior.

Tipo:

```text
entero
```

Agregación utilizada:

```text
SUM
```

La suma permite conocer la cantidad total de tiros ocurridos durante el intervalo consultado.

---

## 6. Patrones de acceso implementados

El modelo fue definido después de identificar las preguntas que debía responder.

### Patrón 1 — Evolución de un equipo

Permite responder:

> ¿Cómo evolucionaron las estadísticas de un equipo durante un intervalo de un partido?

Se filtra principalmente por:

```text
partido_id
equipo_id
rango temporal
```

### Patrón 2 — Comparación entre equipos

Permite comparar las estadísticas de los dos equipos participantes en un mismo partido.

### Patrón 3 — Resumen temporal

Permite obtener un resumen de las estadísticas mediante operaciones como:

```text
AVG
SUM
MAX - MIN
```

La función aplicada depende del significado real de cada medida.

---

## 7. Cardinalidad

Los tags utilizados son:

```text
partido_id
equipo_id
```

El Fixture 2030 contempla 127 partidos.

Considerando dos equipos por partido:

```text
127 partidos × 2 equipos = 254 series aproximadas
```

Esta cardinalidad permanece acotada porque las dimensiones tienen una cantidad limitada de valores.

No se utilizan como tags:

```text
posesion_pct
pases
tiros
timestamp
```

Estos valores cambian constantemente y convertirlos en tags aumentaría innecesariamente la cantidad de series.

---

## 8. Persistencia

Los datos de InfluxDB se almacenan localmente en:

```text
~/docker/data/influxdb
```

El `docker-compose.yml` utiliza un bind mount:

```yaml
${HOME}/docker/data/influxdb:/var/lib/influxdb3/data
```

De esta manera los datos permanecen en el equipo aunque el contenedor sea detenido o recreado.

Los scripts se exponen al contenedor mediante:

```yaml
./scripts:/scripts:ro
```

---

## 9. Seguridad local

InfluxDB 3 Core utiliza tokens para autorización.

El token local se almacena en:

```text
.influxdb3-token
```

Este archivo está excluido mediante `.gitignore`.

También se excluyen los archivos generados para las pruebas:

```gitignore
.influxdb3-token
scripts/puntos_fixture2030.lp
scripts/puntos_volumen.lp
```

No se deben incluir tokens reales en:

- GitHub;
- README;
- scripts versionados;
- capturas;
- documentación.

---

## 10. Requisitos previos

Se requiere:

```text
Docker Desktop
Docker Compose
PowerShell
```

En Windows, si PowerShell bloquea la ejecución de scripts, puede habilitarse únicamente para la terminal actual:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

La configuración vuelve a su estado normal al cerrar esa sesión de PowerShell.

---

## 11. Inicialización del ambiente

Desde la carpeta `InfluxDB`:

```powershell
.\scripts\inicializacion.ps1
```

El script:

1. configura la variable `HOME` utilizando `USERPROFILE` cuando es necesario;
2. prepara la carpeta de persistencia;
3. ejecuta Docker Compose;
4. verifica el estado del contenedor;
5. consulta la versión de InfluxDB.

El resultado esperado es:

```text
OK: ambiente InfluxDB iniciado correctamente.
```

También puede verificarse manualmente:

```powershell
docker compose ps
```

y:

```powershell
docker exec fixture2030-influxdb influxdb3 --version
```

---

## 12. Autorización local

El script:

```powershell
.\scripts\autorizacion_local.ps1
```

comprueba la existencia del archivo local de autorización y evita regenerar innecesariamente el token.

En una inicialización completamente nueva, el primer token administrador puede crearse mediante:

```powershell
docker exec -it fixture2030-influxdb influxdb3 create token --admin
```

El token devuelto debe guardarse localmente en:

```text
.influxdb3-token
```

No debe registrarse en capturas ni copiarse a documentación.

Para cargar el token en una sesión de PowerShell:

```powershell
$TOKEN = (Get-Content .\.influxdb3-token -Raw).Trim()
```

---

## 13. Creación de la base de datos

La base utilizada por el módulo es:

```text
fixture2030
```

Se crea con una retención de 30 días para los datos detallados:

```powershell
docker exec `
    -e "INFLUXDB3_AUTH_TOKEN=$TOKEN" `
    fixture2030-influxdb `
    influxdb3 create database fixture2030 `
    --retention-period 30d
```

La base utiliza el esquema implícito de InfluxDB 3 Core.

La existencia de la base puede verificarse mediante:

```powershell
docker exec `
    -e "INFLUXDB3_AUTH_TOKEN=$TOKEN" `
    fixture2030-influxdb `
    influxdb3 show databases
```

La política de retención puede verificarse mediante:

```powershell
docker exec `
    -e "INFLUXDB3_AUTH_TOKEN=$TOKEN" `
    fixture2030-influxdb `
    influxdb3 show retention
```

---

## 14. Retención y granularidad

La política definida es:

```text
Durante el partido
→ conservar puntos con precisión original.

Hasta 30 días
→ conservar los datos detallados.

Histórico
→ utilizar representaciones resumidas mediante agregaciones.

Después de la retención
→ los puntos detallados pueden expirar.
```

Los datos históricos pueden utilizar una granularidad menor, por ejemplo resúmenes por minuto u otras ventanas temporales.

La reducción de granularidad permite conservar tendencias sin mantener indefinidamente cada observación de alta frecuencia.

---

## 15. Generación del conjunto pequeño

Para generar el conjunto reproducible inicial:

```powershell
.\scripts\generacion_puntos.ps1
```

Se generan:

```text
8 puntos
```

correspondientes al partido:

```text
M001
```

Distribución:

```text
ARG → 4 puntos
POR → 4 puntos
```

El archivo generado es:

```text
scripts/puntos_fixture2030.lp
```

Cada línea utiliza Line Protocol:

```text
tabla,tags fields timestamp
```

Ejemplo conceptual:

```text
estadisticas,partido_id=M001,equipo_id=ARG posesion_pct=55.0,pases=100i,tiros=1i 1917676800
```

El generador escribe el archivo utilizando saltos de línea LF para evitar caracteres adicionales incompatibles con el parser de Line Protocol.

---

## 16. Carga de datos

Para cargar el conjunto pequeño:

```powershell
.\scripts\carga_lotes.ps1
```

El script utiliza:

```text
fixture2030
```

como base de destino y declara precisión temporal en segundos.

El token se obtiene desde `.influxdb3-token` y no se imprime.

---

## 17. Validación

Para comprobar la carga:

```powershell
.\scripts\validacion.ps1
```

El conjunto `M001` debe producir:

```text
8 puntos

ARG → 4
POR → 4
```

La validación se realiza mediante consultas SQL con `COUNT(*)` y agrupación por `equipo_id`.

---

## 18. Consultas temporales

Las consultas se encuentran en:

```text
scripts/consultas_temporales.ps1
```

Se ejecutan mediante:

```powershell
.\scripts\consultas_temporales.ps1
```

El script contiene consultas para:

### Evolución de un equipo

Recupera las observaciones de Argentina en `M001` ordenadas por tiempo.

### Comparación entre equipos

Recupera las observaciones de ambos equipos del partido para permitir su comparación.

### Ventana temporal

Recupera únicamente los puntos comprendidos dentro de un intervalo temporal explícito.

Ejemplo de criterio:

```sql
WHERE partido_id = 'M001'
  AND equipo_id = 'ARG'
  AND time >= '2030-10-08T08:00:01Z'
  AND time <= '2030-10-08T08:00:02Z'
```

Las consultas temporales se acotan por tiempo y dimensiones para evitar recuperar puntos que no son necesarios para la operación.

---

## 19. Agregaciones

Las agregaciones se ejecutan mediante:

```powershell
.\scripts\agregaciones.ps1
```

El resumen implementado utiliza:

```sql
AVG(posesion_pct)
SUM(tiros)
MAX(pases) - MIN(pases)
```

agrupado por equipo.

Para el conjunto pequeño se obtienen resultados equivalentes a:

```text
ARG
posesión promedio → 56,5
tiros totales → 2
pases nuevos → 15

POR
posesión promedio → 43,5
tiros totales → 2
pases nuevos → 13
```

Cada agregación fue seleccionada según la semántica de la medida.

---

## 20. Generación de prueba de volumen

Para la prueba local de volumen:

```powershell
.\scripts\generacion_volumen.ps1
```

Se generan:

```text
10.000 puntos
```

correspondientes al partido:

```text
M002
```

Distribución:

```text
ARG → 5.000 puntos
POR → 5.000 puntos
```

El archivo generado es:

```text
scripts/puntos_volumen.lp
```

Este archivo se excluye del repositorio.

---

## 21. Carga de la prueba de volumen

La carga se ejecuta mediante:

```powershell
.\scripts\carga_lotes.ps1 -Archivo puntos_volumen.lp
```

El script registra:

- cantidad de puntos;
- tiempo total observado;
- resultado de la operación de escritura.

---

## 22. Ambiente de la prueba de rendimiento

La prueba local fue ejecutada el:

```text
06/10/2026
```

Ambiente utilizado:

```text
InfluxDB 3 Core: 3.12.0
CPU: 11th Gen Intel(R) Core(TM) i5-1135G7 @ 2.40GHz
RAM: 7,75 GB
Entorno: Docker Compose local
Sistema de ejecución de scripts: PowerShell
```

Versión observada:

```text
InfluxDB 3 Core, 3.12.0
```

---

## 23. Resultado de la prueba de rendimiento

Volumen efectivamente procesado:

```text
10.000 puntos
```

El CLI de InfluxDB informó:

```text
Tiempo de escritura: 320 ms
Solicitudes: 1
Velocidad: 31.174 líneas/s
Volumen: 887,09 KiB
Transferencia: 2,70 MiB/s
```

El cronómetro externo de `carga_lotes.ps1` registró:

```text
1,0744054 segundos
```

### Interpretación

Los dos tiempos no representan exactamente la misma medición.

Los:

```text
320 ms
```

corresponden al tiempo informado directamente por el comando de escritura de InfluxDB.

Los:

```text
1,0744054 segundos
```

representan el tiempo total observado por el script alrededor de la ejecución del comando.

Por este motivo ambos resultados se documentan por separado y no se consideran equivalentes.

---

## 24. Validación de la prueba de volumen

Después de la carga se ejecutó:

```powershell
.\scripts\validacion.ps1
```

El resultado confirmó:

```text
M002 → 10.000 puntos

ARG → 5.000
POR → 5.000
```

La cantidad y distribución almacenadas coincidieron con los datos generados.

La tabla también contiene el conjunto pequeño `M001`, por lo que el total general almacenado luego de ambas pruebas es:

```text
10.008 puntos
```

Las validaciones se realizan por `partido_id` para comprobar cada conjunto de manera independiente.

---

## 25. Estrategia hacia 10M+ puntos

Los 10M+ puntos representan el objetivo de diseño del Hito y no el volumen efectivamente probado en el ambiente local.

La estrategia contempla:

- generación reproducible;
- escritura mediante Line Protocol;
- cargas por lotes;
- precisión temporal explícita;
- control de cardinalidad;
- consultas por rango temporal;
- filtrado por dimensiones;
- agregaciones;
- validación posterior;
- manejo de errores;
- posibilidad de reintentos;
- política de retención;
- reducción de granularidad para información histórica.

No se extrapola el rendimiento observado con 10.000 puntos directamente hacia 10M+.

Una prueba sobre mayor volumen deberá volver a medir tiempos, recursos utilizados y resultados reales.

---

## 26. Limitaciones de la prueba

La prueba realizada:

```text
no representa un entorno productivo;
no demuestra rendimiento con 10M+ puntos;
no utiliza infraestructura distribuida;
no mide comportamiento bajo múltiples productores simultáneos.
```

Su objetivo es demostrar de manera reproducible:

```text
generación
→ carga
→ almacenamiento
→ consulta
→ agregación
→ validación
```

sobre el hardware local disponible.

---

## 27. Evidencias

Las capturas utilizadas para verificar el trabajo se encuentran en:

```text
docs/evidencia/
```

### Evidencia 01 — Creación de la base

```text
01_creacion_base_fixture2030.png
```

Demuestra la creación de la base `fixture2030`.

### Evidencia 02 — Base y política de retención

```text
02_verificacion_base_y_retencion.png
```

Verifica la existencia de la base y su configuración temporal.

### Evidencia 03 — Generación inicial

```text
03_generacion_8_puntos.png
```

Demuestra la generación reproducible de los 8 puntos de prueba.

### Evidencia 04 — Carga inicial

```text
04_carga_8_puntos.png
```

Demuestra una escritura exitosa mediante Line Protocol.

### Evidencia 05 — Validación inicial

```text
05_validacion_8_puntos.png
```

Verifica la cantidad y distribución del conjunto pequeño.

### Evidencia 06 — Consultas temporales

```text
06_consultas_temporales.png
```

Muestra la recuperación y comparación de estadísticas almacenadas.

### Evidencia 07 — Agregaciones

```text
07_agregaciones_por_equipo.png
```

Muestra el promedio de posesión, total de tiros y diferencia de pases acumulados.

### Evidencia 08 — Prueba de carga

```text
08_carga_10000_puntos.png
```

Registra la carga real de 10.000 puntos y las métricas informadas.

### Evidencia 09 — Validación de volumen

```text
09_validacion_10000_puntos.png
```

Comprueba que `M002` contiene exactamente 10.000 puntos distribuidos en partes iguales entre los dos equipos.

### Evidencia 10 — Ambiente de prueba

```text
10_ambiente_prueba_rendimiento.png
```

Registra la versión de InfluxDB, procesador y memoria RAM utilizados durante la medición.

### Evidencia 11 — Ventana temporal

```text
11_consulta_ventana_temporal.png
```

Demuestra una consulta acotada por partido, equipo y rango temporal.

Las capturas no contienen tokens ni credenciales.

---

## 28. Documentación técnica

El razonamiento de diseño se encuentra separado del README.

### Patrones de acceso

```text
docs/patrones_de_acceso.md
```

Documenta las preguntas temporales prioritarias, dimensiones, medidas, frecuencia y comportamiento ante datos faltantes o tardíos.

### Modelo multidimensional

```text
docs/modelo_multidimensional.md
```

Documenta tabla, tags, fields, timestamp, tipos, agregaciones y relación con el resto del TPO.

### Cardinalidad y escalabilidad

```text
docs/cardinalidad_y_escalabilidad.md
```

Documenta la estimación de series, atributos excluidos de tags, estrategia para 10M+ puntos y resultados de la prueba local.

### Retención y granularidad

```text
docs/retencion_y_granularidad.md
```

Documenta el ciclo de vida de los puntos, conservación del detalle, resúmenes históricos y expiración.

---

## 29. Relación con el resto del Fixture 2030

InfluxDB se utiliza específicamente para información cuya evolución temporal forma parte de la consulta.

Ejemplos:

```text
posesión a lo largo del partido;
evolución de pases;
tiros por intervalo.
```

`partido_id` permite relacionar las observaciones con los partidos del Fixture.

`equipo_id` permite recuperar y comparar las estadísticas de los equipos participantes.

Este módulo no reemplaza los modelos utilizados en los hitos anteriores.

Los distintos modelos del proyecto continúan utilizándose según el patrón de acceso correspondiente, mientras que InfluxDB incorpora el historial temporal de las estadísticas en vivo.

---

## 30. Detener y reiniciar el ambiente

Para detener el servicio:

```powershell
docker compose down
```

Los datos permanecen almacenados en:

```text
~/docker/data/influxdb
```

Para volver a iniciar:

```powershell
.\scripts\inicializacion.ps1
```

o:

```powershell
docker compose up -d
```

No es necesario eliminar la carpeta de persistencia para reiniciar el contenedor.

---

## 31. Problemas conocidos y solución

### PowerShell bloquea los scripts

Error:

```text
la ejecución de scripts está deshabilitada en este sistema
```

Solución temporal:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

### Variable HOME no definida en Windows

Docker puede mostrar:

```text
The "HOME" variable is not set
```

El script `inicializacion.ps1` utiliza `USERPROFILE` como `HOME` cuando corresponde.

Manualmente puede definirse mediante:

```powershell
$env:HOME=$env:USERPROFILE
```

### El contenedor aparece como Restarting

Consultar los logs:

```powershell
docker compose logs influxdb
```

### Error de Line Protocol por `\r`

Si InfluxDB informa:

```text
Could not parse entire line. Found trailing content: '\r'
```

el archivo fue generado con terminaciones de línea incompatibles.

Los generadores actuales escriben los archivos utilizando saltos de línea `LF`, por lo que se debe volver a generar el archivo antes de cargarlo.

---

## 32. Alcance

Este Hito se concentra en:

```text
captura temporal;
modelado multidimensional;
cardinalidad;
carga;
consultas;
agregaciones;
retención;
granularidad;
validación;
escalabilidad.
```

No se implementan para este módulo:

```text
API REST;
interfaz web;
Grafana;
despliegue cloud;
monitorización de producción.
```

---

## 33. Flujo completo de ejecución

Para reproducir el módulo:

```powershell
# 1. Habilitar scripts solamente para esta terminal si Windows los bloquea
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass

# 2. Inicializar ambiente
.\scripts\inicializacion.ps1

# 3. Comprobar autorización local
.\scripts\autorizacion_local.ps1

# 4. Cargar token en la sesión
$TOKEN = (Get-Content .\.influxdb3-token -Raw).Trim()

# 5. Generar conjunto pequeño
.\scripts\generacion_puntos.ps1

# 6. Cargar conjunto pequeño
.\scripts\carga_lotes.ps1

# 7. Validar datos
.\scripts\validacion.ps1

# 8. Ejecutar consultas
.\scripts\consultas_temporales.ps1

# 9. Ejecutar agregaciones
.\scripts\agregaciones.ps1

# 10. Generar prueba de volumen
.\scripts\generacion_volumen.ps1

# 11. Cargar prueba de volumen
.\scripts\carga_lotes.ps1 -Archivo puntos_volumen.lp

# 12. Validar nuevamente
.\scripts\validacion.ps1
```

Si la base todavía no existe, debe crearse antes de ejecutar las cargas siguiendo la sección **Creación de la base de datos**.

---

## 34. Resultado final

El módulo implementado permite:

```text
registrar observaciones temporales;
filtrar por partido y equipo;
consultar ventanas temporales;
comparar equipos;
calcular agregaciones;
controlar cardinalidad;
aplicar retención;
generar cargas reproducibles;
validar cantidad y distribución;
medir una prueba local real;
documentar una estrategia de crecimiento hacia 10M+ puntos.
```

La prueba efectivamente ejecutada fue de **10.000 puntos** y sus resultados se documentan sin extrapolarlos como rendimiento garantizado para el volumen objetivo.