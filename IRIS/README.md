# Hito 9 — Entidades Complejas del Fixture 2030

## 1. Descripción general

Este módulo implementa una base de datos orientada a objetos utilizando InterSystems IRIS Community Edition.

El objetivo es representar entidades complejas del Fixture Mundial 2030 mediante clases persistentes, herencia, relaciones bidireccionales y métodos de validación.

La implementación utiliza ObjectScript y permite almacenar, recuperar y consultar objetos sin depender de un ORM externo.

También demuestra las capacidades multimodelo de IRIS, que permiten consultar mediante SQL los datos almacenados como objetos.

## 2. Tecnologías utilizadas

- InterSystems IRIS Community Edition.
- ObjectScript.
- Docker y Docker Compose.
- SQL.
- Git y GitHub.

El desarrollo se realizó en Windows, utilizando Docker Desktop.

## 3. Estructura del proyecto

```text
IRIS/
├── docker-compose.yml
├── .gitignore
├── README.md
├── scripts/
│   ├── Fixture.Persona.cls
│   ├── Fixture.Jugador.cls
│   ├── Fixture.Arbitro.cls
│   ├── Fixture.Partido.cls
│   ├── Fixture.Evento.cls
│   └── Fixture.CargaInicial.cls
└── evidencias/
    ├── 01_persistencia.png
    ├── 02_navegacion.png
    ├── 03_consultas_partidos.png
    ├── 04_consultas_eventos.png
    ├── 05_validacion_required.png
    ├── 06_validacion_estado.png
    ├── 07_integridad.png
    └── 08_carga_inicial.png
```

Los archivos `.cls` contienen las definiciones de clases persistentes y el procedimiento de carga inicial.

La carpeta `evidencias/` contiene capturas de las pruebas realizadas.

## 4. Modelo de dominio

Se implementaron cinco clases principales:

| Clase | Descripción | Persistencia |
|---|---|---|
| Persona | Contiene los atributos comunes de las personas. | %Persistent |
| Jugador | Representa a un jugador de fútbol. | Hereda de Persona |
| Arbitro | Representa a un árbitro. | Hereda de Persona |
| Partido | Representa un partido y sus estados. | %Persistent |
| Evento | Representa un acontecimiento de un partido. | %Persistent |

Además, se implementó `Fixture.CargaInicial`, una clase auxiliar que ejecuta la carga de datos.

### 4.1. Diagrama de clases UML

![Diagrama UML](/Diagrama_UML.jpg)

El diagrama representa la herencia y la relación padre-hijo implementadas.

## 5. Herencia

Se implementó la clase base `Fixture.Persona`, que contiene propiedades compartidas por las personas del dominio.

Las clases `Fixture.Jugador` y `Fixture.Arbitro` heredan de Persona.

Jugador agrega:

- Numero.
- Posicion.

Arbitro agrega:

- Rol.
- LicenciaFIFA.

La herencia permite reutilizar propiedades y evitar duplicación de código.

Se utiliza para representar especializaciones estables del dominio, no estados temporales.

## 6. Relaciones e integridad referencial

Se implementó una relación padre-hijo entre Partido y Evento.

Un Partido puede contener múltiples Eventos.

Cada Evento pertenece a un Partido.

La relación utiliza:

- `Cardinality = children` en Partido.
- `Cardinality = parent` en Evento.
- `Inverse` para establecer la relación bidireccional.

Esto permite navegar desde un Partido hacia sus Eventos y mantener la integridad referencial.

### 6.1. Matriz de integridad

| Regla | Implementación | Comportamiento esperado |
|---|---|---|
| Un Partido debe tener código. | Property Codigo [Required] | Rechaza el guardado si falta. |
| Un Partido debe tener estado. | Property Estado [Required] | Rechaza el guardado si falta. |
| El código del Partido debe ser único. | Index idxCodigo [Unique] | Rechaza códigos duplicados. |
| Un Evento depende de su Partido. | Relationship parent/children | Mantiene la dependencia entre objetos. |
| Si se elimina el Partido, se eliminan sus Eventos. | Relación padre-hijo | Eliminación en cascada. |
| Una Persona debe tener nombre y nacionalidad. | Propiedades [Required] | Rechaza datos incompletos. |
| Un Partido no debe pasar directamente de Programado a Finalizado. | Método CambiarEstado() | Rechaza la transición mediante el método. |

La validación de estado se encuentra encapsulada en el método `CambiarEstado()`.

La implementación actual no impide modificar directamente la propiedad Estado desde otro código. Por lo tanto, las transiciones deben realizarse mediante el método para respetar esa regla.

## 7. Índices

Se implementaron dos índices:

### idxCodigo

Definido sobre `Partido.Codigo`.

Garantiza que no existan partidos con el mismo código.

### idxPartido

Definido sobre la relación `Evento.Partido`.

Permite localizar los Eventos asociados a un Partido de manera eficiente.

