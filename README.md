# ClassConnect - API Courses

## Contenidos
1. Introducción
2. Arquitectura de componentes, CI-CD, Despliegue en la nube3. Pre-requisitos
4. Documentacion técnica
5. Tests
6. Comandos para construir la imagen de Docker
7. Comandos para correr la base de datos
8. Comandos para correr la imagen del servicio
9. Despliegue en la nube/k8
10. Análisis postmortem

## 1. Introducción

Microservicio dedicado exclusivamente a Cursos. 

Historias de usuario realizadas: 
 - [x] Creacion y gestión de cursos
 - [x] Listado e inscripción a cursos
 - [x] Inscripcion de estudiantes (Por el momento no está del todo completado)
 - [x] Organización de modulos y recursos
 - [x] Visualización de cursos

# 2. Arquitectura de componentes, CI-CD, Despliegue en la nube

[Explicados en API Gateway](https://github.com/1c2025-IngSoftware2-g7/api_gateway)

### Test coverage

[![codecov](https://codecov.io/gh/1c2025-IngSoftware2-g7/service_api_courses/branch/main/graph/badge.svg)](https://codecov.io/gh/1c2025-IngSoftware2-g7/service_api_courses)

## 3. Pre-requisitos
- Necesario para levantar el entorno de desarrollo:
    - [Docker](https://docs.docker.com/get-started/introduction/) (version 27.3.1) 
    - [Docker-compose](https://docs.docker.com/compose/install/) (version 2.30.3)

- Puertos utilizados: 
    - 27015: Utilizado por la base de datos MongoDB.
    - 8080: Utilizado por la API.

## 4. Documentación técnica

- Lenguaje utilizado:
    - Python 3.13 (Utilizado en la imagen del Dockerfile).

- Base de datos:
    - MongoDB 8.0

- Gestión de paquetes:
    - pip (se usa dentro del contenedor para instalar dependencias).

- Instalacion: Se puede clonar este repositorio, realizar la [construccion de la imagen](#6-comandos-para-construir-la-imagen-de-docker), y luego, la [ejecucion de la misma](#7-comandos-para-correr-la-base-de-datos) 

- Definicion de la arquitectura: En este microservicio utilizamos la arquitectura de microservicios, en el cual utilizamos servicios y controladores.

## 5. Tests
Para la implementación de los test de integración, se utilizó la librería [pytest](https://www.psycopg.org/psycopg3/docs/basic/index.html).  
Estos se encuentran desarrollados en [```./test/api_test.py```](./tests/)


## 6. Comandos para construir la imagen de Docker
Al utilizar docker-compose, se puede construir todas las imágenes definidas en docker-compose.yml con el siguiente comando:
```bash
docker compose build
```

## 7. Comandos para correr la base de datos
Como ya se mencionó, se utilizó docker compose. Por lo que para levantar todas las imágenes del proyecto, se debe correr:
```bash
docker compose up
```

En ```docker-compose.yml```:
- mongodb: Base de datos mongoDB. Se define la imagen oficial, los parámetros para la conexión, el puerto en el que escuchará (27015) y se carga el script que se debe correr para inicializar la base de datos, un tipo de usuario, sus permisos y se crea la tabla de cursos. Además, se define la red a la que va a pertenecer.  

## 8. Comandos para correr la imagen del servicio
De igual forma que en el inciso anterior:
```bash
docker compose up
```

En ```docker-compose.yml```:
- courses: API RESTful en Flask. Se utiliza como imagen la definida en Dockerfile. Se indica el puerto 8080 para comunicarse con este servicio y se incluye en la misma red que la base de datos, de esta forma se pueden comunicar. Además, se define que este servicio se va a correr cuando se termine de levantar la base de datos. Por último, se indica el comando que se va a correr.

## 9. Despliegue en la nube/k8

Inicialmente, el proyecto a medida que escaló se realizó deployments sobre la plataforma Render, no obstante, para la última entrega, se decidió hacer un deploy sobre k8, sobre el link [LINKK8CURSOS](http://google.com)

## 10. Análisis postmortem

Inicialmente este microservicio inició como un servicio chico, con funcionalidades básicas y con colecciones (tipo de estructura de mongodb) bastante acotadas.
A medida que las semanas pasaron, decidimos enfocar tiempo en la resolución de puntos opcionales, donde, este
microservicio tenia muchas por realizar.
A medida que se agregaron features, empezó a comprometerse la cantidad de información que había que manejar
para la colecciones que habiamos creado inicialmente, por lo que, tuvimos que no solo repensar como distribuir
colecciones para ciertos datos, sino que también transpasarlo a código.

Haber pensado de antemano nos podría haber ofrecido, inclusive, mas escalabilidad para desarrollar mas features que
fueron presentadas como ideas al docente, sin embargo no pudieron ser realizadas (Por ejemplo, lograr
que cada ayudante tenga individualmente permisos de escritura y/o escritura sobre una acción que tiene posible)