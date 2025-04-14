# ClassConnect - API Courses

## Contenidos
1. Introducción
2. 
3. Pre-requisitos
4. Tests
5. Comandos para construir la imagen de Docker
6. Comandos para correr la base de datos
7. Comandos para correr la imagen del servicio

## 1. Introducción

Microservicio dedicado exclusivamente a Cursos. 

Historias de usuario realizadas: 
 - [x] Creacion y gestión de cursos
 - [x] Listado e inscripción a cursos
 - [x] Inscripcion de estudiantes (Por el momento no está del todo completado)
 - [ ] Organización de modulos y recursos
 - [x] Visualización de cursos

## 2. CI

### Test coverage

[![codecov](https://codecov.io/gh/1c2025-IngSoftware2-g7/service_api_courses/branch/main/graph/badge.svg)](https://codecov.io/gh/1c2025-IngSoftware2-g7/service_api_courses)

## 3. Pre-requisitos
- Necesario para levantar el entorno de desarrollo:
    - [Docker](https://docs.docker.com/get-started/introduction/) (version 27.3.1) 
    - [Docker-compose](https://docs.docker.com/compose/install/) (version 2.30.3)

- Puertos utilizados: 
    - 27015: Utilizado por la base de datos MongoDB.
    - 8080: Utilizado por la API.

Adicionalmente, menciono a continuación lo utilizado dentro de los contenedores:

- Lenguaje:
    - Python 3.13 (Utilizado en la imagen del Dockerfile).

- Base de datos:
    - MongoDB 8.0

- Gestión de paquetes:
    - pip (se usa dentro del contenedor para instalar dependencias).

## 4. Tests
Para la implementación de los test de integración, se utilizó la librería [pytest](https://www.psycopg.org/psycopg3/docs/basic/index.html).  
Estos se encuentran desarrollados en [```./test/api_test.py```](./tests/)


## 5. Comandos para construir la imagen de Docker
Al utilizar docker-compose, se puede construir todas las imágenes definidas en docker-compose.yml con el siguiente comando:
```bash
docker compose build
```

## 6. Comandos para correr la base de datos
Como ya se mencionó, se utilizó docker compose. Por lo que para levantar todas las imágenes del proyecto, se debe correr:
```bash
docker compose up
```

En ```docker-compose.yml```:
- mongodb: Base de datos mongoDB. Se define la imagen oficial, los parámetros para la conexión, el puerto en el que escuchará (27015) y se carga el script que se debe correr para inicializar la base de datos, un tipo de usuario, sus permisos y se crea la tabla de cursos. Además, se define la red a la que va a pertenecer.  

## 7. Comandos para correr la imagen del servicio
De igual forma que en el inciso anterior:
```bash
docker compose up
```

En ```docker-compose.yml```:
- courses: API RESTful en Flask. Se utiliza como imagen la definida en Dockerfile. Se indica el puerto 8080 para comunicarse con este servicio y se incluye en la misma red que la base de datos, de esta forma se pueden comunicar. Además, se define que este servicio se va a correr cuando se termine de levantar la base de datos. Por último, se indica el comando que se va a correr.

## 8. Despliegue en la nube

Actualmente este servicio está corriendo en Render sobre la URL: [https://service-api-courses.onrender.com](https://service-api-courses.onrender.com)