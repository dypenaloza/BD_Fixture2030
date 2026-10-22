# Topología y entornos — Hito 11

## 1. Objetivo

Documentar cómo se comunican los componentes del Fixture Mundial 2030, identificando sus entornos de ejecución, puertos y mecanismos de conexión.

## 2. Arquitectura general

El proyecto utiliza una API REST desarrollada con FastAPI y seis bases de datos NoSQL ejecutadas en contenedores Docker independientes.

La comunicación sigue esta estructura:

Cliente HTTP → API REST → Adaptador → Base NoSQL

Cada adaptador utiliza el driver o protocolo correspondiente a su base de datos.

## 3. Entorno de ejecución

Las bases de datos se ejecutan mediante Docker Desktop en la notebook del equipo.

La API REST está configurada para poder ejecutarse localmente y conectarse a los puertos publicados de Docker mediante 127.0.0.1.

La ejecución efectiva de la API será verificada durante las pruebas de conectividad.

## 4. Puertos y servicios

| Producto         | Puerto en Windows | Puerto interno |
| ---------------- | ----------------- | -------------- |
| MongoDB          | 27017             | 27017          |
| Neo4j Bolt       | 7687              | 7687           |
| Neo4j Browser    | 7474              | 7474           |
| Cassandra        | 9042              | 9042           |
| Redis            | 6379              | 6379           |
| InfluxDB         | 8181              | 8181           |
| IRIS Superserver | 1972              | 1972           |
| IRIS Portal      | 52873             | 52773          |

Los valores fueron identificados mediante `docker ps`.

IRIS e InfluxDB tienen sus puertos publicados en 127.0.0.1, mientras que los otros cuatro productos muestran publicaciones en todas las interfaces IPv4.

## 5. Diferencia entre Windows y Docker

Cuando la API se ejecuta directamente en Windows, puede acceder a los servicios mediante los puertos publicados en localhost.

Cuando una aplicación se ejecuta dentro de un contenedor, localhost hace referencia a ese mismo contenedor.

Por eso, una API contenerizada normalmente debe utilizar los nombres de servicio y puertos internos correspondientes a una red Docker compartida.

## 6. Configuración de conexiones

La API utiliza variables de entorno definidas en su archivo `.env`.

Estas variables permiten configurar hosts, puertos, bases de datos y mecanismos de autenticación sin modificar el código.

Los archivos que contienen credenciales y tokens deben permanecer excluidos del repositorio mediante `.gitignore`.

## 7. Estado inicial

Se verificó mediante `docker ps` que los seis contenedores estaban iniciados.

IRIS mostró el estado `healthy`.

Este diagnóstico confirma que los procesos están iniciados y permite identificar sus puertos publicados.

Sin embargo, todavía no demuestra que las conexiones desde la API funcionen correctamente.

Las pruebas TCP, nativas y de API se realizarán en las siguientes etapas del hito.