Este índice evita depender de recorridos completos sobre los Eventos cuando se necesita recuperar una colección de hijos.

La decisión sigue las buenas prácticas de indexación del lado hijo vistas en la Clase 10.

## 8. Configuración de Docker

Se utilizó la imagen oficial:

`intersystems/iris-community:latest-cd`

El servicio se configuró mediante Docker Compose.

### Puertos

| Puerto de Windows | Puerto interno | Función |
|---|---|---|
| 1972 | 1972 | Conexión al motor IRIS |
| 52873 | 52773 | Management Portal |

Se modificó el puerto externo del Management Portal porque Windows tenía reservado el puerto 52773.

El puerto interno de IRIS permanece sin modificaciones.

### Persistencia

Durante el desarrollo se utilizó un volumen administrado por Docker:

`iris_durable`

Este volumen permite conservar los datos entre recreaciones del contenedor mientras no se elimine explícitamente.

**Limitación pendiente:** el enunciado exige utilizar `~/docker/data/iris`. La configuración con volumen administrado permitió resolver un problema de permisos durante las pruebas en Windows, pero todavía debe adaptarse para cumplir exactamente esa ubicación obligatoria.

No deben versionarse los datos persistentes del motor.

## 9. Instalación y ejecución

Los comandos siguientes se ejecutan desde la raíz del repositorio.

### 9.1. Iniciar Docker

```powershell
docker compose -f .\IRIS\docker-compose.yml up -d
```

### 9.2. Verificar el contenedor

```powershell
docker ps --filter "name=fixture2030-iris"
```

### 9.3. Ingresar al Terminal de IRIS

```powershell
docker exec -it fixture2030-iris iris session IRIS
```

Si el contenedor presenta errores de permisos sobre `/durable`, durante la preparación del entorno se utilizaron:

```powershell
docker exec -u 0 fixture2030-iris chown -R irisowner:irisowner /durable
docker exec -u 0 fixture2030-iris chmod 770 /durable
docker restart fixture2030-iris
```

Estos comandos corresponden al entorno de práctica y pueden requerir una revisión según la configuración del equipo.

## 10. Carga y compilación de clases

Desde el Terminal de IRIS, en el namespace USER, ejecutar:

```objectscript
Do $system.OBJ.Load("/scripts/Fixture.Persona.cls","ck")
Do $system.OBJ.Load("/scripts/Fixture.Jugador.cls","ck")
Do $system.OBJ.Load("/scripts/Fixture.Arbitro.cls","ck")
```

Las clases Partido y Evento poseen dependencias mutuas.

Por ese motivo, primero se cargan sus definiciones:

```objectscript
Do $system.OBJ.Load("/scripts/Fixture.Partido.cls","k")
Do $system.OBJ.Load("/scripts/Fixture.Evento.cls","k")
```

Luego se compilan:

```objectscript
Do $system.OBJ.Compile("Fixture.Partido","ck")
Do $system.OBJ.Compile("Fixture.Evento","ck")
```

Finalmente, se carga la clase auxiliar:

```objectscript
Do $system.OBJ.Load("/scripts/Fixture.CargaInicial.cls","ck")
```

Las clases fueron compiladas correctamente durante las pruebas.

## 11. Carga inicial de objetos

Se implementó la clase `Fixture.CargaInicial`, que contiene el método `Ejecutar()`.

La carga crea:

- Un Partido identificado como M004.
- Un Evento de tipo Gol.
- Una relación padre-hijo entre ambos.

Para ejecutar la carga:

```objectscript
Do ##class(Fixture.CargaInicial).Ejecutar()
```

El procedimiento utiliza `%New()` para instanciar objetos.

La relación se establece mediante:

```objectscript
Do partido.Eventos.Insert(evento)
```

Finalmente, ambos objetos se almacenan mediante una sola llamada:

```objectscript
Set sc = partido.%Save()
```

El resultado del guardado se verifica mediante `%Status`.

El script utiliza un código fijo y está diseñado para ejecutarse una vez sobre una base sin ese Partido. Ejecutarlo nuevamente sin limpiar los datos provocará una colisión con el índice único.

## 12. Recuperación y navegación de objetos

La recuperación se realiza mediante `%OpenId()`.

Ejemplo:

```objectscript
Set partido = ##class(Fixture.Partido).%OpenId(idPartido)
```

Para acceder al primer Evento relacionado:

```objectscript
Set evento = partido.Eventos.GetAt(1)
```

Para mostrar sus propiedades:

```objectscript
Write evento.Tipo,!
Write evento.Minuto,!
```

Este mecanismo permite recorrer las relaciones utilizando referencias entre objetos sin recurrir a SQL.

Se comprobó el funcionamiento de esta navegación durante las pruebas.

## 13. Proyección multimodelo SQL

Las clases persistentes de IRIS también pueden consultarse mediante SQL.

Se utilizó el Management Portal en el namespace USER.

### Consulta de Partidos

```sql
SELECT ID, Codigo, Estado
FROM Fixture.Partido;
```

### Consulta de Eventos

```sql
SELECT ID, Tipo, Minuto
FROM Fixture.Evento;
```

Las consultas permiten comprobar que los datos creados mediante ObjectScript están disponibles desde SQL.

No fue necesario crear tablas manualmente ni duplicar los datos.

## 14. Pruebas de integridad y validación

Se realizaron las siguientes verificaciones.

### 14.1. Persistencia de objetos relacionados

Se creó un Partido y un Evento.

Ambos fueron vinculados y guardados mediante una única invocación de `%Save()`.

Se verificó que los dos objetos recibieran identidad persistente.

### 14.2. Recuperación de objetos

Se recuperó un Partido utilizando `%OpenId()`.

Posteriormente, se navegó hacia su Evento mediante la relación `Eventos`.

Se comprobaron las propiedades recuperadas.

### 14.3. Validación de propiedades obligatorias

Se creó una Persona sin asignar Nacionalidad.

Al ejecutar `%Save()`, IRIS rechazó el guardado debido a la ausencia de una propiedad obligatoria.

Esta prueba demuestra el funcionamiento de las restricciones `[Required]`.

### 14.4. Validación de transiciones

Se implementó el método `CambiarEstado()`.

Transiciones admitidas:

- Programado → Jugando.
- Jugando → Finalizado.

Se intentó realizar una transición directa:

`Programado → Finalizado`

El método devolvió `0`, indicando que la transición fue rechazada.

Posteriormente, se ejecutó:

`Programado → Jugando`

El método devolvió `1`, indicando que la transición fue aceptada.

### 14.5. Integridad referencial

Se creó un Partido de prueba con un Evento asociado.

Después de guardar ambos objetos, se eliminó el Partido mediante `%DeleteId()`.

Se comprobó que el Evento dependiente ya no podía recuperarse.

Esto demuestra el comportamiento de eliminación en cascada de la relación padre-hijo implementada.

## 15. Evidencias de ejecución

Las capturas se encuentran en `evidencias/`.

### 15.1. Persistencia

![Persistencia](evidencias/01_persistencia.png)

Demuestra la creación, vinculación y almacenamiento de objetos relacionados.

### 15.2. Navegación mediante objetos

![Navegacion](evidencias/02_navegacion.png)

Demuestra la recuperación y navegación mediante referencias sin utilizar SQL.

### 15.3. Consulta SQL de Partidos

![Consulta Partidos](evidencias/03_consultas_partidos.png)

Demuestra la proyección SQL de los objetos Partido.

### 15.4. Consulta SQL de Eventos

![Consulta Eventos](evidencias/04_consultas_eventos.png)

Demuestra la proyección SQL de los objetos Evento.

### 15.5. Validación de propiedades obligatorias

![Validacion Required](evidencias/05_validacion_required.png)

Demuestra el rechazo de un guardado inválido.

### 15.6. Validación de estados

![Validacion Estado](evidencias/06_validacion_estado.png)

Demuestra una transición rechazada y una transición aceptada.

### 15.7. Integridad referencial

![Integridad](evidencias/07_integridad.png)

Demuestra la eliminación de un Evento dependiente al eliminar su Partido.

### 15.8. Carga inicial

![Carga Inicial](evidencias/08_carga_inicial.png)

Demuestra la ejecución de la carga mediante el método `Fixture.CargaInicial.Ejecutar()`.

## 16. Escalabilidad y consideraciones técnicas

El diseño incorpora un índice sobre la relación del lado hijo para optimizar la recuperación de Eventos por Partido.

La separación entre Partido y Evento evita representar todos los acontecimientos del torneo como una única estructura persistente.

Las pruebas realizadas permiten verificar el comportamiento funcional del modelo.

No se realizaron pruebas de carga de gran volumen ni mediciones de rendimiento. Por lo tanto, no se presentan conclusiones sobre rendimiento en producción.

Las principales limitaciones actuales son:

- La validación de estados debe ejecutarse mediante el método correspondiente.
- La carga inicial utiliza un código fijo y no es idempotente.
- La persistencia debe adaptarse a la ruta obligatoria del enunciado.
- No se implementó una política general de inmutabilidad para los Eventos.

## 17. Conclusión

El módulo demuestra el uso de InterSystems IRIS como base de datos orientada a objetos y multimodelo.

Se implementaron clases persistentes con propiedades tipadas, herencia, relaciones bidireccionales, índices y una validación encapsulada.

Las pruebas demostraron el almacenamiento de objetos relacionados, su recuperación mediante referencias, la ejecución de consultas SQL y el comportamiento de las restricciones de integridad.

La implementación permite representar una porción estructural compleja del Fixture Mundial 2030 mediante ObjectScript, sin utilizar un ORM externo.

La adaptación de la persistencia a la ruta obligatoria del enunciado queda identificada como una tarea pendiente.